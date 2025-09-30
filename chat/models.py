from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    # Extend later with avatar, bio, etc.
    pass

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    current_users = models.ManyToManyField("User", related_name="current_rooms", blank=True, through="RoomMembership")

    def __str__(self):
        return f"Room({self.name})"

class RoomMembership(models.Model):
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="memberships")
    nickname = models.CharField(max_length=50, blank=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("room", "user")

    def touch(self):
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])

class Message(models.Model):
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="messages")
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message({self.user} -> {self.room})"
