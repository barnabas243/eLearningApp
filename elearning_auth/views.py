from django.shortcuts import redirect
from django.contrib.auth import logout


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
