from django.urls import path
from users.views import (
    AutocompleteView,
    HomeView,
    LandingView,
    ProfileView,
    SearchUsersView,
    UploadPictureView,
    UserHomePage,
)


urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("home/", HomeView.as_view(), name="home"),
    path("home/search/", SearchUsersView.as_view(), name="search"),
    path("home/search/<str:username>/", UserHomePage.as_view(), name="user_home"),
    path("home/autocomplete/", AutocompleteView.as_view(), name="autocomplete"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("upload_picture/", UploadPictureView.as_view(), name="upload_picture"),
]
