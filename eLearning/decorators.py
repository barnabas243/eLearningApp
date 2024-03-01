from django.http import HttpResponseForbidden
from django.urls import reverse
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

from django.contrib.auth.decorators import user_passes_test


def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Add the ?next parameter to redirect back to the original URL after login
            next_url = request.path_info
            login_url = f"{reverse('login')}?next={next_url}"
            messages.error(request, "You need to log in to access this page.")
            return redirect(
                login_url
            )  # Redirect to the login page with ?next parameter
        return view_func(request, *args, **kwargs)

    return wrapper


def teacher_required(view_func):
    """
    Decorator to restrict access to views/methods only for users in the teacher group.
    """

    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name="teacher").exists():
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to unauthorized page or return HttpResponseForbidden
            return HttpResponseForbidden("You are not authorized to access this page.")

    return _wrapped_view


def student_required(view_func):
    """
    Decorator to restrict access to views/methods only for users in the teacher group.
    """

    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name="student").exists():
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to unauthorized page or return HttpResponseForbidden
            return HttpResponseForbidden("You are not authorized to access this page.")

    return _wrapped_view
