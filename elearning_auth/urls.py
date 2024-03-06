from django.urls import path
from elearning_auth.apis import (
    LoginAPIView,
    PasswordChangeAPIView,
    RegisterAPIView,
)
from elearning_auth.views import logout_user

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", logout_user, name="logout"),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("change-password/", PasswordChangeAPIView.as_view(), name="change-password"),
]
