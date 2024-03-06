import os
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


def profile_picture_upload_path(instance, filename):
    """
    Function to determine the upload path for profile pictures.

    Args:
        instance: The user instance for which the profile picture is uploaded.
        filename (str): The original filename of the profile picture being uploaded.

    Returns:
        str: The upload path for the profile picture.

    """
    # Construct the upload path based on the user's username
    username = instance.username
    return os.path.join("photos", f"{username}", filename)


class User(AbstractUser):
    """
    Custom user model representing different types of users in the eLearning application.

    Attributes:
        user_type (str): The type of user, either 'student' or 'teacher'.
        photo (ImageField): The profile photo of the user.
        username (str): The unique username of the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        email (EmailField): The email address of the user.
        date_of_birth (DateField): The date of birth of the user.

    Inherited Attributes from AbstractUser:
        password (str): The password of the user.
        last_login (DateTimeField): The date and time of the last login.
        is_superuser (bool): Indicates whether the user has superuser privileges.
        is_staff (bool): Indicates whether the user is staff.
        date_joined (DateTimeField): The date and time when the user joined.
        groups (ManyToManyField): The groups to which the user belongs.
        user_permissions (ManyToManyField): The permissions granted to the user.

    """

    # Define choices for user types
    STUDENT = "student"
    TEACHER = "teacher"
    USER_TYPE_CHOICES = [
        (STUDENT, _("Student")),
        (TEACHER, _("Teacher")),
    ]

    user_type = models.CharField(
        _("User type"),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=STUDENT,
    )

    # Add custom fields
    photo = models.ImageField(
        upload_to=profile_picture_upload_path,
        null=True,
        blank=True,
        default="/photos/default_profile_picture.png",
    )
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)

    # Set max_length
    first_name = models.CharField(_("First name"), max_length=30)
    last_name = models.CharField(_("Last name"), max_length=150)
    email = models.EmailField(
        _("Email address"), max_length=254, unique=True
    )  # Make email field unique
    username = models.CharField(_("Username"), max_length=150, unique=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name", "last_name", "date_of_birth", "user_type"]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.get_full_name()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

        unique_together = ["username", "email"]


class StatusUpdate(models.Model):
    """
    Model representing a status update by a user.

    Attributes:
        user (ForeignKey): The user who posted the status update.
        content (TextField): The content of the status update.
        created_at (DateTimeField): The date and time when the status update was created.

    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Status Update")
        verbose_name_plural = _("Status Updates")


# Define fixed permissions for students and teachers
student_permissions = [
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

teacher_permissions = [
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


# Example usage: Assign users to groups based on user_type
@receiver(post_save, sender=User)
def assign_user_to_group(sender, instance, created, **kwargs):
    if created:
        # Get content type for the User model
        content_type = ContentType.objects.get_for_model(User)

        # Bulk create permissions for student group if they don't exist
        student_group, student_group_created = Group.objects.get_or_create(
            name="student"
        )

        if student_group_created:
            for codename, name in student_permissions:
                try:
                    permission, created = Permission.objects.get_or_create(
                        codename=codename, name=name, content_type=content_type
                    )
                    student_group.permissions.add(permission)
                except IntegrityError as e:
                    print(
                        f"An error occurred while adding permission to student group: {e}"
                    )

        # Bulk create permissions for teacher group if they don't exist
        teacher_group, teacher_group_created = Group.objects.get_or_create(
            name="teacher"
        )

        if teacher_group_created:
            for codename, name in teacher_permissions:
                try:
                    permission, created = Permission.objects.get_or_create(
                        codename=codename, name=name, content_type=content_type
                    )
                    teacher_group.permissions.add(permission)
                except IntegrityError as e:
                    print(
                        f"An error occurred while adding permission to teacher group: {e}"
                    )

        # Assign users to groups based on user_type
        if instance.user_type == User.STUDENT:
            instance.groups.add(student_group)
        elif instance.user_type == User.TEACHER:
            instance.groups.add(teacher_group)
