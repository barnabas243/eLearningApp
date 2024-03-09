from django.contrib import admin

from courses.models import (
    AssignmentSubmission,
    Feedback,
    Course,
    CourseMaterial,
    Assignment,
    Enrolment,
)
from django.contrib import admin

admin.site.register(Feedback)
admin.site.register(Course)
admin.site.register(CourseMaterial)
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Enrolment)
