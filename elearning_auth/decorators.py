from django.http import HttpResponseForbidden
from django.urls import reverse
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Add the ?next parameter to redirect back to the original URL after login
            next_url = request.path_info
            login_url = f"{reverse('login')}?next={next_url}"
            messages.error(request, "You need to log in to access this page.")
            return redirect(login_url)
        return view_func(request, *args, **kwargs)

    return wrapper
