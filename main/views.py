from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
import datetime
from django.http import JsonResponse


# Create your views here.
def show_main(request):
    # show user info if logged in
    context = {
        'user': request.user,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    return render(request, 'main.html', context)


# REGISTER, LOGIN, AUTHENTICATION

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            
            # Return JSON response for AJAX requests
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'success': True, 'message': 'Registration successful'})
            
            return redirect('main:login')
        else:
            # Return JSON error response for AJAX requests
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    context = {'form':form}
    return render(request, 'register.html', context)

def login_user(request):
   if request.method == 'POST':
      form = AuthenticationForm(data=request.POST)

      if form.is_valid():
        user = form.get_user()
        login(request, user)
        
        # Return JSON response for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': True, 'message': 'Login successful'})
        
        response = HttpResponseRedirect(reverse("main:show_main"))
        response.set_cookie('last_login', str(datetime.datetime.now()))
        return response
      else:
        # Return JSON error response for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

   else:
      form = AuthenticationForm(request)
   context = {'form': form}
   return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response