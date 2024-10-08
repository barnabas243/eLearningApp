from itertools import groupby
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View, ListView
from django.contrib import messages

from chat.models import ChatRoom

from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.template.loader import render_to_string
from elearning_auth.decorators import custom_login_required
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.views.decorators.csrf import csrf_exempt

import logging
from courses.forms import CreateCourseForm

from courses.models import Assignment, AssignmentSubmission, Course, Enrolment, User
from users.forms import StatusUpdateForm, ProfilePictureForm
from users.models import StatusUpdate
from users.serializers import UserUpdateSerializer

logger = logging.getLogger(__name__)


class LandingView(TemplateView):
    """
    Renders the landing page template for unauthenticated users.

    If the user is authenticated, redirects to the Home page.
    """

    template_name = "users/public/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


class HomeView(View):
    """
    View for rendering the Home page.

    This view handles requests to render the Home page for both students and teachers.
    The Home displays registered courses, status updates, course chats, and deadlines for the user.

    Attributes:
        template_student (str): The template file path for the student home.
        template_teacher (str): The template file path for the teacher home.
    """

    template_student = "users/private/student_home.html"
    template_teacher = "users/private/teacher_home.html"

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to render the Home page.

        This method retrieves necessary data based on the user type (student or teacher),
        and renders the corresponding Home template with the context.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.

        :return: The rendered Home page.
        :rtype: HttpResponse
        """

        user = request.user
        status_updates = StatusUpdate.objects.filter(user=user).order_by("-created_at")[
            :5
        ]

        if user.user_type == User.STUDENT:
            # Retrieve all enrollments for the student
            registered_courses = Course.objects.filter(enrolment__student=user)
            # Query ChatRoom objects for registered courses
            course_chats = ChatRoom.objects.filter(course__in=registered_courses)

            # Prefetch AssignmentSubmission objects related to Assignment objects
            deadlines = (
                Assignment.objects.filter(course__in=registered_courses)
                .select_related("course")
                .prefetch_related("submissions")
                .order_by("course")
            )

            # Group assignments by course
            grouped_deadlines = {}

            for assignment in deadlines:
                course = assignment.course
                for submission in assignment.submissions.all():
                    grouped_deadlines.setdefault(course, []).append(
                        {
                            "assignment": assignment,
                            "submitted_at": submission.submitted_at,
                        }
                    )
                if not assignment.submissions.exists():
                    grouped_deadlines.setdefault(course, []).append(
                        {
                            "assignment": assignment,
                            "submitted_at": None,
                        }
                    )

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
            teacher = user
            draft_courses = teacher.courses_taught.filter(status="draft")
            official_courses = teacher.courses_taught.filter(status="official")

            context = {
                "user": teacher,
                "draft_courses": draft_courses,
                "official_courses": official_courses,
                "status_updates": status_updates,
                "statusUpdateForm": StatusUpdateForm,
                "createCourseForm": CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, self.template_teacher, context)

    def post(self, request, *args, **kwargs):
        user = request.user

        try:
            form = StatusUpdateForm(data=request.POST)

            if form.is_valid():
                status_update = form.save(commit=False)
                status_update.user = user
                status_update.save()

                messages.success(request, "Status update posted successfully.")
                return redirect("home")
            else:
                # Form validation failed
                messages.error(request, "Invalid form data. Please check your input.")
                logger.error("Invalid form data submitted: %s", form.errors)
                # Get the referrer URL or default to '/'

                return redirect("home")
        except Exception as e:
            # Unexpected error occurred
            messages.error(
                request, "An error occurred while posting the status update."
            )
            logger.exception("Error occurred while posting status update: %s", str(e))

            return redirect("home")


def userSearchFilter(user_type, query):
    """
    Function to filter users based on the search query and user type.

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
        return User.objects.annotate(
            full_name=Concat("first_name", Value(" "), "last_name")
        ).filter(
            Q(username__icontains=query, user_type=User.STUDENT)
            | Q(email__icontains=query, user_type=User.STUDENT)
            | Q(full_name__icontains=query, user_type=User.STUDENT)
        )
    elif user_type == "teacher":
        # Fetch both students and teachers if the current user is a teacher
        return User.objects.annotate(
            full_name=Concat("first_name", Value(" "), "last_name")
        ).filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(full_name__icontains=query)
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

        user = request.user

        user_type = user.user_type
        user_id = user.id

        users = userSearchFilter(user_type, query)

        print("Users:", users)  # Debugging: Print the queryset

        options_html = render_to_string(
            "users/partials/autocomplete_options.html", {"users": users}
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
        current_user = request.user

        if current_user.username == username:
            # Redirect the current user to the Home
            return redirect("home")

        searched_user = get_object_or_404(User, username=username)

        if searched_user.user_type == User.STUDENT:
            # Retrieve all enrollments for the student
            enrollments = Enrolment.objects.filter(student=searched_user)
            # Extract the courses from enrollments
            registered_courses = [enrollment.course for enrollment in enrollments]

            # Now you have the list of registered courses for the user
            status_updates = StatusUpdate.objects.filter(user=searched_user).order_by(
                "-created_at"
            )[:5]

            context = {
                "other_user": current_user,
                "user": searched_user,
                "registered_courses": registered_courses,
                "status_updates": status_updates,
            }
            return render(request, "users/private/student_home.html", context)
        elif (
            current_user.user_type == User.TEACHER
            and searched_user.user_type == User.TEACHER
        ):
            teacher = searched_user
            official_courses = teacher.courses_taught.filter(status="official")

            # Now you have the list of registered courses for the user
            status_updates = StatusUpdate.objects.filter(user=searched_user).order_by(
                "-created_at"
            )[:5]
            context = {
                "other_user": current_user,
                "user": teacher,
                # "draft_courses": [],
                "official_courses": official_courses,
                "status_updates": status_updates,
                "createCourseForm": CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, "users/private/teacher_home.html", context)

        else:
            messages.error(
                request, "You are not authorized to access this user's homepage."
            )

            redirect_url = request.META.get("HTTP_REFERER", "/")
            return HttpResponseRedirect(redirect_url, status=403)


class SearchUsersView(ListView):
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

    template_name = "users/private/search_users.html"
    context_object_name = "users"
    paginate_by = 10

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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

        user = self.request.user
        user_type = user.user_type
        user_id = user.id

        users = userSearchFilter(user_type, query)

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
            "users/private/profile.html",
            {"user": user, "profileForm": ProfilePictureForm},
        )

    def patch(self, request, *args, **kwargs):
        """
        Handles PATCH requests to update user profile information.

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
            # Get the field name from the data
            field_name = next(iter(data.keys()))

            # Instantiate the serializer with the user object and data
            serializer = UserUpdateSerializer(
                user,
                data=data,
                partial=True,
                fields=[field_name],  # Pass the field name to the serializer
            )

            # Validate and save the user object to persist changes
            if serializer.is_valid():
                serializer.save()
                # Return success response
                return JsonResponse({"success": "Profile updated successfully"})
            else:
                # Return error response with serializer errors
                return JsonResponse(serializer.errors, status=400)

        except json.JSONDecodeError:
            # Log and return error response for invalid JSON data
            logger.error("Invalid JSON data in the request body")
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        except Exception as e:
            # Log and return error response with status code 500 for unexpected errors
            logger.exception("An unexpected error occurred: %s", e)
            return JsonResponse({"error": "An unexpected error occurred"}, status=500)


class UploadPictureView(View):
    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile photo has been updated successfully")

            return redirect("profile")
        else:
            error_message = f"Error(s) in the form: {form.errors.as_text()}"
            messages.error(request, error_message)
            redirect_url = request.META.get("HTTP_REFERER", "/")
            return HttpResponseRedirect(redirect_url, status=400)
