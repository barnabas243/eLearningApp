import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from users.models import User
from users.signals import assign_user_to_group, STUDENT_PERMISSIONS, TEACHER_PERMISSIONS
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestAssignUserToGroupSignal:
    @pytest.fixture
    def student_user(self):
        return UserFactory(user_type=User.STUDENT)

    @pytest.fixture
    def teacher_user(self):
        return UserFactory(user_type=User.TEACHER)

    @pytest.fixture
    def content_type(self):
        return ContentType.objects.get_for_model(User)

    def test_student_user_assigned_to_student_group(self, student_user):
        post_save.disconnect(assign_user_to_group, sender=User)

        assign_user_to_group(sender=User, instance=student_user, created=True)

        student_group = Group.objects.get(name="student")
        assert student_group in student_user.groups.all()
        assert student_user.groups.count() == 1

    def test_teacher_user_assigned_to_teacher_group(self, teacher_user):
        post_save.disconnect(assign_user_to_group, sender=User)

        assign_user_to_group(sender=User, instance=teacher_user, created=True)

        teacher_group = Group.objects.get(name="teacher")
        assert teacher_group in teacher_user.groups.all()
        assert teacher_user.groups.count() == 1

    def test_student_group_has_correct_permissions(self, student_user, content_type):
        post_save.disconnect(assign_user_to_group, sender=User)

        assign_user_to_group(sender=User, instance=student_user, created=True)

        student_group = Group.objects.get(name="student")
        expected_permissions = Permission.objects.filter(
            codename__in=[codename for codename, _ in STUDENT_PERMISSIONS],
            content_type=content_type,
        )
        permissions = student_group.permissions.all()

        assert set(permissions) == set(expected_permissions)

    def test_teacher_group_has_correct_permissions(self, teacher_user, content_type):
        post_save.disconnect(assign_user_to_group, sender=User)

        assign_user_to_group(sender=User, instance=teacher_user, created=True)

        teacher_group = Group.objects.get(name="teacher")
        expected_permissions = Permission.objects.filter(
            codename__in=[codename for codename, _ in TEACHER_PERMISSIONS],
            content_type=content_type,
        )
        permissions = teacher_group.permissions.all()

        assert set(permissions) == set(expected_permissions)
