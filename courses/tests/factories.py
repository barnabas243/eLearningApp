from factory.django import DjangoModelFactory
from factory import SubFactory, Faker
from courses.models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseMaterial,
    Enrolment,
    Feedback,
)
from users.tests.factories import UserFactory  # Import the UserFactory from another app


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    name = Faker("sentence", nb_words=4)
    summary = Faker("text")
    description = Faker("paragraph")
    teacher = SubFactory(UserFactory)
    duration_weeks = Faker("random_int", min=1, max=50)
    created_at = Faker("date_time")
    last_modified = Faker("date_time")
    status = Course.DRAFT  # Default status is DRAFT


class CourseMaterialFactory(DjangoModelFactory):
    class Meta:
        model = CourseMaterial

    course = SubFactory(CourseFactory)
    material = Faker("file_name", category="document")
    week_number = Faker("random_int", min=1, max=20)  # Adjust max week number as needed


class AssignmentFactory(DjangoModelFactory):
    class Meta:
        model = Assignment

    course = SubFactory(CourseFactory)
    name = Faker("text", max_nb_chars=100)
    instructions = Faker("text")
    week_number = Faker("random_int", min=1, max=20)  # Adjust max week number as needed
    duration_days = Faker("random_int", min=1, max=10)  # Adjust max duration as needed


class AssignmentSubmissionFactory(DjangoModelFactory):
    class Meta:
        model = AssignmentSubmission

    assignment = SubFactory(AssignmentFactory)
    student = SubFactory(UserFactory)
    submitted_at = Faker("date_time_this_year")
    assignment_file = Faker("file_name", category="document")
    teacher_comments = Faker("text")
    grade = Faker("random_int", min=0, max=100)


class FeedbackFactory(DjangoModelFactory):
    class Meta:
        model = Feedback

    user = SubFactory(UserFactory)
    course = SubFactory(CourseFactory)
    course_rating = Faker("random_int", min=1, max=5)
    teacher_rating = Faker("random_int", min=1, max=5)
    comments = Faker("text")
    created_at = Faker("date_time_this_year")


class EnrolmentFactory(DjangoModelFactory):
    class Meta:
        model = Enrolment

    student = SubFactory(UserFactory)
    course = SubFactory(CourseFactory)
    is_banned = False
    is_completed = False
