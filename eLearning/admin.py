from django.contrib import admin
from .models import User, StatusUpdate, Feedback, Course, CourseMaterial, Assignment, Enrollment
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type')
    list_filter = ('user_type',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'photo', 'date_of_birth', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'photo', 'date_of_birth', 'user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['groups'].required = False  # Allow groups to be optional
        return form

    
admin.site.register(User, UserAdmin)
admin.site.register(StatusUpdate)
admin.site.register(Feedback)
admin.site.register(Course)
admin.site.register(CourseMaterial)
admin.site.register(Assignment)
admin.site.register(Enrollment)
