from django.http import HttpResponseForbidden
from functools import wraps
from django.shortcuts import render

from courses.models import Enrolment


def teacher_required(view_func):
    """
    Decorator to restrict access to views/methods only for users in the teacher group.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name="teacher").exists():
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to unauthorized page or return HttpResponseForbidden
            return HttpResponseForbidden("You are not authorized to access this page.")

    return wrapper


def student_required(view_func):
    """
    Decorator to restrict access to views/methods only for users in the student group.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name="student").exists():
            # Check if the student is not banned
            enrolment = Enrolment.objects.filter(
                student=request.user, is_banned=False
            ).first()
            if enrolment:
                return view_func(request, *args, **kwargs)
            else:
                error_message = "You are banned from accessing this page."
                return render(
                    request,
                    "errors/403.html",
                    {"error_message": error_message},
                    status=403,
                )  # Render the custom error page with error message
        else:
            error_message = "This is a STUDENT ONLY page. You are not authorized to access this page."
            return render(
                request, "errors/403.html", {"error_message": error_message}, status=403
            )  # Render the custom error page with error message

    return wrapper
