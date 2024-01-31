from django.urls import path
from eLearning import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password_change/', views.password_change_view.as_view(), name='password_change'),
    path('courses/', views.courses_view, name='courses'),
    path('dashboard/',views.dashboard_view, name='dashboard'),
    path('profile/',views.profile_view, name="profile"),
]