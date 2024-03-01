from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import FormView

from eLearning.forms import UserLoginForm, UserRegistrationForm


import logging

logger = logging.getLogger(__name__)


class LoginView(FormView):
    """
    Renders the login page and handles user login.

    Inherits from FormView, which renders a form and processes submitted data.
    """

    template_name = "public/login.html"
    form_class = UserLoginForm

    def form_valid(self, form):
        """
        Validates the submitted form data and logs in the user if valid.

        :param form: The submitted login form.
        :type form: forms.UserLoginForm
        :return: Redirects the user to the dashboard upon successful login,
                 otherwise displays an error message.
        :rtype: HttpResponseRedirect or HttpResponse
        """
        user = form.get_user()
        if user is not None and user.is_active:
            login(self.request, user)
            next_url = self.request.GET.get("next", None)
            if next_url:
                return redirect(next_url)
            else:
                return redirect("dashboard")
        else:
            messages.error(self.request, "Invalid username or password.")
            return self.render_to_response(self.get_context_data(form=form))

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

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to the login page.

        Processes the submitted login form data.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Variable length argument list.
        :type args: tuple
        :param kwargs: Arbitrary keyword arguments.
        :type kwargs: dict

        :return: Redirects the user to the dashboard upon successful login,
                 otherwise displays an error message.
        :rtype: HttpResponseRedirect or HttpResponse
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            messages.error(self.request, "Invalid username or password.")
            return self.form_invalid(form)


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

    def form_valid(self, form):
        """
        Handles form submission when the form data is valid.

        Attempts to create a new user account using the form data. If successful,
        logs in the new user and redirects to the dashboard page. If an error occurs
        during registration, displays an error message and re-renders the registration
        form.

        :param form: The validated form instance.
        :type form: forms.Form

        :return: Redirects to the dashboard upon successful registration, or re-renders
            the registration form with error messages if registration fails.
        :rtype: HttpResponseRedirect or HttpResponse
        """
        try:
            user = form.save()
            login(self.request, user)
            return redirect("dashboard")
        except Exception as e:
            print(f"An error occurred during registration: {e}")
            messages.error(
                self.request, "An unexpected error occurred. Please try again later."
            )
            return self.render_to_response(self.get_context_data(form=form))

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

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to the registration form.

        If the form data is valid, calls the form_valid method to process the form.
        Otherwise, re-renders the registration form with validation errors.

        :param request: The HTTP request object.
        :type request: HttpRequest

        :return: Redirects to the dashboard upon successful registration, or re-renders
            the registration form with error messages if form validation fails.
        :rtype: HttpResponseRedirect or HttpResponse
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PasswordChangeViewCustom(PasswordChangeView):
    template_name = "public/password_change.html"
    success_url = reverse_lazy("password_change_done")
