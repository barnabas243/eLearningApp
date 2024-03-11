from django.http import HttpResponseForbidden
from functools import wraps


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
