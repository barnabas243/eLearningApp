from django.conf import settings
from datetime import datetime
import os
from django.core.files.uploadedfile import InMemoryUploadedFile
import time
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic import TemplateView, View, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from notifications.signals import notify
from courses.tasks import upload_materials
from elearning_auth.decorators import custom_login_required
from users.decorators import (
    check_student_banned,
    student_required,
    teacher_required,
)
from chat.models import ChatRoom
from courses.forms import (
    AssignmentForm,
    AssignmentSubmissionForm,
    CourseForm,
    CreateCourseForm,
    FeedbackForm,
    MaterialUploadForm,
)
from courses.models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseMaterial,
    Enrolment,
    Feedback,
    slugify,
)
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail

import logging

logger = logging.getLogger(__name__)


class CoursesView(ListView):
    """
    View for displaying a list of courses.

    This view retrieves and displays a list of courses with the status "official".

    :ivar model: The model used for retrieving the list of courses.
    :vartype model: Type[django.db.models.Model]
    :ivar template_name: The name of the template used for rendering the list of courses.
    :vartype template_name: str
    :ivar context_object_name: The name of the context variable containing the list of courses
        in the template.
    :vartype context_object_name: str
    """

    model = Course
    template_name = "courses/public/view_courses.html"
    context_object_name = "courses"

    @csrf_exempt
    def get_queryset(self):
        """
        Retrieves the queryset of courses with the status "official".

        This method filters the queryset of courses to include only those with the status
        "official".

        :param self: The view instance.
        :type self: CoursesView

        :return: The queryset of courses with the status "official".
        :rtype: QuerySet[Course]
        """
        return Course.objects.filter(status="official")


@require_http_methods(["GET"])
def course_details(request, course_id):
    """
    View for displaying details of a specific course.

    This view retrieves details of a specific course identified by the provided course ID.
    It checks if the current user is authenticated and if they are enrolled in the course.

    :param request: The HTTP request object.
    :type request: django.http.HttpRequest
    :param course_id: The ID of the course for which details are to be displayed.
    :type course_id: int

    :return: The rendered course details page.
    :rtype: django.http.HttpResponse
    """
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    # Check if the current user is authenticated and if so, check if they are enrolled in the course
    is_enrolled = False
    if user.is_authenticated:
        is_enrolled = Enrolment.is_student_enrolled(user, course)

    # Render the course details template with the course object and enrollment status
    return render(
        request,
        "courses/public/course_details.html",
        {"course": course, "is_enrolled": is_enrolled, "user": user},
    )


@custom_login_required
@student_required
@require_http_methods(["POST"])
def enroll(request, course_id):
    """
    Enroll a user in a course.

    This view handles the enrollment process for a user in a course. It checks if the user is already enrolled,
    and if not, creates a new enrollment for the user in the specified course. It also sends an enrollment email
    to the user upon successful enrollment.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_id: The ID of the course to enroll in.
    :type course_id: int

    :return: An HTTP response with html button or error message.
    :rtype: JsonResponse or HttpResponse
    """

    # Force evaluation of request.user
    user = request.user

    logger.info("request.user type: %s", type(request.user))
    logger.info("request.user value: %s", request.user)
    course = get_object_or_404(Course, id=course_id)

    # Check if the user is already enrolled in the course
    if Enrolment.objects.filter(student=user, course=course).exists():
        return JsonResponse(
            {"message": "You are already enrolled in this course."}, status=400
        )

    # Create a new enrollment for the user and course
    Enrolment.objects.create(student=user, course=course)

    # Send enrollment email to the user
    enrolmentEmail(user, course)

    course_link = (
        f'<a href="{course.get_absolute_url()}" class="disabled-link">{course.name}</a>'
    )
    notify.send(
        course.teacher,
        recipient=user,
        verb=f"You have enrolled into {course_link}.",
    )

    # Construct the HTML with the generated URL
    url = reverse("official", args=[course_id])
    html = f'<a href="{url}" class="btn btn-primary">View Course Materials</a>'

    # Return the HTML in an HttpResponse
    return HttpResponse(html, status=201)


@custom_login_required
@teacher_required
@require_http_methods(["POST"])
def create_course(request):
    """
    Handles the creation of a new course.

    If the request method is POST, attempts to create a new course
    using the data submitted in the form. If successful, redirects to
    the draft page for the newly created course. If a course with the
    same name already exists for the current user, displays an error
    message and redirects to the dashboard.

    :param request: The HTTP request object.
    :type request: HttpRequest

    :return: HttpResponseRedirect object for redirection.
    :rtype: django.http.HttpResponseRedirect
    """
    user = request.user
    form = CreateCourseForm(request.POST)
    if form.is_valid():
        course = form.save(commit=False)
        course.teacher = user

        # Check if a course with the same name already exists for the current user
        try:
            existing_course = Course.objects.get(name=course.name, teacher=user)
            messages.error(request, "Course with the same name already exists.")
            return redirect("dashboard")
        except ObjectDoesNotExist:
            course.save()
            messages.success(request, "Course created successfully.")
            return redirect(reverse("draft", args=[course.id]))
    else:
        logger.error("Error while validating form: %s", form.errors)
        messages.error(request, "Failed to create course. Please check the form.")

    return redirect("dashboard")


class WeekView(View):
    """
    View for managing course weeks.

    This view handles the creation and deletion of weeks for a course.

    """

    @method_decorator(custom_login_required)
    @method_decorator(teacher_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch method with custom login decorator.

        :param request: HttpRequest object representing the request.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: HttpResponse object representing the response.
        :rtype: django.http.HttpResponse
        """
        return super().dispatch(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Handles PATCH requests to create a new week for a course.

        This method creates a new week for the specified course by incrementing the duration_weeks
        attribute of the course. It then renders the HTML markup for the new week.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: An HTTP response containing the HTML markup for the new week.
        :rtype: HttpResponse
        """
        course_id = kwargs["course_id"]
        course = get_object_or_404(Course, id=course_id)

        # Determine the next week number based on existing weeks
        new_week_number = course.duration_weeks + 1

        # Update the course's duration_weeks
        course.duration_weeks = new_week_number
        course.save()

        # Render the HTML markup for the new week
        new_week_html = render_to_string(
            "courses/partials/week_item.html",
            {"course_id": course_id, "week_number": new_week_number},
            request=request,
        )

        return HttpResponse(new_week_html)

    def delete(self, request, *args, **kwargs):
        """
        Handles DELETE requests to delete a week from a course.

        This method deletes the last week of the specified course by decrementing the duration_weeks
        attribute of the course.

        :param request: The HTTP request object.
        :type request: HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        :return: An HTTP response indicating the success or failure of the deletion.
        :rtype: HttpResponse
        """
        course_id = kwargs["course_id"]
        course = get_object_or_404(Course, id=course_id)

        # Determine the next week number based on existing weeks
        new_week_number = course.duration_weeks - 1

        if new_week_number < 1:
            # Ensure the duration_weeks does not go below 1
            messages.error(request, "Weeks can not be lesser than 1")
            error_msg = render_to_string(
                "messages/messages.html",
                {"messages": messages.get_messages(request)},
                request=request,
            )

            return HttpResponse(error_msg, status=400)

        # Update the course's duration_weeks
        course.duration_weeks = new_week_number
        course.save()

        return HttpResponse(status=200)


class OfficialCourseView(UserPassesTestMixin, TemplateView):
    """
    A view to display the course materials for students and teacher.

    """

    template_name = "courses/private/course.html"

    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch method with custom login decorator.

        :param request: HttpRequest object representing the request.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: HttpResponse object representing the response.
        :rtype: django.http.HttpResponse
        """
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        """
        Method to check if the user is authorized to access the course.

        The user must be either the teacher of the course or enrolled in it.
        """
        course_id = self.kwargs.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        # Check if the current user is the teacher of the course
        if self.request.user == course.teacher:
            return True

        # Check if the current user is enrolled in the course
        if Enrolment.objects.filter(student=self.request.user, course=course).exists():
            return True

        return False

    @csrf_exempt
    def get_context_data(self, **kwargs):
        """
        Method to get context data for rendering the template.

        Fetches course information, materials, and form for editing the course.

        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: A dictionary containing context data.
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)

        course_id = self.kwargs.get("course_id")

        user = self.request.user

        # Fetch the draft course for the current teacher
        course = get_object_or_404(Course, id=course_id)
        context["course"] = course

        is_teacher = user == course.teacher
        context["teacher"] = is_teacher
        # Generate a range of numbers from 1 to course.duration_weeks
        context["weeks"] = range(1, course.duration_weeks + 1)
        # Fetch materials for the selected week (default to week 1)
        course_materials = CourseMaterial.objects.filter(course=course, week_number=1)
        context["course_materials"] = course_materials

        context["form"] = CourseForm(instance=course)

        if is_teacher is False:
            feedback_instance = Feedback.objects.filter(
                course_id=course_id, user_id=user
            ).first()

            feedback_form = FeedbackForm(instance=feedback_instance)
            context["feedback_form"] = feedback_form

        context["course_feedbacks"] = Feedback.objects.filter(course_id=course_id)
        context["stars"] = [1, 2, 3, 4, 5]

        return context

    @method_decorator(teacher_required)
    def post(self, request, *args, **kwargs):
        """
        Method to handle POST requests for updating course details.

        Validates the form and updates the course details.

        :param request: HttpRequest object representing the request.
        :type request: django.http.HttpRequest
        :param args: Additional positional arguments.
        :type args: tuple
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict

        :return: HttpResponseRedirect object for redirection.
        :rtype: django.http.HttpResponseRedirect
        """
        course_id = self.kwargs.get("course_id")
        user = request.user
        course = get_object_or_404(Course, id=course_id, teacher=user)

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

        # Redirect to the same page after unsuccessful form submission
        return HttpResponseRedirect(reverse("draft", kwargs={"course_id": course_id}))


@custom_login_required
@check_student_banned
@require_http_methods(["POST"])
def submit_feedback(request, course_id):

    if not Course.objects.filter(id=course_id).exists():
        messages.error(request, "Course doesn't exist.")
        return redirect("dashboard")

    try:
        user = request.user

        logger.info(f"POST data received: {request.POST}")

        mutable_post = request.POST.copy()

        course_ratings = mutable_post.getlist("course_rating")
        teacher_ratings = mutable_post.getlist("teacher_rating")

        if isinstance(course_ratings, list):
            if len(course_ratings) == 1:
                course_rating_sum = int(
                    course_ratings[0]
                )  # Assign the single element as the sum
            else:
                course_rating_sum = sum(int(rating) for rating in course_ratings)
        else:
            course_rating_sum = int(course_ratings)

        # Calculate the sum of ratings for teacher_rating
        if isinstance(teacher_ratings, list):
            if len(teacher_ratings) == 1:
                teacher_rating_sum = int(
                    teacher_ratings[0]
                )  # Assign the single element as the sum
            else:
                teacher_rating_sum = sum(int(rating) for rating in teacher_ratings)
        else:
            teacher_rating_sum = int(
                teacher_ratings
            )  # Handle the case when teacher_ratings is not a list

        # Update the request.POST data with the sums
        feedback_object = {
            "teacher_rating": teacher_rating_sum,
            "course_rating": course_rating_sum,
            "comments": mutable_post["comments"],
        }

        form = FeedbackForm(feedback_object)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            teacher_rating = cleaned_data.get("teacher_rating")
            course_rating = cleaned_data.get("course_rating")
            comments = cleaned_data.get("comments")

            # update the existing feedback instance or create a new one
            feedback, created = Feedback.objects.update_or_create(
                course_id=course_id,
                user_id=user.id,
                defaults={
                    "teacher_rating": teacher_rating,
                    "course_rating": course_rating,
                    "comments": comments,
                },
            )

            # If the feedback was created, send a notification to the teacher
            if created:
                notify.send(
                    sender=user,
                    recipient=feedback.course.teacher,
                    verb=f"A new feedback for {feedback.course.name}",
                )
            messages.success(request, "Submitted a feedback successfully.")
        else:
            # Get the form errors and include them in the error message
            error_message = "Invalid form data."
            for field, errors in form.errors.items():
                error_message += f' {field}: {", ".join(errors)}'
            messages.error(request, error_message)

    except ValueError as e:
        logger.error(f"Error processing feedback: {e}")
        messages.error(request, "Invalid data format. Please provide integer ratings.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")

    return redirect("official", course_id=course_id)


@custom_login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_week_materials(request, course_id, week_number):
    """
    Retrieves materials for a specific week of a course.

    If the request method is GET, retrieves materials and assignments
    for the specified week of the course. Renders the materials template
    with the retrieved data and upload forms.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_id: The ID of the course.
    :type course_id: int
    :param week_number: The week number for which materials are requested.
    :type week_number: int

    :return: An HTTP response with the rendered materials template and data.
    :rtype: HttpResponse
    """
    try:
        course = get_object_or_404(Course, id=course_id)

        user = request.user
        course_materials = CourseMaterial.objects.filter(
            course=course, week_number=week_number
        )

        course_assignments = Assignment.objects.filter(
            course=course, week_number=week_number
        )

        if course_assignments.exists() and user.user_type == "student":
            user_assignments = AssignmentSubmission.objects.filter(
                assignment__in=course_assignments, student=user
            )
        else:
            user_assignments = None

        course_week_date_range = getCourseDateRange(course, week_number)

    except Exception as e:
        logger.error("Unexpected Error occured while getting week materials: %s", e)
        return JsonResponse({"error": "An error occurred"}, status=500)

    initial_data = {"course_id": course_id, "week_number": week_number}
    # Instantiate the MaterialUploadForm
    material_upload_form = MaterialUploadForm(initial=initial_data)
    assignment_upload_form = AssignmentForm(initial=initial_data)
    # Render the materials template with the materials data and the upload form
    return render(
        request,
        "courses/partials/materials.html",
        {
            "course_id": course_id,
            "week_number": week_number,
            "course_materials": course_materials,
            "course_assignments": course_assignments,
            "user_assignments": user_assignments,
            "materialUploadForm": material_upload_form,
            "assignmentForm": assignment_upload_form,
            "teacher": course.teacher == user,
            "course_week_date_range": course_week_date_range,
        },
    )


def getCourseDateRange(course, week_number):
    start_date = course.datetime_from_start_date(week_number).strftime("%d %b")
    end_date = course.datetime_from_start_date(week_number + 1).strftime("%d %b")
    course_week_date_range = f"{start_date} - {end_date}"

    return course_week_date_range


@custom_login_required
@teacher_required
@require_http_methods(["POST"])
def upload_assignment_material(request, course_id, week_number):
    """
    View function to handle the upload of assignment materials for a specific course and week.

    :param request: HttpRequest object representing the request.
    :type request: HttpRequest
    :param course_id: The ID of the course.
    :type course_id: int
    :param week_number: The week number.
    :type week_number: int

    :return: HttpResponseRedirect object redirecting to the 'get_week_materials' view.
    :rtype: HttpResponseRedirect
    """
    try:
        # Create a form instance with the POST data
        logger.info("POST data received: %s", request.POST)

        course = get_object_or_404(Course, pk=course_id)

        # Create a form instance with the POST data and course instance
        form = AssignmentForm(data=request.POST)

        form.course = course
        if form.is_valid():
            logger.info("cleaned form: %s", form.cleaned_data)
            assignment = form.save(commit=False)  # Don't save to the database yet
            assignment.week_number = week_number
            assignment.course_id = course_id  # Set the course_id attribute
            assignment.save()

            messages.success(request, "Assignment material uploaded successfully.")
            logger.info(
                "Assignment material uploaded successfully for course %s, week %s.",
                assignment.course.name,
                assignment.week_number,
            )

            # Retrieve all enrollments for the specified course
            enrollments = Enrolment.objects.filter(course=course)

            # Retrieve the associated students from the enrollments
            students_enrolled = [enrollment.student for enrollment in enrollments]

            course_link = f'<a href="{course.get_absolute_url()}?week={week_number}" disabled>{course.name}</a>'
            deadline = assignment.get_assignment_deadline()  # Format deadline as string
            verb = f"New assignment has been added to {course_link}. Please finish it by {deadline}."

            try:
                # Send notification to all students in the course
                notify.send(sender=request.user, recipient=students_enrolled, verb=verb)
            except Exception as e:
                # Log the exception
                logger.error(f"Error occurred while sending notification: {e}")

        else:
            error_message = "Invalid form data."
            for field, errors in form.errors.items():
                error_message += f' {field}: {", ".join(errors)}'
            messages.error(request, error_message)
            logger.error(
                "Failed to upload assignment material for course %s, week %s.",
                course_id,
                week_number,
            )

    except Exception as e:
        # Log the exception
        logger.exception(
            "An error occurred while uploading assignment material: %s", str(e)
        )
        # Add error message for the user
        messages.error(
            request,
            "An error occurred while processing your request. Please try again later.",
        )

    # Redirect to the 'get_week_materials' view for the specified course and week
    return redirect("get_week_materials", course_id=course_id, week_number=week_number)


@custom_login_required
@check_student_banned
@require_http_methods(["POST"])
def upload_student_submission(request, course_id, assignment_id):
    """
    Handles the submission of an assignment by a student.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param assignment_id: The ID of the assignment.
    :type assignment_id: int

    :return: An HTTP redirect response.
    :rtype: HttpResponseRedirect
    """
    try:
        assignment = Assignment.objects.get(id=assignment_id)
        existing_submission = AssignmentSubmission.objects.filter(
            assignment=assignment, student=request.user
        )
        form = AssignmentSubmissionForm(
            data=request.POST,
            files=request.FILES,
            instance=existing_submission.first(),
        )

        user = request.user

        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = user
            submission.grade = form.cleaned_data.get("grade", None)
            submission.submitted_at = timezone.now()
            submission.save()

            messages.success(request, "Assignment submitted successfully.")
        else:
            error_message = "Failed to submit Assignment. Please check the form."
            error_message += "<br>" + str(form.errors)
            messages.error(request, error_message)
            logger.error(error_message)
    except Assignment.DoesNotExist:
        error_message = "Assignment does not exist."
        messages.error(request, error_message)
        logger.error(error_message)

        return redirect(
            "get_week_materials",
            course_id=course_id,
            week_number=1,
        )
    except Exception as e:
        messages.error(request, e)
        logger.error(e)

    return redirect(
        "get_week_materials",
        course_id=assignment.course.id,
        week_number=assignment.week_number,
    )


@custom_login_required
@teacher_required
@require_http_methods(["DELETE"])
def delete_course_material(request, course_material_id):
    """
    Deletes a course material.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_material_id: The ID of the course material to be deleted.
    :type course_material_id: int

    :return: An HTTP response indicating successful deletion.
    :rtype: HttpResponse
    """
    try:
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
    except Http404:
        messages.error(request, "The material you want to delete does not exist")
        return HttpResponse(
            status=303, headers={"Location": request.META.get("HTTP_REFERER", "/")}
        )


@custom_login_required
@teacher_required
@require_http_methods(["PATCH"])
def student_ban_status_update(request, course_id, student_id):
    """
    Updates the ban status of a student enrolled in a course.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_id: The ID of the course.
    :type course_id: int
    :param student_id: The ID of the student.
    :type student_id: int

    :return: An HTTP response containing HTML content.
    :rtype: HttpResponse
    """
    enrolment = get_object_or_404(Enrolment, course_id=course_id, student_id=student_id)

    # Toggle the is_banned status
    enrolment.is_banned = not enrolment.is_banned
    enrolment.save()

    user = request.user

    if enrolment.is_banned:
        verb = f"You have been banned from {enrolment.course.name}. \n\n Please email {enrolment.course.teacher.email} for clarification "
    else:
        verb = f"You have been unbanned from {enrolment.course.name}. \n\n You may now access the course."

    notify.send(sender=user, recipient=enrolment.student, verb=verb)
    # banStudentEmail(enrolment.student, enrolment.course)
    logger.info(
        f"Ban status for student {student_id} in course {course_id} updated to {enrolment.is_banned}"
    )

    html_content = render_to_string(
        "courses/partials/ban_button.html", {"enrolment": enrolment}
    )

    return HttpResponse(html_content)


@custom_login_required
@teacher_required
@require_http_methods(["POST"])
def upload_material(request, course_id, week_number):
    """
    Handles the upload of materials for a specific course and week.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_id: The ID of the course for which materials are being uploaded.
    :type course_id: int
    :param week_number: The week number for which materials are being uploaded.
    :type week_number: int

    :return: An HTTP redirect response to the 'get_week_materials' view for the specified course and week.
    :rtype: HttpResponseRedirect
    """
    try:
        user = request.user
        # Retrieve the course object or return a 404 error if not found
        course = get_object_or_404(Course, id=course_id, teacher=user)

        form = MaterialUploadForm(request.POST, request.FILES)

        if form.is_valid():

            temporary_paths = []
            for file in request.FILES.getlist("material"):
                # Check if file is InMemoryUploadedFile
                if isinstance(file, InMemoryUploadedFile):

                    # Create a temporary file in the proj dir.
                    temp_file_path = os.path.join(settings.BASE_DIR, "tmp", file.name)

                    # Write the contents of the InMemoryUploadedFile to the temporary file
                    with open(temp_file_path, "wb") as temp_file:
                        temp_file.write(file.read())

                    # Check if the temporary file exists
                    if os.path.exists(temp_file_path):
                        temporary_paths.append(temp_file_path)
                    else:
                        # log the case if the temporary file is not created
                        logger.info(f"Failed to create temporary file for {file.name}")
                else:
                    # skip the case if the file is not an InMemoryUploadedFile
                    pass

            logger.info("temp paths: %s", temporary_paths)

            # Call the Celery task asynchronously
            task = upload_materials.delay(course_id, week_number, temporary_paths)

            # Poll the task result until it's ready
            while not task.ready():
                time.sleep(1)  # Sleep for 1 second before checking again

            logger.info("Materials upload completed.")

            # Retrieve the result once the task is ready
            result = task.result

            # Extract num_of_materials and num_of_failed_uploads from the result
            num_of_materials, num_of_failed_uploads = result

            # add any failed uploads to the error message
            if num_of_failed_uploads:
                error_message = (
                    f"{len(num_of_failed_uploads)} materials failed to upload:\n"
                )

                for failed_material in num_of_failed_uploads:
                    error_message += f"- {failed_material['material_name']}: {failed_material['error_message']}\n"

                messages.error(request, error_message)

            if num_of_materials > 0:
                # Send success message for successful uploads
                success_message = f"{num_of_materials} materials uploaded successfully."
                messages.success(request, success_message)

                # Retrieve the associated students from the enrollments
                enrollments = Enrolment.objects.filter(course=course)
                students_enrolled = [enrollment.student for enrollment in enrollments]

                # Send email notification to all students in the course
                materialsUpdateEmail(
                    students_enrolled, course, week_number, num_of_materials
                )

                # Send django notification to all students in the course
                course_link = f'<a href="{course.get_absolute_url()}?week={week_number}">{course.name}</a>'
                verb = f"<span class='fw-bold'>{num_of_materials} materials</span> added to {course_link}"

                try:
                    notify.send(sender=user, recipient=students_enrolled, verb=verb)
                except Exception as e:
                    logger.error(f"Error occurred while sending notification: {e}")

        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    return redirect("get_week_materials", course_id=course_id, week_number=week_number)


@custom_login_required
@teacher_required
@require_http_methods(["POST"])
def publish_course(request, course_id):
    """
    Publishes a course.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param course_id: The ID of the course to be published.
    :type course_id: int

    :return: An HTTP redirect response to the dashboard.
    :rtype: HttpResponseRedirect
    """
    # Get the course object
    course = get_object_or_404(Course, id=course_id)
    # Check if all necessary fields are not null
    if course.name and course.summary and course.description and course.start_date:
        if course.status == "official":
            messages.error(request, "Course is already published.")
        else:
            course.status = "official"
            course.save()

            messages.success(request, "Course published successfully.")

            chat_name = slugify(course.name)

            # create the chat room for the course
            ChatRoom.objects.create(course=course, chat_name=chat_name)
    else:
        messages.error(
            request,
            "Cannot publish course. All fields (name, summary, description, start_date) are required.",
        )
    return redirect("draft", course_id=course_id)


# ===============================================
# Email Functions
# ===============================================


def enrolmentEmail(user, course):
    """
    Sends an enrollment confirmation email to the user.

    This function sends an email to the provided user to confirm their successful enrollment
    in the specified course. The email contains details about the course such as its name,
    start date, end date, duration, teacher's name and email.

    :param user: The user who has been enrolled in the course.
    :type user: django.contrib.auth.models.User
    :param course: The course in which the user has been enrolled.
    :type course: YourCourseModel
    """
    subject = f"Successful Enrolment to {course.name}"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Congratulations! You have successfully enrolled in the course '{course.name}'.\n"
        f"We're excited to have you on board and look forward to seeing you excel in the course.\n\n"
        f"Course Details:\n"
        f"Name: {course.name}\n"
        f"Start Date: {course.start_date}\n"
        f"End Date: {course.datetime_from_start_date(course.duration_weeks)}\n"
        f"Duration: {course.duration_weeks} weeks\n"
        f"Teacher: {course.teacher.get_full_name()} - {course.teacher.email}\n\n"
        f"If you have any questions or need assistance, feel free to contact us.\n\n"
        f"Best regards,\nThe Course Management Team"
    )
    from_email = "awdtest04@gmail.com"  # Update with your email
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)


def materialsUpdateEmail(students, course, week, num_of_materials):
    """
    Sends an email update about new course materials to the specified students.

    This function sends personalized email updates to each student in the provided list,
    informing them about the addition of new course materials for a specific week in the course.
    Each email contains information about the course, the week, the number of new materials added,
    and instructions on accessing the materials.

    :param students: The list of students to whom the email updates will be sent.
    :type students: list of django.contrib.auth.models.User
    :param course: The course for which the materials update is being sent.
    :type course: YourCourseModel
    :param week: The week number for which the materials update is being sent.
    :type week: int
    :param num_of_materials: The number of new materials added for the specified week.
    :type num_of_materials: int
    """
    subject = f"Materials Update for {course.name}"

    # for loop to send mass emails with personalization
    for student in students:
        greeting = f"Dear {student.get_full_name()},\n\n"

        # Introduction
        intro = (
            "We hope this message finds you well. As part of our ongoing efforts to support your learning experience, "
            "we are pleased to inform you about the latest updates in your course materials.\n\n"
        )

        # Instructions on accessing materials
        instructions = (
            f"{num_of_materials} new course materials {'have' if num_of_materials > 1 else 'has'} been added to week '{week}'.\n"
            f"To access the materials, click on the link below:\n"
            f"https://localhost/official/{course.id}?week={week}.\n\n"
        )

        # Call to action
        call_to_action = (
            "We encourage you to review the new materials at your earliest convenience to stay updated with the course "
            "content.\n\n"
        )

        # Closing statement
        closing = " Best regards,\nThe Course Management Team"

        # Combine all parts of the message
        message = greeting + intro + instructions + call_to_action + closing

        # Sender email address (From address)
        from_email = (
            "awdtest04@gmail.com"  # Update with the desired sender email address
        )

        recipient_list = [student.email]

        send_mail(subject, message, from_email, recipient_list)


# @custom_login_required
# @teacher_required
# def banStudentEmail(student, course):
#     """
#     Sends anban confirmation email to the student

#     This function sends an email to the student to confirm their banned status
#     in the specified course. The email contains details about the course such as its name,
#     start date, end date, duration, teacher's name and email.

#     :param user: The user who has been enrolled in the course.
#     :type user: django.contrib.auth.models.User
#     :param course: The course in which the user has been enrolled.
#     :type course: YourCourseModel
#     """
#     subject = f"[Important] Banned from {course.name}"
#     message = (
#         f"Dear {student.get_full_name()},\n\n"
#         f"You have been banned from the enrolment '{course.name}'.\n"
#         f"If you have any questions, please send an enquiry to us with this email  \n\n"
#         f"Best regards,\nThe Course Management Team"
#     )
#     from_email = "awdtest04@gmail.com"  # Update with your email
#     recipient_list = [student.email]

#     send_mail(subject, message, from_email, recipient_list)
