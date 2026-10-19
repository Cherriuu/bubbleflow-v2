from django.urls import path
from . import auth_views

urlpatterns = [
    path("register/", auth_views.register_view),
    path("login/", auth_views.login_view),
    path("logout/", auth_views.logout_view),
    path("me/", auth_views.me_view),
    path("demo-login/", auth_views.demo_login_view),
]
