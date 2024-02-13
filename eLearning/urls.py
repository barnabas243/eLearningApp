from django.urls import path
from eLearning import views

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('password_change/', views.PasswordChangeViewCustom.as_view(), name='password_change'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('course_details/<int:course_id>/', views.course_details, name='course_details'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/search/', views.SearchUsersView.as_view(), name='search'),
    path('dashboard/search/<str:username>/', views.UserHomePage.as_view(), name='user_home'),
    path('dashboard/autocomplete/', views.AutocompleteView.as_view(), name='autocomplete'),
    path('profile/', views.ProfileView.as_view(), name="profile"),
    path('upload_picture/', views.UploadPictureView.as_view(), name="upload_picture"),
    path('create_course/', views.create_course, name='create_course'),
    path('official/<int:course_id>/', views.OfficialCourseView.as_view(), name='official'),
    path('draft/<int:course_id>/', views.DraftCourseView.as_view(), name='draft'),
    path('get_week_materials/<int:course_id>/<int:week_number>/', views.get_week_materials, name='get_week_materials'),
    path('upload-material/<int:course_id>/<int:week_number>/', views.upload_material, name='upload_material'),
    path('delete_course_material/<int:course_material_id>/', views.delete_course_material, name='delete_course_material'),
    path('publish-course/<int:course_id>/', views.publish_course, name='publish_course'),
    path('enroll/<int:course_id>/', views.enroll, name='enroll'),
]
