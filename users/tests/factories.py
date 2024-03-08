# In users/tests/factories.py
from factory.django import DjangoModelFactory
from factory import (
    Faker,
    Sequence,
    SubFactory,
    LazyFunction,
)
from django.db import IntegrityError
from users.models import StatusUpdate, User
from django.utils import timezone
from django.contrib.auth.models import Group
from users.signals import assign_user_to_group


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    email = Sequence(lambda n: "user{}@example.com".format(n))  # unique
    username = Sequence(lambda n: f"user{n}")  # unique
    date_of_birth = Faker("date_between", start_date="-40y", end_date="-18y")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Exclude unique constraints when creating instances
        while True:
            try:
                # Create the user instance
                instance = model_class.objects.create_user(*args, **kwargs)

                # Trigger the signal after creating the user instance
                assign_user_to_group(sender=User, instance=instance, created=True)

                return instance
            except IntegrityError:
                # Retry with a different email if IntegrityError occurs
                kwargs["email"] = f"user{User.objects.count()}@example.com"


class StatusUpdateFactory(DjangoModelFactory):
    class Meta:
        model = StatusUpdate

    user = SubFactory(UserFactory)
    content = Faker("text")
    created_at = LazyFunction(timezone.now)


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    name = Sequence(lambda n: f"group_{n}")
