import pytest
from courses.models import Course
from users.models import User
from users.tests.factories import UserFactory
from courses.tests.factories import (
    AssignmentFactory,
    CourseFactory,
    CourseMaterialFactory,
    EnrolmentFactory,
)


@pytest.fixture
def enrolled_student_user():
    return UserFactory(
        user_type=User.STUDENT, password="ThisMustBeAn3xtremelyComplexed"
    )


@pytest.fixture
def not_enrolled_student_user():
    return UserFactory(
        user_type=User.STUDENT, password="ThisMustBeAn3xtremelyComplexed"
    )


@pytest.fixture
def teacher_user():
    return UserFactory(
        user_type=User.TEACHER, password="ThisMustBeAn3xtremelyComplexed"
    )


@pytest.fixture
def official_course(teacher_user):
    return CourseFactory(teacher=teacher_user, status=Course.OFFICIAL, duration_weeks=2)


@pytest.fixture
def official_course_1_week(teacher_user):
    return CourseFactory(teacher=teacher_user, status=Course.OFFICIAL, duration_weeks=1)


@pytest.fixture
def draft_course(teacher_user):
    return CourseFactory(teacher=teacher_user)


@pytest.fixture
def enrol(enrolled_student_user, official_course):
    return EnrolmentFactory(student=enrolled_student_user, course=official_course)


@pytest.fixture
def courseMaterials(official_course):
    return CourseMaterialFactory.create_batch(5, course=official_course)


@pytest.fixture
def assignmentMaterial(official_course):
    return AssignmentFactory.create(course=official_course, week_number=1)
