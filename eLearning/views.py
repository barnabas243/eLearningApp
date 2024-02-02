from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, ListView, FormView
from .forms import *
from .models import *
from rest_framework import status
from .serializers import UserSerializer

from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from functools import wraps
from django.urls import reverse

def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Add the ?next parameter to redirect back to the original URL after login
            next_url = request.path_info
            login_url = f"{reverse('login')}?next={next_url}"
            messages.error(request, "You need to log in to access this page.")
            return redirect(login_url)  # Redirect to the login page with ?next parameter
        return view_func(request, *args, **kwargs)
    return wrapper

class LandingView(TemplateView):
    template_name = 'public/landing.html'
    
   # User.objects.all().delete()
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(FormView):
    template_name = 'public/login.html'
    form_class = UserLoginForm

    def form_valid(self, form):
        user = form.get_user()
        if user is not None and user.is_active:
            login(self.request, user)
            next_url = self.request.GET.get('next', None)
            if next_url:
                return redirect(next_url)
            else:
                return redirect('dashboard')
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)


def logout_view(request):
    logout(request)
    return redirect('login')


class RegisterView(FormView):
    template_name = 'public/register.html'
    form_class = UserRegistrationForm

    def form_valid(self, form):
        try:
            user = form.save()
            login(self.request, user)
            return redirect('dashboard')
        except Exception as e:
            print(f"An error occurred during registration: {e}")
            messages.error(self.request, "An unexpected error occurred. Please try again later.")
            return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class PasswordChangeViewCustom(PasswordChangeView):
    template_name = 'public/password_change.html'
    success_url = reverse_lazy('password_change_done')


class CoursesView(ListView):
    model = Course
    template_name = 'public/courses.html'
    context_object_name = 'courses'


class DashboardView(View):
    @method_decorator(custom_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.user_type == User.STUDENT:
            registered_courses = user.courses.all()
            status_updates = StatusUpdate.objects.filter(user=user).order_by('-created_at')[:5]
            context = {
                'user': user,
                'registered_courses': registered_courses,
                'status_updates': status_updates,
            }
            return render(request, 'user/student_dashboard.html', context)
        elif user.user_type == User.TEACHER:
            teacher = request.user
            draft_courses = teacher.courses.filter(status='draft')
            official_courses = teacher.courses.filter(status='official')

            context = {
                'user': teacher,
                'draft_courses': draft_courses,
                'official_courses': official_courses,
                'createCourseForm': CreateCourseForm,  # Assuming CourseForm is your form for creating a new course
            }

            return render(request, 'user/teacher_dashboard.html', context)


class ProfileView(View):
    @method_decorator(custom_login_required)
    def get(self, request, *args, **kwargs):
        user = request.user
        return render(request, 'user/profile.html', {'user': user})


class UploadPictureView(FormView):
    form_class = ProfilePictureForm

    def form_valid(self, form):
        # Save the uploaded file
        form.save(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data if needed
        return context

@custom_login_required
def create_course(request):
    if request.method == 'POST':
        form = CreateCourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, 'Course created successfully.')
            return redirect(reverse('draft', args=[course.name]))
        else:
            print(form.errors)
            messages.error(request, 'Failed to create course. Please check the form.')
    return redirect('dashboard')

class DraftCourseView(TemplateView):
    template_name = 'user/draft_course.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_name = self.kwargs.get('course_name')
        
        # Fetch the draft course for the current teacher
        course = get_object_or_404(Course, name=course_name, teacher=self.request.user, status='draft')
        context['course'] = course

        # Generate a range of numbers from 1 to course.duration_weeks
        context['weeks'] = range(1, course.duration_weeks + 1)

        # Fetch materials for the selected week (default to week 1)
        course_materials = CourseMaterial.objects.filter(course=course, week_number=1)
        context['materials'] = course_materials
        context['selected_week'] = 1

        return context

@custom_login_required
def get_week_materials(request):
    if request.method == 'GET':
        # Get parameters from the request URL
        course_name = request.GET.get('course_name')
        week_number = request.GET.get('week_number')

        try:
            # Query the database to retrieve materials for the specified week of the course
            course_materials = CourseMaterial.objects.filter(course__name=course_name, week_number=week_number)
        except CourseMaterial.DoesNotExist:
            # Handle the case where no materials are found for the specified week
            return JsonResponse({'error': 'No materials found for the specified week'}, status=404)
        except Course.DoesNotExist:
            # Handle the case where the specified course does not exist
            return JsonResponse({'error': 'Course not found'}, status=404)

        # Instantiate the MaterialUploadForm
        material_upload_form = MaterialUploadForm()

        # Render the materials template with the materials data and the upload form
        return render(request, 'partials/materials.html', {'selected_week': week_number, 'materials': course_materials, 'materialUploadForm': material_upload_form})

    
@custom_login_required
def upload_material(request):
    if request.method == 'POST':
        form = MaterialUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the file to Material model
            material = Material(file=request.FILES['file'])
            material.save()

            # Create CourseMaterial entry linking material to course and week
            course_name = form.cleaned_data['course']
            week_number = form.cleaned_data['week_number']
            course = Course.objects.get(name=course_name, teacher=request.user)
            course_material = CourseMaterial(course=course, week_number=week_number)
            course_material.save()
            
            # Add the material to the CourseMaterial materials field
            course_material.materials.add(material)

            # Return success JSON response
            return JsonResponse({'success': True})
    
    # Return failure JSON response if form is not valid or method is not POST
    return JsonResponse({'success': False})