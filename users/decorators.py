from django.http import HttpResponseForbidden
from functools import wraps

from courses.models import Enrolment


def teacher_required(view_func):
    """
    Decorator to restrict access to views/methods only for users in the teacher group.

    :param view_func: The view function to decorate.
    :type view_func: function
    :return: Decorated function.
    :rtype: function
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name="teacher").exists():
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You are not authorized to access this page.")

    return wrapper


def student_required(view_func):
    """
    Decorator to restrict access to views/methods only for users in the student group.

    :param view_func: The view function to decorate.
    :type view_func: function
    :return: Decorated function.
    :rtype: function
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name="student").exists():
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(
                "You are not authorized to access this page. STUDENT only."
            )

    return wrapper


def check_student_banned(view_func):
    """
    Decorator to check the banned status of the student.

    :param view_func: The view function to decorate.
    :type view_func: function
    :return: Decorated function.
    :rtype: function
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.groups.filter(name="student").exists():
            enrolment = Enrolment.objects.filter(student=request.user).first()
            if not enrolment:
                return HttpResponseForbidden("You are not enrolled into the course.")
            elif not enrolment.is_banned:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden(
                    "You are banned from accessing the course. Please contact awdtest04@gmail.com for more information."
                )
        else:
            return HttpResponseForbidden(
                "You are not authorized to access this page. STUDENT only."
            )

    return wrapper
