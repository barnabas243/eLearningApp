import os
from django.contrib.auth.models import Group
from django.db import IntegrityError, models
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from django.db.models.signals import post_save
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator,
)

from users.models import User


class Course(models.Model):
    """
    Model representing a course.

    Attributes:
        name (str): The name of the course.
        summary (str): The summary of the course
        description (str): The Details concerning the course
        teacher (ForeignKey): Relationship to the User model representing the teacher.
        duration_weeks (PositiveIntegerField): The duration of the course in weeks.
        status (str): Indicates whether the course is in draft or official mode.

    """

    DRAFT = "draft"
    OFFICIAL = "official"
    STATUS_CHOICES = [
        (DRAFT, _("Draft")),
        (OFFICIAL, _("Official")),
    ]

    name = models.CharField(max_length=100)
    summary = models.TextField()
    description = RichTextField()  # CKEditor
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="courses_taught"
    )
    duration_weeks = models.PositiveIntegerField(
        _("Duration (weeks)"), default=20, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default=DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(null=True)

    start_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

    def datetime_from_start_date(self, week_number):
        if self.start_date:
            timedelta_weeks = max(
                week_number - 1, 0
            )  # week 1 will be 0, week 2 is 1...
            return self.start_date + timezone.timedelta(weeks=timedelta_weeks)
        else:
            # Handle the case where start_date is None
            return None

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        unique_together = ["name", "teacher"]

    def get_absolute_url(self):
        return reverse("official", kwargs={"course_id": self.pk})


def material_upload_path(instance, filename):
    """
    Function to determine the upload path for material files.

    Args:
        instance: The CourseMaterial instance being uploaded.
        filename (str): The original filename of the file being uploaded.

    Returns:
        str: The upload path for the file.

    """
    # Construct the upload path based on the course name
    course_id = instance.course.id
    course_name = slugify(
        instance.course.name
    )  # Convert course name to a valid filename
    return os.path.join("materials", f"{course_id}-{course_name}", filename)


class CourseMaterial(models.Model):
    """
    Model representing the linking of course materials to weeks of a course.

    Attributes:
        course (ForeignKey): The course to which the material is linked.
        materials (ManyToManyField): Relationship to Material model.
        week_number (PositiveIntegerField): The week number to which the materials are linked.

    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="course_materials"
    )
    material = models.FileField(upload_to=material_upload_path)
    week_number = models.PositiveIntegerField(_("Week Number"))

    class Meta:
        verbose_name = _("Course Material")
        verbose_name_plural = _("Course Materials")
        unique_together = ["material", "course", "week_number"]

    def __str__(self):
        return f"{self.course.name} - {self.get_base_name()}"

    def get_base_name(self):
        """
        Method to return the base name of the uploaded file.
        """
        return os.path.basename(self.material.name)


class Assignment(models.Model):
    """
    Model representing an assignment for a course.

    Attributes:
        course (ForeignKey): The course to which the assignment belongs.
        name (str): The name of the assignment.
        instructions (RichTextField): Description of the assignment.
        week_number (PositiveIntegerField): The week number associated with the assignment.
        duration_days (PositiveIntegerField): The duration of the assignment in days.
    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assignments"
    )
    name = models.CharField(max_length=100)
    instructions = RichTextField()
    week_number = models.PositiveIntegerField(
        _("Week Number"), validators=[MinValueValidator(1)]
    )
    duration_days = models.PositiveIntegerField(
        _("Duration (days)"), validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return self.name

    def get_assignment_deadline(self):
        """
        Calculate the deadline for the assignment based on the course start date and assignment duration.
        """
        return self.course.datetime_from_start_date(
            self.week_number
        ) + timezone.timedelta(days=self.duration_days)

    @staticmethod
    def get_materials(course, week_number):
        """
        Retrieve materials related to this assignment for the given course and week number.
        """
        return CourseMaterial.objects.filter(course=course, week_number=week_number)

    class Meta:
        verbose_name = _("Assignment")
        verbose_name_plural = _("Assignments")


def assignment_upload_path(instance, filename):
    """
    Function to determine the upload path for material files.

    Args:
        instance: The CourseMaterial instance being uploaded.
        filename (str): The original filename of the file being uploaded.

    Returns:
        str: The upload path for the file.

    """
    # Construct the upload path based on the course name
    course_id = instance.assignment.course.id
    course_name = slugify(
        instance.assignment.course.name
    )  # Convert course name to a valid filename
    week_number = instance.assignment.week_number
    return os.path.join(
        "assignments_submission",
        f"{course_id}-{course_name}",
        f"week {week_number}",
        filename,
    )


class AssignmentSubmission(models.Model):
    """
    Model representing a submission of an assignment by a student.

    Attributes:
        assignment (ForeignKey): The assignment that was submitted.
        student (ForeignKey): The student who submitted the assignment.
        submitted_at (DateTimeField): The datetime when the assignment was submitted.
        assignment_file (FileField): The file containing the assignment submission.
        teacher_comments (TextField): Comments provided by the teacher for the submission.
        grade (DecimalField): The grade received for the submission.

    """

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="assignment_submissions"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    assignment_file = models.FileField(
        upload_to=assignment_upload_path, validators=[FileExtensionValidator(["pdf"])]
    )
    teacher_comments = models.TextField(null=True, blank=True)
    grade = models.DecimalField(
        _("Grade"),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.student} - {self.assignment}"

    class Meta:
        verbose_name = _("Assignment Submission")
        verbose_name_plural = _("Assignment Submissions")


class Feedback(models.Model):
    """
    Model representing feedback for a course.

    Attributes:
        user (ForeignKey): The user who provided the feedback.
        course (ForeignKey): The course for which the feedback is provided.
        course_rating (IntegerField): The rating assigned to the course.
        teacher_rating (IntegerField): The rating assigned to the teacher.
        comments (TextField): The content of the feedback.
        created_at (DateTimeField): The date and time when the feedback was created.

    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, verbose_name=_("Course")
    )
    course_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Course Rating"),
    )
    teacher_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Teacher Rating"),
    )
    comments = models.TextField(verbose_name=_("Comments"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")

    def __str__(self):
        return f"Feedback for {self.course} by {self.user}"


class Enrolment(models.Model):
    """
    Model representing a student's Enrolment in a course.

    Attributes:
        student (ForeignKey): The student who is enrolled in the course.
        course (ForeignKey): The course in which the student is enrolled.
        is_banned (BooleanField): Indicates if the enrolment is banned.
        is_completed (BooleanField): Indicates if the enrolment is completed.

    """

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_banned = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    @staticmethod
    def is_student_enrolled(student, course):
        # Check if there exists an Enrolment record for the student and course
        return Enrolment.objects.filter(
            student=student, course=course, is_banned=False
        ).exists()

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.name}"

    class Meta:
        verbose_name = _("Enrolment")
        verbose_name_plural = _("Enrolments")


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
