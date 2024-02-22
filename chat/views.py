from django.shortcuts import redirect, render, get_object_or_404
from chat.models import ChatRoom
from eLearning.models import Enrollment, User, Course
from eLearning.decorators import custom_login_required
from django.contrib import messages

def index(request):
    """
    Render the index page.
    """
    return render(request, "chat/index.html")

@custom_login_required
def room(request, room_name):
    """
    Render the chat room page.
    
    Parameters:
    - request (HttpRequest): The HTTP request object.
    - room_name (str): The name of the chat room.

    Returns:
    - HttpResponse: The rendered chat room page.
    """
    # Retrieve the chat room or return a 404 error if not found
    chat_room = get_object_or_404(ChatRoom, chat_name=room_name)

    # Check if the user is authorized to access the chat room
    is_enrolled_or_teacher = (
        Enrollment.is_student_enrolled(request.user, chat_room.course)
        or chat_room.course.teacher == request.user
    )

    if is_enrolled_or_teacher:
        # Get users in the course (both students and teacher)
        users = User.objects.filter(
            enrollment__course=chat_room.course
        ) | User.objects.filter(pk=chat_room.course.teacher_id)

        # Render the chat room page with required data
        return render(
            request,
            "chat/chat_room.html",
            {
                "chat_room_id": chat_room.id,
                "room_name": room_name,
                "current_user": request.user.username,
                "users": users,
                "messages": chat_room.messages.all(),
            },
        )
    else:
        # Redirect the user to the index page with an error message
        messages.error(request, "You are not authorized to enter the chatroom.")
        return redirect("/")
