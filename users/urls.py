from django.urls import path
from users.views import (
    AutocompleteView,
    DashboardView,
    LandingView,
    ProfileView,
    SearchUsersView,
    UploadPictureView,
    UserHomePage,
)


urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard/search/", SearchUsersView.as_view(), name="search"),
    path("dashboard/search/<str:username>/", UserHomePage.as_view(), name="user_home"),
    path("dashboard/autocomplete/", AutocompleteView.as_view(), name="autocomplete"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("upload_picture/", UploadPictureView.as_view(), name="upload_picture"),
]
