from django.shortcuts import redirect
from django.contrib.auth import logout
from django.views.generic import FormView

from elearning_auth.forms import UserLoginForm, UserRegistrationForm


import logging

logger = logging.getLogger(__name__)


class LoginView(FormView):
    """
    Renders the login page and handles user login.

    Inherits from FormView, which renders a form and processes submitted data.
    """

    template_name = "public/login.html"
    form_class = UserLoginForm

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to the login page.

        Redirects authenticated users to the dashboard.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Variable length argument list.
        :type args: tuple
        :param kwargs: Arbitrary keyword arguments.
        :type kwargs: dict

        :return: Redirects authenticated users to the dashboard,
                 otherwise renders the login page.
        :rtype: HttpResponseRedirect or HttpResponse
        """
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)


def logout_user(request):
    """
    Logs out the user and redirects to the login page.

    :param request: The HTTP request object.
    :type request: HttpRequest

    :return: Redirects the user to the login page after logout.
    :rtype: HttpResponseRedirect
    """
    logout(request)
    return redirect("login")


class RegisterView(FormView):
    """
    View for user registration.

    Displays a registration form to allow users to create a new account.

    :ivar template_name: The name of the template to render for registration.
    :vartype template_name: str
    :ivar form_class: The form class used for user registration.
    :vartype form_class: Type[forms.Form]
    """

    template_name = "public/register.html"
    form_class = UserRegistrationForm

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to the registration page.

        If the user is already authenticated, redirects them to the dashboard.
        Otherwise, renders the registration form.

        :param request: The HTTP request object.
        :type request: HttpRequest

        :return: Redirects to the dashboard if the user is authenticated, otherwise
            renders the registration form.
        :rtype: HttpResponseRedirect or HttpResponse
        """
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)
