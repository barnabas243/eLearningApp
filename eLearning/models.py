import os
from django.contrib.auth.models import AbstractUser, Group as DjangoGroup, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date


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
        dob (DateField): The date of birth of the user.

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
    STUDENT = 'student'
    TEACHER = 'teacher'
    USER_TYPE_CHOICES = [
        (STUDENT, _('Student')),
        (TEACHER, _('Teacher')),
    ]

    user_type = models.CharField(
        _('User type'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=STUDENT,
    )

    # Add custom fields
    photo = models.ImageField(upload_to='static/photos/', null=True, blank=True, default='photos/default_profile_picture.png')
    dob = models.DateField(_('Date of Birth'), null=True, blank=True)
    
    # Set max_length
    first_name = models.CharField(_('First name'), max_length=30)
    last_name = models.CharField(_('Last name'), max_length=150)
    email = models.EmailField(_('Email address'), max_length=254)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'dob', 'user_type']

    def calculate_age(self):
        """
        Calculate the age of the user based on their date of birth.

        Returns:
            int: The age of the user.
        """
        today = date.today()

        try: 
            birthday = self.dob.replace(year=today.year)
        # raised when birth date is February 29 and the current year is not a leap year
        except ValueError:
            birthday = self.dob.replace(year=today.year, day=self.dob.day-1)

        if birthday > today:
            return today.year - self.dob.year - 1
        else:
            return today.year - self.dob.year

    def __str__(self):
        return "{}".format(self.username)

    class Meta:
        """Meta class containing permissions for the User model."""
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        permissions = [
           # ("can_view_student_records", "Can view student records"),
            # Add more permissions as needed
        ]

    # Define related_name for groups and user_permissions fields
    groups = models.ManyToManyField(
        DjangoGroup,
        verbose_name=_('groups'),
        blank=True,
        related_name='custom_user_groups'  # Specify a unique related_name for groups
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name='custom_user_permissions'  # Specify a unique related_name for user_permissions
    )

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
        verbose_name = _('Status Update')
        verbose_name_plural = _('Status Updates')

class Feedback(models.Model):
    """
    Model representing feedback for a course.

    Attributes:
        user (ForeignKey): The user who provided the feedback.
        course (ForeignKey): The course for which the feedback is provided.
        content (TextField): The content of the feedback.
        created_at (DateTimeField): The date and time when the feedback was created.

    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Feedback')
        verbose_name_plural = _('Feedback')

class Course(models.Model):
    """
    Model representing a course.

    Attributes:
        name (str): The name of the course.
        description (str): A brief description of the course.
        teacher (ForeignKey): Relationship to the User model representing the teacher.
        duration_weeks (PositiveIntegerField): The duration of the course in weeks.
        status (str): Indicates whether the course is in draft or official mode.

    """
    DRAFT = 'draft'
    OFFICIAL = 'official'
    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (OFFICIAL, _('Official')),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    duration_weeks = models.PositiveIntegerField(_('Duration (weeks)'), default=20)  # Default duration is 20 weeks
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default=DRAFT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        unique_together = ('name', 'teacher')

def material_upload_path(instance, filename):
    """
    Function to determine the upload path for material files.

    Args:
        instance: The Material instance being uploaded.
        filename (str): The original filename of the file being uploaded.

    Returns:
        str: The upload path for the file.

    """
    # Construct the upload path based on the course name
    course_name = instance.course.name
    return os.path.join('static', course_name, 'materials', filename)

class Material(models.Model):
    """
    Model representing course materials.

    Attributes:
        PDF (str): Constant representing PDF material type.
        IMAGE (str): Constant representing image material type.
        MATERIAL_TYPE_CHOICES (list of tuple): Choices for the material type field.
        course (ManyToManyField): Relationship to Course model.
        file (FileField): Field for uploading material files.
        type (CharField): Field for specifying material type.

    """
    PDF = 'pdf'
    IMAGE = 'image'
    MATERIAL_TYPE_CHOICES = [
        (PDF, _('PDF')),
        (IMAGE, _('Image')),
    ]
    file = models.FileField(upload_to=material_upload_path)
    type = models.CharField(_('Material Type'), max_length=20, choices=MATERIAL_TYPE_CHOICES)

    class Meta:
        verbose_name = _('Material')
        verbose_name_plural = _('Materials')

class CourseMaterial(models.Model):
    """
    Model representing the linking of course materials to weeks of a course.

    Attributes:
        course (ForeignKey): The course to which the material is linked.
        materials (ManyToManyField): Relationship to Material model.
        week_number (PositiveIntegerField): The week number to which the materials are linked.

    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_materials')
    materials = models.ManyToManyField(Material, related_name='course_materials')
    week_number = models.PositiveIntegerField(_('Week Number'))

    class Meta:
        verbose_name = _('Course Material')
        verbose_name_plural = _('Course Materials')
        unique_together = ['course', 'week_number'] 

class Assignment(models.Model):
    """
    Model representing an assignment for a course.

    Attributes:
        course (ForeignKey): The course to which the assignment belongs.
        name (str): The name of the assignment.
        description (TextField): Description of the assignment.
        duration_days (PositiveIntegerField): The duration of the assignment in days.

    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_days = models.PositiveIntegerField(_('Duration (days)'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Assignment')
        verbose_name_plural = _('Assignments')

class Enrollment(models.Model):
    """
    Model representing a student's enrollment in a course.

    Attributes:
        student (ForeignKey): The student who is enrolled in the course.
        course (ForeignKey): The course in which the student is enrolled.
        start_date (DateField): The start date of the enrollment.

    """
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_date = models.DateField()

    class Meta:
        verbose_name = _('Enrollment')
        verbose_name_plural = _('Enrollments')
