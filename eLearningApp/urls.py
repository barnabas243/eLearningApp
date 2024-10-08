"""
URL configuration for eLearningApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ckeditor_uploader.views import upload
from django.views.generic import RedirectView
from elearning_auth.decorators import custom_login_required

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("courses.urls")),
    path("", include("users.urls")),
    path("auth/", include("elearning_auth.urls")),
    path(
        "chat/", include("chat.urls")
    ),  # Include the chat app's URLs under the 'chat/' path
    path("ckeditor/upload/", custom_login_required(upload), name="ckeditor_upload"),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("docs/", RedirectView.as_view(url="/docs/index.html", permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static("/docs/", document_root=settings.BASE_DIR / "static/docs/build")
