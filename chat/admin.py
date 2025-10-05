from django.contrib import admin
from .models import User, Room, RoomMembership, Message

admin.site.register(User)
admin.site.register(Room)
admin.site.register(RoomMembership)
admin.site.register(Message)
