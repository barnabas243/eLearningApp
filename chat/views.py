from django.shortcuts import redirect, render, get_object_or_404
from chat.models import ChatMembership, ChatRoom
from courses.models import Enrolment, User
from elearning_auth.decorators import custom_login_required
from django.contrib import messages
from django.db.models import OuterRef, F, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def get_chat_rooms_for_user(user):
    # Retrieve courses where the user is either enrolled or teaching

    enrolled_course_ids = Enrolment.objects.filter(student=user).values_list(
        "course_id", flat=True
    )
    teaching_course_ids = user.courses_taught.values_list("id", flat=True)

    # Retrieve chat rooms associated with the retrieved courses
    enrolled_chat_rooms = ChatRoom.objects.filter(course_id__in=enrolled_course_ids)
    teaching_chat_rooms = ChatRoom.objects.filter(course_id__in=teaching_course_ids)

    # Combine and return the chat rooms
    return enrolled_chat_rooms | teaching_chat_rooms


@custom_login_required
def index(request):
    """
    Render the index page with a list of chat rooms the student can access.
    """
    # Get the currently logged-in user
    user = request.user

    # Fetch the chat rooms associated with the enrolled courses
    chat_rooms = get_chat_rooms_for_user(user)

    # Pass the chat rooms to the template
    context = {"chat_rooms": chat_rooms}

    # Render the template with the context
    return render(request, "chat/private/index.html", context)


@custom_login_required
def room(request, room_name):
    """
    Render the chat room page.

    :param request: HttpRequest object.
    :type request: HttpRequest
    :param room_name: The name of the chat room.
    :type room_name: str

    :return: HttpResponse object representing the rendered chat room page or a redirection to the index page.
    :rtype: HttpResponse
    """
    # Retrieve the chat room or return a 404 error if not found
    chat_room = get_object_or_404(ChatRoom, chat_name=room_name)
    course = chat_room.course
    # Check if the user is authorized to access the chat room
    is_enrolled_or_teacher = (
        Enrolment.is_student_enrolled(request.user, chat_room.course)
        or chat_room.course.teacher == request.user
    )

    if is_enrolled_or_teacher:
        # Get users in the course (both students and teacher)
        # Filter users
        # Get users enrolled in the course or the course teacher
        users = User.objects.filter(
            enrolment__course=chat_room.course
        ) | User.objects.filter(pk=chat_room.course.teacher_id)

        # Filter ChatMembership queryset based on chat_room_id
        chat_membership_queryset = ChatMembership.objects.filter(
            chat_room_id=chat_room.id
        )

        # Subquery to get the last_active_timestamp for each user
        last_active_subquery = chat_membership_queryset.filter(
            user_id=OuterRef("pk")
        ).values("last_active_timestamp")[
            :1
        ]  # Limit to 1 since each user has only one timestamp per chat room

        # Annotate each user with the last_active_timestamp from ChatMembership
        users_with_last_active = users.annotate(
            last_active_timestamp=Coalesce(
                Subquery(last_active_subquery), F("last_login"), Value(None)
            )
        )

        # Initialize a dictionary to store message blocks

        message_blocks = {}

        for message in chat_room.messages.all():
            # Localize the timestamp to the current timezone
            localized_timestamp = timezone.localtime(message.timestamp)

            # Extract the date component without the time
            message_date = localized_timestamp.date()

            # Check if a message block already exists for the current date
            if message_date in message_blocks:
                message_blocks[message_date]["messages"].append(message)
            else:
                # Create a new message block for the current date
                message_blocks[message_date] = {
                    "date": message_date,
                    "messages": [message],
                }

        # Convert the dictionary to a list of message blocks
        message_blocks = list(message_blocks.values())

        logger.info("message_blocks: %s", message_blocks)
        return render(
            request,
            "chat/private/chat_room.html",
            {
                "chat_room_id": chat_room.id,
                "room_name": room_name,
                "course": course,
                "current_user": request.user.username,
                "users": users_with_last_active,
                "message_blocks": message_blocks,
            },
        )
    else:
        # Redirect the user to the index page with an error message
        messages.error(request, "You are not authorized to enter the chatroom.")
        return redirect("/")
