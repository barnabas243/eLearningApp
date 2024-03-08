import pytest
from django.contrib.admin.sites import AdminSite
from users.admin import UserAdmin
from users.models import User
from users.tests.fixtures import request_factory


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def user_admin(admin_site):
    return UserAdmin(User, admin_site)


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin123"
    )


@pytest.mark.django_db
class TestUserAdmin:
    def test_list_display(self, user_admin):
        expected_list_display = (
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
        )
        assert user_admin.list_display == expected_list_display

    def test_list_filter(self, user_admin):
        expected_list_filter = ("user_type",)
        assert user_admin.list_filter == expected_list_filter

    def test_get_form(self, user_admin, request_factory, superuser):
        # Create a mock request object
        request = request_factory.get("/admin/users/user/")
        request.user = superuser  # Assign the superuser to the request

        # Call the get_form method
        form = user_admin.get_form(request)

        # Check if the form is returned
        assert form is not None

        # Check if the can_add_related attribute of the groups field widget is True
        assert form.base_fields["groups"].widget.can_add_related == True

        # Check if the can_change_related attribute of the groups field widget is True
        assert form.base_fields["groups"].widget.can_change_related == True
