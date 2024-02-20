from datetime import datetime
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.views import PasswordChangeView
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, ListView, FormView
from django.contrib.auth.mixins import UserPassesTestMixin
from .forms import *
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.template.loader import render_to_string
from django.urls import reverse
from .decorators import custom_login_required
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail


class LandingView(TemplateView):
    template_name = "public/landing.html"

    # User.objects.all().delete()
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class LoginView(FormView):
    template_name = "public/login.html"
    form_class = UserLoginForm

    def form_valid(self, form):
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
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            messages.error(self.request, "Invalid username or password.")
            return self.form_invalid(form)


def logout_view(request):
    logout(request)
    return redirect("login")


class RegisterView(FormView):
    template_name = "public/register.html"
    form_class = UserRegistrationForm

    def form_valid(self, form):
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
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PasswordChangeViewCustom(PasswordChangeView):
    template_name = "public/password_change.html"
    success_url = reverse_lazy("password_change_done")


class CoursesView(ListView):
    model = Course
    template_name = "public/view_courses.html"
    context_object_name = "courses"

    @csrf_exempt
    def get_queryset(self):
        # Filter courses with status "official"
        return Course.objects.filter(status="official")


def course_details(request, course_id):
    if request.method == "GET":
        # Retrieve the course object from the database
        course = get_object_or_404(Course, id=course_id)

        # Check if the current user is authenticated and if so, check if they are enrolled in the course
        is_enrolled = False
        if request.user.is_authenticated:
            is_enrolled = Enrollment.is_student_enrolled(request.user, course)

        # Render the course details template with the course object and enrollment status
        return render(
            request,
            "public/course_details.html",
            {"course": course, "is_enrolled": is_enrolled},
        )


def enrolmentEmail(user, course):
    subject = f"Successful Enrolment to {course.name}"
    message = (
        f"Dear {user.get_full_name},\n\n"
        f"Congratulations! You have successfully enrolled in the course '{course.name}'.\n"
        f"We're excited to have you on board and look forward to seeing you excel in the course.\n\n"
        f"Course Details:\n"
        f"Name: {course.name}\n"
        f"Description: {course.description}\n"
        f"Start Date: {course.start_date}\n"
        f"Duration: {course.duration} weeks\n"
        f"Teacher: {course.teacher} - {course.teacher__email}\n\n"
        f"If you have any questions or need assistance, feel free to contact us.\n\n"
        f"Best regards,\nThe Course Management Team"
    )
    from_email = "awdtest04@gmail.com"  # Update with your email
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)


@custom_login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Check if the user is already enrolled in the course
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return JsonResponse(
            {"message": "You are already enrolled in this course."}, status=400
        )

    # Create a new enrollment for the user and course
    Enrollment.objects.create(student=request.user, course=course)

    enrolmentEmail(request.user, course)
    return HttpResponse(
        '<a href="{% url \'official\' course.id %}" class="btn btn-primary">View Course Materials</a>',
        status=201,
    )


class DashboardView(View):
    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.user_type == User.STUDENT:
            # Retrieve all enrollments for the student
            enrollments = Enrollment.objects.filter(student=user)
            # Extract the courses from enrollments
            registered_courses = [enrollment.course for enrollment in enrollments]

            # Now you have the list of registered courses for the user
            status_updates = StatusUpdate.objects.filter(user=user).order_by(
                "-created_at"
            )[:5]
            context = {
                "user": user,
                "registered_courses": registered_courses,
                "status_updates": status_updates,
            }
            return render(request, "user/student_dashboard.html", context)
        elif user.user_type == User.TEACHER:
            teacher = request.user
            draft_courses = teacher.courses_taught.filter(status="draft")
            official_courses = teacher.courses_taught.filter(status="official")

            context = {
                "user": teacher,
                "draft_courses": draft_courses,
                "official_courses": official_courses,
                "createCourseForm": CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, "user/teacher_dashboard.html", context)


class AutocompleteView(View):
    @csrf_exempt
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get("q", "")
        print("Search query:", search_query)  # Debugging: Print the search query

        User = get_user_model()

        if request.user.user_type == "student":
            # Fetch only students if the current user is a student
            users = (
                User.objects.filter(
                    Q(user_type="student")
                    & (
                        Q(username__icontains=search_query)
                        | Q(email__icontains=search_query)
                        | Q(first_name__icontains=search_query)
                        | Q(last_name__icontains=search_query)
                    )
                )
                .exclude(id=request.user.id)
                .distinct()
            )
        else:
            # Fetch both students and teachers if the current user is a teacher
            users = (
                User.objects.filter(
                    (Q(user_type="student") | Q(user_type="teacher"))
                    & (
                        Q(username__icontains=search_query)
                        | Q(email__icontains=search_query)
                        | Q(first_name__icontains=search_query)
                        | Q(last_name__icontains=search_query)
                    )
                )
                .exclude(id=request.user.id)
                .distinct()
            )

        print("Users:", users)  # Debugging: Print the queryset

        options_html = render_to_string(
            "partials/autocomplete_options.html", {"users": users}
        )
        print(options_html)
        return HttpResponse(options_html)


class UserHomePage(View):
    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        username = kwargs["username"]  # Retrieve the username from URL parameters

        if request.user.username == username:
            # Redirect the current user to the dashboard
            return redirect("dashboard")

        user = get_object_or_404(User, username=username)

        if user.user_type == User.STUDENT:
            # Retrieve all enrollments for the student
            enrollments = Enrollment.objects.filter(student=user)
            # Extract the courses from enrollments
            registered_courses = [enrollment.course for enrollment in enrollments]

            # Now you have the list of registered courses for the user
            status_updates = StatusUpdate.objects.filter(user=user).order_by(
                "-created_at"
            )[:5]
            context = {
                "current_user": request.user,
                "user": user,
                "registered_courses": registered_courses,
                "status_updates": status_updates,
            }
            return render(request, "user/student_dashboard.html", context)
        elif user.user_type == User.TEACHER:
            teacher = user
            official_courses = teacher.courses_taught.filter(status="official")

            context = {
                "current_user": request.user,
                "user": teacher,
                "draft_courses": [],
                "official_courses": official_courses,
                "createCourseForm": CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, "user/teacher_dashboard.html", context)


class SearchUsersView(UserPassesTestMixin, ListView):
    template_name = "user/search_users.html"
    context_object_name = "users"
    paginate_by = 10

    def test_func(self):
        user = self.request.user
        return user.user_type == User.STUDENT or user.user_type == User.TEACHER

    @csrf_exempt
    def get_queryset(self):
        query = self.request.GET.get("q", "")
        user_type = self.request.user.user_type
        current_user = self.request.user

        if user_type == User.STUDENT:
            print("reached here")
            users = (
                User.objects.annotate(
                    full_name=Concat("first_name", Value(" "), "last_name")
                )
                .filter(
                    Q(username__icontains=query, user_type=User.STUDENT)
                    | Q(email__icontains=query, user_type=User.STUDENT)
                    | Q(full_name__icontains=query, user_type=User.STUDENT)
                )
                .exclude(id=current_user.id)
            )
        elif user_type == User.TEACHER:
            users = (
                User.objects.annotate(
                    full_name=Concat("first_name", Value(" "), "last_name")
                )
                .filter(
                    Q(username__icontains=query)
                    | Q(email__icontains=query)
                    | Q(full_name__icontains=query)
                )
                .exclude(id=current_user.id)
            )

        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get(
            "q", ""
        )  # Include the query in the context
        return context


class ProfileView(View):
    @method_decorator(custom_login_required)
    def get(self, request, *args, **kwargs):
        user = request.user
        return render(
            request,
            "user/profile.html",
            {"user": user, "profileForm": ProfilePictureForm},
        )

    @method_decorator(custom_login_required)
    def put(self, request, *args, **kwargs):
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
    form_class = ProfilePictureForm

    def form_valid(self, form):
        # Get the current user instance
        user = self.request.user
        # Save the uploaded file to the user's photo field
        user.photo = form.cleaned_data["photo"]
        user.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("profile")


@custom_login_required
def create_course(request):
    if request.method == "POST":
        form = CreateCourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user

            # Check if a course with the same name already exists for the current user
            try:
                existing_course = Course.objects.get(
                    name=course.name, teacher=request.user
                )
                messages.error(request, "Course with the same name already exists.")
                return redirect("dashboard")
            except ObjectDoesNotExist:
                course.save()
                messages.success(request, "Course created successfully.")
                return redirect(reverse("draft", args=[course.id]))
        else:
            print(form.errors)
            messages.error(request, "Failed to create course. Please check the form.")
    return redirect("dashboard")


class DraftCourseView(UserPassesTestMixin, TemplateView):
    template_name = "user/course.html"

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        course_id = self.kwargs.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        # Check if the current user is the teacher of the course
        if self.request.user == course.teacher:
            return True

        return False

    @csrf_exempt
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get("course_id")

        # Fetch the draft course for the current teacher
        course = get_object_or_404(Course, id=course_id, teacher=self.request.user)
        context["course"] = course

        # Generate a range of numbers from 1 to course.duration_weeks
        context["weeks"] = range(1, course.duration_weeks + 1)

        # Fetch materials for the selected week (default to week 1)
        course_materials = CourseMaterial.objects.filter(course=course, week_number=1)
        context["course_materials"] = course_materials
        context["selected_week"] = 1

        context["form"] = CourseForm(instance=course)

        return context

    def post(self, request, *args, **kwargs):
        course_id = self.kwargs.get("course_id")
        course = get_object_or_404(Course, id=course_id, teacher=request.user)

        form = CourseForm(request.POST, instance=course)

        if form.is_valid():
            last_modified_date = datetime.now()
            course = form.save(commit=False)
            course.last_modified = last_modified_date
            course.save()
            messages.success(request, "Course details updated successfully.")

            # Redirect to the same page after successful form submission
            return HttpResponseRedirect(
                reverse("draft", kwargs={"course_id": course_id})
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        # Redirect to the same page after successful form submission
        return HttpResponseRedirect(reverse("draft", kwargs={"course_id": course_id}))


class WeekView(View):
    def post(self, request, *args, **kwargs):
        course_id = kwargs["course_id"]
        course = get_object_or_404(Course, id=course_id)

        # Determine the next week number based on existing weeks
        new_week_number = course.duration_weeks + 1

        # Update the course's duration_weeks
        course.duration_weeks = new_week_number
        course.save()

        # Render the HTML markup for the new week
        new_week_html = render_to_string(
            "partials/week_item.html",
            {"course_id": course_id, "week_number": new_week_number},
            request=request,
        )

        return HttpResponse(new_week_html)

    def delete(self, request, *args, **kwargs):
        course_id = kwargs["course_id"]
        course = get_object_or_404(Course, id=course_id)

        # Determine the next week number based on existing weeks
        new_week_number = course.duration_weeks - 1

        if new_week_number < 1:
            # Ensure the duration_weeks does not go below 1
            messages.error(request, "Weeks can not be lesser than 1")
            error_msg = render_to_string(
                "partials/messages.html",
                {"messages": messages.get_messages(request)},
                request=request,
            )

            return HttpResponse(error_msg, status=400)

        # Update the course's duration_weeks
        course.duration_weeks = new_week_number
        course.save()

        return HttpResponse(status=200)


class OfficialCourseView(UserPassesTestMixin, TemplateView):
    template_name = "user/course.html"

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        course_id = self.kwargs.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        # Check if the current user is the teacher of the course
        if self.request.user == course.teacher:
            return True

        # Check if the current user is enrolled in the course
        if Enrollment.objects.filter(student=self.request.user, course=course).exists():
            return True

        return False

    @csrf_exempt
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get("course_id")

        # Fetch the draft course for the current teacher
        course = get_object_or_404(
            Course,
            id=course_id,
        )
        context["course"] = course

        # Generate a range of numbers from 1 to course.duration_weeks
        context["weeks"] = range(1, course.duration_weeks + 1)

        # Fetch materials for the selected week (default to week 1)
        course_materials = CourseMaterial.objects.filter(course=course, week_number=1)
        context["course_materials"] = course_materials
        context["selected_week"] = 1

        context["form"] = CourseForm(instance=course)

        return context


@custom_login_required
@csrf_exempt
def get_week_materials(request, course_id, week_number):
    print("get_week_materials: ", request.method)
    if request.method == "GET":
        print("redirecting")
        try:
            # Query the database to retrieve materials for the specified week of the course
            course = Course.objects.get(id=course_id)
            course_materials = CourseMaterial.objects.filter(
                course=course, week_number=week_number
            )

        except CourseMaterial.DoesNotExist:
            # Handle the case where no materials are found for the specified week
            return JsonResponse(
                {"error": "No materials found for the specified week"}, status=404
            )
        except Course.DoesNotExist:
            # Handle the case where the specified course does not exist
            return JsonResponse({"error": "Course not found"}, status=404)
        except Exception as e:
            print(e)
            return JsonResponse({"error": "An error occurred"}, status=500)

        print("redirect passed")
        # Instantiate the MaterialUploadForm
        material_upload_form = MaterialUploadForm()

        # Render the materials template with the materials data and the upload form
        return render(
            request,
            "partials/materials.html",
            {
                "course_id": course_id,
                "week_number": week_number,
                "course_materials": course_materials,
                "materialUploadForm": material_upload_form,
                "teacher": course.teacher == request.user,
            },
        )


@custom_login_required
def delete_course_material(request, course_material_id):
    if request.method == "DELETE":
        material = get_object_or_404(CourseMaterial, id=course_material_id)
        material.delete()
        messages.success(request, "Material deleted successfully.")

        # Construct the URL for the get_week_materials view
        redirect_url = reverse(
            "get_week_materials",
            kwargs={
                "course_id": material.course_id,
                "week_number": material.week_number,
            },
        )

        # Return a redirect response with status code 303
        return HttpResponse(status=303, headers={"Location": redirect_url})
    else:
        # Return a method not allowed response
        return HttpResponse(status=405)


@custom_login_required
def upload_material(request, course_id, week_number):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == "POST":
        form = MaterialUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the file to CourseMaterial model
            material = request.FILES["material"]
            course_material = CourseMaterial.objects.create(
                course=course, week_number=week_number, material=material
            )
            messages.success(request, "Material uploaded successfully.")

            # send notification to all students in the course
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return redirect("get_week_materials", course_id=course_id, week_number=week_number)


@custom_login_required
def publish_course(request, course_id):
    # Get the course object
    if request.method == "POST":
        course = get_object_or_404(Course, id=course_id)

        # Implement the logic to publish the course (e.g., update the course status)
        course.status = "official"
        course.save()

        messages.success(request, "Course published successfully")
        return redirect("dashboard")
