from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import UserRegistrationForm, UserLoginForm
# from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import StatusUpdate, User, Enrollment,Course

def landing_view(request):
    """
    Render the landing page.

    This view renders the landing page of the eLearning application.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered landing page.
    """
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'public/landing.html', {})

def login_view(request):
    """
    Handle user login.

    This view handles the user login process. 
    
    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The login page with login form or dashboard upon successful login.
    """
    
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        try:
            if form.is_valid():
                form.clean()
                user = form.get_user()
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'The account is disabled')
                else:
                    # Invalid credentials
                    messages.error(request, 'Invalid username or password.')
            else:
                # Form is not valid
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in {field}: {error}")
        except Exception as e:
            # Log the error for debugging purposes
            print(f"An unexpected error occurred: {e}")
            messages.error(request, f"An unexpected error occurred: {e}")
    else:
        form = UserLoginForm()  # Instantiate the login form
    
    return render(request, 'public/login.html', {'form': form})

def logout_view(request):
    """
    Logout the user.

    This view logs out the currently logged-in user.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: Redirects to the login page after logout.
    """
    logout(request)
    return redirect('login')  # Redirect to login page after logout


def register_view(request):
    """
    Handle user registration.

    This view handles the user registration process.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The registration page with registration form or dashboard upon successful registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                print(user)
                login(request, user)
                return redirect('dashboard')  # Redirect to dashboard or any desired page after registration
            except Exception as e:
                # Log the error for debugging purposes
                print(f"An error occurred during registration: {e}")
                messages.error(request, "An unexpected error occurred. Please try again later.")
        else:
            # Handle form validation errors
            
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = UserRegistrationForm()
    return render(request, 'public/register.html', {'form': form})


class password_change_view(PasswordChangeView):
    """
    Handle password change.

    This view handles the password change process.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The password change page.
    """
    template_name = 'public/password_change.html'  # Change this to your actual template name
    success_url = reverse_lazy('password_change_done')  # Change this to your actual success URL name

def courses_view(request):
    """
    Render the courses page.

    This view renders the courses page of the eLearning application.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered courses page.
    """
    courses = Course.objects.all() # Fetch all available courses
    #  courses = Course.objects.all()  # Fetch all available courses
    return render(request, 'public/courses.html', {'courses': courses})


@login_required(login_url="/login")
def dashboard_view(request):
    user = request.user
    if user.user_type == User.STUDENT:
        # Retrieve student-related data from the database
        registered_courses = user.courses.all()  # Assuming a ManyToManyField named 'courses' in the User model
        status_updates = StatusUpdate.objects.filter(user=user).order_by('-created_at')[:5]  # Display latest 5 status updates
        context = {
            'user': user,
            'registered_courses': registered_courses,
            'status_updates': status_updates,
        }
        return render(request, 'private/student_dashboard.html', context)
    elif user.user_type == User.TEACHER:
        # Retrieve teacher-related data from the database
        teacher_courses = Course.objects.filter(teacher=user)  # Assuming ForeignKey relationship with the User model
        context = {
            'user': user,
            'teacher_courses': teacher_courses,
            # Add additional context data for teachers if needed
        }
        return render(request, 'private/teacher_dashboard.html', context)
    else:
        # Handle other user types or scenarios
        return HttpResponse("Unauthorized", status=401)


    
@login_required
def profile_view(request):
    """
    Render the user profile page.

    This view renders the profile page of the logged-in user, displaying their personal information.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The rendered profile page.
    """
    user = request.user
    return render(request, 'private/profile.html', {'user': user})