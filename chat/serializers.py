from rest_framework import serializers
from .models import User, Room, RoomMembership, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = RoomMembership
        fields = ["user", "nickname", "last_seen"]

class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "text", "user", "created_at", "created_at_formatted"]

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %H:%M:%S")

class RoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    members = MembershipSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Room
        fields = ["id", "name", "members", "last_message"]

    def get_last_message(self, obj):
        last = obj.messages.order_by("created_at").last()
        return MessageSerializer(last).data if last else None
