from django.urls import path
from eLearning import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('password_change/', views.PasswordChangeViewCustom.as_view(), name='password_change'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name="profile"),
    path('upload_picture/', views.UploadPictureView.as_view(), name="upload_picture"),
    path('create_course/', views.create_course, name='create_course'),
    path('draft/<str:course_name>/', views.DraftCourseView.as_view(), name='draft'),
    path('get_week_materials/', views.get_week_materials, name='get_week_materials'),
    path('upload_material/', views.upload_material, name='upload_material'),
]
