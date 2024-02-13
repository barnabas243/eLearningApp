from django.contrib import admin
from .models import User, StatusUpdate, Feedback, Course, CourseMaterial, Assignment, Enrollment
from django.contrib.auth.models import Group

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'date_of_birth', 'user_type')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('user_type',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'groups':
            # Ensure queryset is fetched properly
            kwargs['queryset'] = Group.objects.all().order_by('name')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    

class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    search_fields = ('user__username', 'content')

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'content', 'created_at')
    search_fields = ('user__username', 'course__name', 'content')

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'duration_weeks', 'status', 'start_date')
    search_fields = ('name', 'teacher__username')
    list_filter = ('status',)

class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('course', 'material', 'week_number')
    search_fields = ('course__name', 'material__name')
    list_filter = ('week_number',)

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'duration_days', 'is_submitted')
    search_fields = ('course__name', 'name')
    list_filter = ('is_submitted',)

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course')
    search_fields = ('student__username', 'course__name')
    
admin.site.register(User, UserAdmin)
admin.site.register(StatusUpdate, StatusUpdateAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseMaterial, CourseMaterialAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
