from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm
from django.contrib.auth.models import Group
import datetime



@login_required(login_url='/login/')
def show_home(request):
    context = {
        'user': request.user,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    return render(request, 'home.html', context)

def show_main(request):
    # show user info if logged in
    context = {
        'user': request.user,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    return render(request, 'main.html', context)


def register(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Check if Facility Administrator group exists, if not create it
            facility_admin_group, created = Group.objects.get_or_create(name='Facility Administrator')
            
            # Add user to Facility Administrator group
            if 'is_facility_admin' in request.POST:
                user.groups.add(facility_admin_group)
            
            messages.success(request, 'Your account has been successfully created!')
            
            # Return JSON response for AJAX requests
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'success': True, 'message': 'Registration successful'})
            
            return redirect('main:login')
        else:
            # Return JSON error response for AJAX requests
            if request.headers.get('Accept') == 'application/json':
                errors_dict = {field: [str(error) for error in errors] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors_dict}, status=400)
            
    context = {'form':form}
    return render(request, 'register.html', context)

@ensure_csrf_cookie
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response
        else:
            messages.info(request, 'Sorry, incorrect username or password. Please try again.')
    
    context = {}
    return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Make sure this is present
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CSRF settings
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Required for AJAX requests
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']  # Add your domain in production
