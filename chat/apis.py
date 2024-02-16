from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

class ChatRoomView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'chat_room.html'

    def get(self, request, room_name):
        return Response({'room_name': room_name})

