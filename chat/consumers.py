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
