from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin
from djangochannelsrestframework.decorators import action

from .models import Room, Message
from .serializers import RoomSerializer, MessageSerializer


class ChatConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    """
    WebSocket API:
      - join_room: subscribe to message stream for a room
      - leave_room: unsubscribe
      - create_message: persist a message (requires auth)
    Observer:
      - message_activity: pushes new messages to subscribers of that room
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    lookup_field = "pk"

    @action() 
    async def join_room(self, pk, request_id: str, **kwargs):
        room = await database_sync_to_async(self.get_object)(pk=pk)

        await self.message_activity.subscribe(room=room.pk, request_id=request_id)
        data = await database_sync_to_async(lambda: RoomSerializer(room).data)() 
        return data, 200

    @action()
    async def leave_room(self, pk, **kwargs):
        await self.message_activity.unsubscribe(room=pk)
        return {"left": pk}, 200

    @action()
    async def create_message(self, message: str = "", room: int | None = None, room_id: int | None = None, **kwargs):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return {"detail": "Authentication required"}, 403

        rid = room or room_id
        if not rid:
            return {"detail": "room (or room_id) is required"}, 400

        def _create():
            try:
                r = Room.objects.get(pk=rid)
            except Room.DoesNotExist:
                return None
            return Message.objects.create(room=r, user=user, text=message)

        msg = await database_sync_to_async(_create)()
        if msg is None:
            return {"detail": f"Room {rid} not found"}, 404

        return {"ok": True}, 201

    @model_observer(Message)
    async def message_activity(self, message, observer=None, subscribing_request_ids=list, **kwargs):
        for request_id in subscribing_request_ids:
            body = dict(request_id=request_id)
            body.update(message)
            await self.send_json(body)

    @message_activity.serializer
    def message_activity(self, instance: Message, action, **kwargs):
        return dict(
            data=MessageSerializer(instance).data,
            action=action.value,
            pk=instance.pk,
        )

    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f"room__{instance.room_id}"

    @message_activity.groups_for_consumer
    def message_activity(self, room=None, **kwargs):
        if room is not None:
            yield f"room__{room}"


from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from asgiref.sync import sync_to_async

from .presence import (
    heartbeat, remove_global,
    room_join, room_leave,
    list_online_user_ids, room_online_user_ids
)

HB_SECONDS = getattr(settings, "PRESENCE_HEARTBEAT_SECONDS", 20)

def _uid(user):
    return getattr(user, "id", None)

class PresenceConsumer(AsyncJsonWebsocketConsumer):
    """
    ws://.../ws/presence/
    - requires authenticated user
    - client should send {"type":"heartbeat"} every HB_SECONDS
    - server can send:
        {"type":"all_online", "user_ids":[...], "heartbeat_every":HB_SECONDS}
        {"type":"presence_event", "event":"online|offline", "user_id":...}
    """
    group_name = "presence_global"

    async def connect(self):
        user = self.scope.get("user", AnonymousUser())
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await sync_to_async(heartbeat)(_uid(user))
        await self.channel_layer.group_send(self.group_name, {
            "type": "presence.update",
            "payload": {"event": "online", "user_id": _uid(user)}
        })

        ids = await sync_to_async(list_online_user_ids)()
        await self.send_json({"type": "all_online", "user_ids": ids, "heartbeat_every": HB_SECONDS})

    async def disconnect(self, code):
        user = self.scope.get("user", AnonymousUser())
        if user and user.is_authenticated:
            await sync_to_async(remove_global)(_uid(user))
            await self.channel_layer.group_send(self.group_name, {
                "type": "presence.update",
                "payload": {"event": "offline", "user_id": _uid(user)}
            })
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        user = self.scope.get("user", AnonymousUser())
        if not user or not user.is_authenticated:
            return
        if content.get("type") == "heartbeat":
            await sync_to_async(heartbeat)(_uid(user))
        elif content.get("type") == "get_all":
            ids = await sync_to_async(list_online_user_ids)()
            await self.send_json({"type": "all_online", "user_ids": ids, "heartbeat_every": HB_SECONDS})

    async def presence_update(self, event):
        await self.send_json({"type": "presence_event", **event["payload"]})


class RoomPresenceConsumer(AsyncJsonWebsocketConsumer):
    """
    ws://.../ws/room/<room_id>/presence/
    Track presence of users inside a specific room.
    """
    async def connect(self):
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        user = self.scope.get("user", AnonymousUser())
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"presence_room_{self.room_id}"
        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await sync_to_async(room_join)(_uid(user), self.room_id)

        await self.channel_layer.group_send(self.group_name, {
            "type": "presence.update",
            "payload": {"event": "room_join", "user_id": _uid(user), "room_id": self.room_id}
        })

        ids = await sync_to_async(room_online_user_ids)(self.room_id)
        await self.send_json({"type": "room_online", "room_id": self.room_id, "user_ids": ids, "heartbeat_every": HB_SECONDS})

    async def disconnect(self, code):
        user = self.scope.get("user", AnonymousUser())
        if user and user.is_authenticated:
            await sync_to_async(room_leave)(_uid(user), self.room_id)
            await self.channel_layer.group_send(self.group_name, {
                "type": "presence.update",
                "payload": {"event": "room_leave", "user_id": _uid(user), "room_id": self.room_id}
            })
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        user = self.scope.get("user", AnonymousUser())
        if user and user.is_authenticated and content.get("type") == "heartbeat":
            await sync_to_async(heartbeat)(_uid(user))

    async def presence_update(self, event):
        await self.send_json({"type": "presence_event", **event["payload"]})
