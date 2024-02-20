from django.shortcuts import redirect, render, get_object_or_404
from chat.models import ChatRoom
from eLearning.models import Enrollment, User, Course
from eLearning.decorators import custom_login_required
from django.contrib import messages


def index(request):
    return render(request, "chat/index.html")


@custom_login_required
def room(request, room_name):
    # Retrieve the chat room
    chat_room = get_object_or_404(ChatRoom, name=room_name)

    # Check if the user is authorized (either enrolled student or teacher of the course)
    is_enrolled_or_teacher = (
        Enrollment.is_student_enrolled(request.user, chat_room.course)
        or chat_room.course.teacher == request.user
    )

    if is_enrolled_or_teacher:
        # Get users in the course (both students and teacher)
        users = User.objects.filter(
            enrollment__course=chat_room.course
        ) | User.objects.filter(pk=chat_room.course.teacher_id)

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
        messages.error(request, "user is not authorized to enter the chatroom")
        return redirect("/")
