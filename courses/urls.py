from django.urls import include, path, re_path
from courses.apis import (
    NotificationViewSet,
)
from courses.views import (
    CoursesView,
    OfficialCourseView,
    WeekView,
    course_details,
    create_course,
    delete_course_material,
    enroll,
    get_week_materials,
    publish_course,
    student_ban_status_update,
    submit_feedback,
    upload_assignment_material,
    upload_material,
    upload_student_submission,
)


urlpatterns = [
    path("courses/", CoursesView.as_view(), name="courses"),
    path("course_details/<int:course_id>/", course_details, name="course_details"),
    path("official/<int:course_id>/", OfficialCourseView.as_view(), name="official"),
    path("draft/<int:course_id>/", OfficialCourseView.as_view(), name="draft"),
    path("create_course/", create_course, name="create_course"),
    path(
        "get_week_materials/<int:course_id>/<int:week_number>/",
        get_week_materials,
        name="get_week_materials",
    ),
    path("week/<int:course_id>/", WeekView.as_view(), name="week"),
    path(
        "upload-material/<int:course_id>/<int:week_number>/",
        upload_material,
        name="upload_material",
    ),
    path(
        "upload-assignment/<int:course_id>/<int:week_number>/",
        upload_assignment_material,
        name="upload_assignment_material",
    ),
    path(
        "upload-student-submission/<int:course_id>/<int:assignment_id>/",
        upload_student_submission,
        name="upload_student_submission",
    ),
    path(
        "update-ban-status/<int:course_id>/<int:student_id>/",
        student_ban_status_update,
        name="update-ban-status",
    ),
    path(
        "delete_course_material/<int:course_material_id>/",
        delete_course_material,
        name="delete_course_material",
    ),
    path(
        "submit-feedback/<int:course_id>/",
        submit_feedback,
        name="submit_feedback",
    ),
    path("publish-course/<int:course_id>/", publish_course, name="publish_course"),
    path("enroll/<int:course_id>/", enroll, name="enroll"),
    path(
        "inbox/notifications/mark-as-read/<int:notification_id>/",
        NotificationViewSet.as_view({"patch": "mark_as_read"}),
        name="mark_as_read",
    ),
    re_path(
        r"^inbox/notifications/",
        include("notifications.urls", namespace="notifications"),
    ),
]
