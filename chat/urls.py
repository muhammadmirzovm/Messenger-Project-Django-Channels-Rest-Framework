from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("room/<int:pk>/", views.room, name="room"),

    path("login/", auth_views.LoginView.as_view(
        template_name="chat/login.html",
        redirect_authenticated_user=True
    ), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup, name="signup"),

    path("accounts/login/", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("api/online/", views.online_users_api, name="online_users_api"),
    path("api/room/<int:pk>/online/", views.room_online_users_api, name="room_online_users_api"),
]
