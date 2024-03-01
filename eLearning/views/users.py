from itertools import groupby
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from django.views.generic import TemplateView, View, ListView, FormView
from django.contrib.auth.mixins import UserPassesTestMixin

from chat.models import ChatRoom

# from eLearning.forms import *
# from eLearning.models import *
from django.http import (
    HttpResponse,
    JsonResponse,
)
from django.template.loader import render_to_string
from django.urls import reverse
from eLearning.decorators import custom_login_required
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.views.decorators.csrf import csrf_exempt

import logging
from eLearning.forms import CreateCourseForm, ProfilePictureForm, StatusUpdateForm

from eLearning.models import Assignment, Enrolment, StatusUpdate, User
from eLearning.tasks import process_image

logger = logging.getLogger(__name__)


class LandingView(TemplateView):
    """
    Renders the landing page template for unauthenticated users.

    If the user is authenticated, redirects to the dashboard page.
    """

    template_name = "public/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(View):
    """
    View for rendering the dashboard page.

    This view handles requests to render the dashboard page for both students and teachers.
    The dashboard displays registered courses, status updates, course chats, and deadlines for the user.

    Attributes:
        template_student (str): The template file path for the student dashboard.
        template_teacher (str): The template file path for the teacher dashboard.
    """

    template_student = "user/student_dashboard.html"
    template_teacher = "user/teacher_dashboard.html"

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to render the dashboard page.

        This method retrieves necessary data based on the user type (student or teacher),
        and renders the corresponding dashboard template with the context.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.

        :return: The rendered dashboard page.
        :rtype: HttpResponse
        """
        user = request.user
        status_updates = StatusUpdate.objects.filter(user=user).order_by("-created_at")[
            :5
        ]

        if user.user_type == User.STUDENT:
            # Retrieve all enrollments for the student
            enrollments = Enrolment.objects.filter(student=user)
            # Extract the courses from enrollments
            registered_courses = [enrollment.course for enrollment in enrollments]
            # Query ChatRoom objects for registered courses
            course_chats = ChatRoom.objects.filter(course__in=registered_courses)
            # Query Assignment objects for registered courses
            deadlines = Assignment.objects.filter(
                course__in=registered_courses
            ).order_by("course")

            # Group assignments by course
            grouped_deadlines = {}
            for course, assignments in groupby(deadlines, key=lambda x: x.course):
                grouped_deadlines[course] = list(assignments)

            context = {
                "user": user,
                "registered_courses": registered_courses,
                "status_updates": status_updates,
                "course_chats": course_chats,
                "grouped_deadlines": grouped_deadlines,
                "statusUpdateForm": StatusUpdateForm,
            }
            return render(request, self.template_student, context)

        elif user.user_type == User.TEACHER:
            teacher = request.user
            draft_courses = teacher.courses_taught.filter(status="draft")
            official_courses = teacher.courses_taught.filter(status="official")

            context = {
                "user": teacher,
                "draft_courses": draft_courses,
                "official_courses": official_courses,
                "status_updates": status_updates,
                "createCourseForm": CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, self.template_teacher, context)

    def post(self, request, *args, **kwargs):
        # post status update
        form = StatusUpdateForm(data=request.POST)

        if form.is_valid:
            status_update = form.save(commit=False)
            status_update.user = request.user
            status_update.save()

            return redirect("dashboard")


@custom_login_required
@require_http_methods(["GET"])
def userSearchFilter(user_id, user_type, query):
    """
    Function to filter users based on the search query and user type.

    This function filters users based on the provided search query and user type.

    :param user_id: The ID of the user performing the search.
    :type user_id: int
    :param user_type: The type of the user performing the search (student or teacher).
    :type user_type: str
    :param query: The search query entered by the user.
    :type query: str

    :return: The filtered queryset of users.
    :rtype: QuerySet
    """
    if user_type == "student":
        # Fetch only students if the current user is a student
        return (
            User.objects.annotate(
                full_name=Concat("first_name", Value(" "), "last_name")
            )
            .filter(
                Q(username__icontains=query, user_type=User.STUDENT)
                | Q(email__icontains=query, user_type=User.STUDENT)
                | Q(full_name__icontains=query, user_type=User.STUDENT)
            )
            .exclude(id=user_id)
        )
    elif user_type == "teacher":
        # Fetch both students and teachers if the current user is a teacher
        return (
            User.objects.annotate(
                full_name=Concat("first_name", Value(" "), "last_name")
            )
            .filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(full_name__icontains=query)
            )
            .exclude(id=user_id)
        )


class AutocompleteView(View):
    """
    View for handling autocomplete functionality.

    This view fetches users based on the search query entered by the user and returns the matching results
    in HTML format for use in autocomplete suggestions.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param args: Additional positional arguments.
    :type args: tuple
    :param kwargs: Additional keyword arguments.
    :type kwargs: dict

    :return: An HTTP response with HTML containing autocomplete options.
    :rtype: HttpResponse
    """

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to fetch autocomplete options.

        This method retrieves users based on the search query entered by the user and returns the matching results
        in HTML format for use in autocomplete suggestions.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: An HTTP response with HTML containing autocomplete options.
        :rtype: HttpResponse
        """
        query = request.GET.get("q", "")
        logger.info("Search query: %s", query)  # Debugging: Print the search query

        user_type = self.request.user.user_type
        user_id = self.request.user.id

        users = userSearchFilter(user_id, user_type, query)

        print("Users:", users)  # Debugging: Print the queryset

        options_html = render_to_string(
            "partials/autocomplete_options.html", {"users": users}
        )
        print(options_html)
        return HttpResponse(options_html)


class UserHomePage(View):
    """
    View for rendering the user's home page.

    This view renders the home page for a specific user, displaying different content based on whether the user is a student or a teacher.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param args: Additional positional arguments.
    :type args: tuple
    :param kwargs: Additional keyword arguments.
    :type kwargs: dict

    :return: An HTTP response with the rendered home page.
    :rtype: HttpResponse
    """

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        """
        Handler for processing GET requests.

        This method handles GET requests to the user's home page, retrieving necessary data based on the user's role
        and rendering the appropriate template.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: An HTTP response with the rendered home page.
        :rtype: HttpResponse
        """
        username = kwargs["username"]  # Retrieve the username from URL parameters

        if request.user.username == username:
            # Redirect the current user to the dashboard
            return redirect("dashboard")

        user = get_object_or_404(User, username=username)

        if user.user_type == User.STUDENT:
            # Retrieve all enrollments for the student
            enrollments = Enrolment.objects.filter(student=user)
            # Extract the courses from enrollments
            registered_courses = [enrollment.course for enrollment in enrollments]

            # Now you have the list of registered courses for the user
            status_updates = StatusUpdate.objects.filter(user=user).order_by(
                "-created_at"
            )[:5]
            context = {
                "other_user": request.user,
                "user": user,
                "registered_courses": registered_courses,
                "status_updates": status_updates,
            }
            return render(request, "user/student_dashboard.html", context)
        elif user.user_type == User.TEACHER:
            teacher = user
            official_courses = teacher.courses_taught.filter(status="official")

            context = {
                "other_user": request.user,
                "user": teacher,
                "draft_courses": [],
                "official_courses": official_courses,
                "createCourseForm": CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, "user/teacher_dashboard.html", context)


class SearchUsersView(UserPassesTestMixin, ListView):
    """
    View for searching users based on a query.

    This view allows searching for users based on a query string entered by the user.
    The search results are displayed in a paginated list.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param args: Additional positional arguments.
    :type args: tuple
    :param kwargs: Additional keyword arguments.
    :type kwargs: dict

    :return: An HTTP response containing search results.
    :rtype: HttpResponse
    """

    template_name = "user/search_users.html"
    context_object_name = "users"
    paginate_by = 10

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """
        Checks if the current user is authorized to access the view.

        This method verifies whether the current user is either a student or a teacher,
        as only students and teachers are allowed to access this view.

        :return: True if the user is authorized, False otherwise.
        :rtype: bool
        """
        user = self.request.user
        return user.user_type == User.STUDENT or user.user_type == User.TEACHER

    @csrf_exempt
    def get_queryset(self):
        """
        Retrieves the queryset of users based on the search query.

        This method fetches users from the database based on the search query entered
        by the user in the request. The queryset is filtered based on the user type
        and the search query.

        :return: A queryset containing the users matching the search query.
        :rtype: QuerySet
        """
        query = self.request.GET.get("q", "")
        user_type = self.request.user.user_type
        user_id = self.request.user.id

        users = userSearchFilter(user_id, user_type, query)

        return users

    def get_context_data(self, **kwargs):
        """
        Adds additional context data to the view.

        This method adds the search query to the context data dictionary,
        which will be passed to the template for rendering.

        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: The context data dictionary.
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class ProfileView(View):
    """
    View for handling user profile.

    This view allows users to view and update their profile information,
    including the profile picture.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param args: Additional positional arguments.
    :type args: tuple
    :param kwargs: Additional keyword arguments.
    :type kwargs: dict

    :return: An HTTP response with the user profile information or a success/error message.
    :rtype: HttpResponse
    """

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve user profile information.

        This method retrieves the user's profile information and renders the
        profile page with the profile form.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: An HTTP response with the rendered profile page.
        :rtype: HttpResponse
        """
        user = request.user
        return render(
            request,
            "user/profile.html",
            {"user": user, "profileForm": ProfilePictureForm},
        )

    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests to update user profile information.

        This method updates the user's profile information based on the data
        received in the request body.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: An HTTP response with a success or error message.
        :rtype: HttpResponse
        """
        user = request.user
        try:

            # Retrieve data from the request body
            data = json.loads(request.body)
            # Iterate over each key-value pair in the data
            for field_name, field_value in data.items():
                # Check if the field exists in the user model and update it
                if hasattr(request.user, field_name):
                    setattr(request.user, field_name, field_value)
                else:
                    print("failed")
                    return JsonResponse(
                        {"error": f"Invalid field name: {field_name}"}, status=400
                    )

            # Save the user object to persist changes
            user.save()

            # Return success response
            return JsonResponse({"success": "Profile updated successfully"})
        except json.JSONDecodeError:
            # Return error response for invalid JSON data
            print("error: invalid JSON data")
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            # Return error response for unexpected errors
            print("error: ", e)
            return JsonResponse({"error": str(e)}, status=500)


class UploadPictureView(FormView):
    """
    View for uploading a profile picture.

    This view allows users to upload a profile picture by providing a form to select an image file.
    Upon successful upload, the profile picture is associated with the current user.

    :param form_class: The form class used for uploading the profile picture.
    :type form_class: Form
    """

    form_class = ProfilePictureForm

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handles form submission when the form data is valid.

        This method is called when the form data submitted by the user is valid.
        It saves the uploaded file to the user's profile picture field.

        :param form: The form instance containing the uploaded picture.
        :type form: Form

        :return: A response indicating successful form submission.
        :rtype: HttpResponse
        """
        # Get the current user instance
        user = self.request.user
        # Save the uploaded file to the user's photo field
        user.photo = form.cleaned_data["photo"]

        if user.photo:
            process_image.delay(user.photo.path)

        user.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Retrieves the URL to redirect to after successful form submission.

        This method returns the URL to redirect to after successfully uploading the profile picture.

        :return: The URL to redirect to.
        :rtype: str
        """
        return reverse("profile")
