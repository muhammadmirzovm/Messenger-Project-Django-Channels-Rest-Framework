from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .presence import list_online_user_ids, room_online_user_ids

from .models import Room
from .forms import CustomUserCreationForm

User = get_user_model()

def online_users_api(request):
    ids = list_online_user_ids()
    users = list(User.objects.filter(id__in=ids).values("id", "username"))
    return JsonResponse({"online": users})

def room_online_users_api(request, pk: int):
    ids = room_online_user_ids(int(pk))
    users = list(User.objects.filter(id__in=ids).values("id", "username"))
    return JsonResponse({"room_id": pk, "online": users})

def index(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            room, _ = Room.objects.get_or_create(name=name)
            return HttpResponseRedirect(reverse("room", args=[room.pk]))
    rooms = Room.objects.all().order_by("name")
    return render(request, "chat/index.html", {"rooms": rooms})

@login_required
def room(request, pk: int):
    room = get_object_or_404(Room, pk=pk)
    # load past messages (persist across refresh)
    messages = room.messages.select_related("user").order_by("created_at")
    return render(request, "chat/room.html", {"room": room, "messages": messages})

def logout_view(request):
    logout(request)
    return redirect("index")

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data["password1"]
            user = authenticate(username=user.username, password=raw_password)
            if user:
                login(request, user)
            return redirect("index")
    else:
        form = CustomUserCreationForm()
    return render(request, "chat/signup.html", {"form": form})
