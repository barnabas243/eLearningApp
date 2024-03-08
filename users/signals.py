import logging
from django.db import IntegrityError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

# Define fixed permissions for students and teachers
STUDENT_PERMISSIONS = [
    ("view_user_profile", "Can view user profile"),
    ("edit_user_profile", "Can edit user profile"),
    ("change_user_password", "Can edit user password"),
    ("view_enrolment", "Can view enrolment"),
    ("view_assignment", "Can view assignment"),
    ("view_statusupdate", "Can view status updates"),
    ("add_statusupdate", "Can add status updates"),
    ("view_course", "Can view course"),
    ("add_feedback", "Can add feedback"),
    ("view_assignment_submission", "Can view assignment submission"),
    ("add_assignment_submission", "Can add assignment submission"),
]

TEACHER_PERMISSIONS = [
    ("view_user_profile", "Can view user profile"),
    ("edit_user_profile", "Can edit user profile"),
    ("change_user_password", "Can edit user password"),
    ("view_enrolment", "Can view enrolment"),
    ("change_enrolment", "Can edit enrolment"),
    ("delete_enrolment", "Can delete enrolment"),
    ("view_feedback", "Can view feedback"),
    ("view_assignment_submission", "Can view assignment submission"),
    ("view_assignment", "Can view assignment"),
    ("add_assignment", "Can add assignment"),
    ("delete_assignment", "Can delete assignment"),
    ("view_statusupdate", "Can view status updates"),
    ("add_statusupdate", "Can add status updates"),
    ("view_course", "Can view course"),
    ("add_course", "Can add course"),
    ("edit_course", "Can edit course"),
    ("delete_course", "Can delete course"),
]


def assign_user_to_group(sender, instance, created, **kwargs):
    if created:
        from users.models import User

        content_type = ContentType.objects.get_for_model(User)

        if instance.user_type == User.STUDENT:
            student_group, student_group_created = Group.objects.get_or_create(
                name="student"
            )
            if student_group_created:
                create_group_with_permissions(
                    student_group, STUDENT_PERMISSIONS, content_type
                )
            instance.groups.add(student_group)
        elif instance.user_type == User.TEACHER:
            teacher_group, teacher_group_created = Group.objects.get_or_create(
                name="teacher"
            )
            if teacher_group_created:
                create_group_with_permissions(
                    teacher_group, TEACHER_PERMISSIONS, content_type
                )
            instance.groups.add(teacher_group)


def create_group_with_permissions(group, permissions, content_type):
    try:
        group.permissions.add(*get_or_create_permissions(permissions, content_type))
    except IntegrityError as e:
        logger.error(
            f"Error occurred while adding permissions to group {group.name}: {e}"
        )


def get_or_create_permissions(permissions, content_type):
    return [
        Permission.objects.get_or_create(
            codename=codename, name=name, content_type=content_type
        )[0]
        for codename, name in permissions
    ]
