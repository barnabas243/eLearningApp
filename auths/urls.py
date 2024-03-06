from django.urls import path
from elearning_auth.apis import (
    LoginAPIView,
    PasswordChangeAPIView,
    RegisterAPIView,
)
from elearning_auth.views import LoginView, RegisterView, logout_user

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_user, name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login-api/", LoginAPIView.as_view(), name="login"),
    path("register-api/", RegisterAPIView.as_view(), name="register"),
    path("change-password/", PasswordChangeAPIView.as_view(), name="change-password"),
]
