from django.urls import path
from eLearning.views.auth import *
from eLearning.views.courses import *
from eLearning.views.users import *

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password_change/', PasswordChangeViewCustom.as_view(), name='password_change'),
    
    path('courses/', CoursesView.as_view(), name='courses'),
    path('course_details/<int:course_id>/', course_details, name='course_details'),
    
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/search/', SearchUsersView.as_view(), name='search'),
    path('dashboard/search/<str:username>/', UserHomePage.as_view(), name='user_home'),
    path('dashboard/autocomplete/', AutocompleteView.as_view(), name='autocomplete'),
    
    path('profile/', ProfileView.as_view(), name="profile"),
    path('upload_picture/', UploadPictureView.as_view(), name="upload_picture"),
    
    path('official/<int:course_id>/', OfficialCourseView.as_view(), name='official'),
    path('draft/<int:course_id>/', OfficialCourseView.as_view(), name='draft'),
    path('create_course/', create_course, name='create_course'), # only allow POST
    
    path('get_week_materials/<int:course_id>/<int:week_number>/', get_week_materials, name='get_week_materials'),
    path('week/<int:course_id>/', WeekView.as_view(), name='week'),
    
    path('upload-material/<int:course_id>/<int:week_number>/', upload_material, name='upload_material'),
    path('upload-assignment/<int:course_id>/<int:week_number>/', upload_assignment_material, name='upload_assignment_material'),
    path('upload-student-submission/<int:assignment_id>/',upload_student_submission, name='upload_student_submission'),
    path('update-ban-status/<int:course_id>/<int:student_id>/',student_ban_status_update,name="update-ban-status"),
    path('delete_course_material/<int:course_material_id>/', delete_course_material, name='delete_course_material'),
    path('submit-feedback/<int:course_id>/<int:student_id>/', submit_feedback, name='submit_feedback'),
    path('publish-course/<int:course_id>/', publish_course, name='publish_course'),
    
    path('enroll/<int:course_id>/', enroll, name='enroll'),
]
