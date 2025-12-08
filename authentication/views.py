import json
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from user_profile.models import UserProfile 
from django.conf import settings # Pastikan import ini ada

@csrf_exempt
def register(request):
    """
    Endpoint: POST /auth/register/
    Handles JSON data from Flutter postJson() method.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get data - support both password/password1 formats
            username = data.get('username', '').strip()
            password1 = data.get('password1') or data.get('password')
            password2 = data.get('password2') or password1
            
            # --- 1. Validasi Input Kosong ---
            if not username or not password1:
                return JsonResponse({
                    "status": "error",
                    "message": "Username and password are required."
                }, status=400)

            # --- 2. Validasi Password Match ---
            if password1 != password2:
                return JsonResponse({
                    "status": "error",
                    "message": "Passwords do not match."
                }, status=400)

            # --- 3. Validasi Uniqueness (Username) ---
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    "status": "error",
                    "message": "Username already exists."
                }, status=400)

            # --- 4. Proses Pembuatan User ---
            user = User.objects.create_user(username=username, password=password1)
            user.save()

            # Try to create/update profile if model exists
            try:
                profile = user.profile
                profile.save()
            except:
                pass

            return JsonResponse({
                "status": "success",
                "message": "Registration successful!",
                "username": user.username
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON."
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "status": "error",
        "message": "Method not allowed."
    }, status=405)


@csrf_exempt
def login(request):
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method not allowed."}, status=405)

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON."}, status=400)
        username = payload.get('username', '').strip()
        password = payload.get('password', '').strip()
    else:
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

    if not username or not password:
        return JsonResponse({"status": False, "message": "Username and password are required."}, status=400)

    if not User.objects.filter(username=username).exists():
        return JsonResponse({"status": False, "message": "Username not found."}, status=401)

    user = authenticate(request, username=username, password=password)
    if not user or not user.is_active:
        return JsonResponse({"status": False, "message": "Invalid credentials."}, status=401)

    auth_login(request, user)

    try:
        role = user.profile.role
    except Exception:
        role = 'USER'

    response = JsonResponse({
        "status": True,
        "message": "Login successful!",
        "username": user.username,
        "role": role,
    })

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=request.session.session_key,
        httponly=True,
        samesite='None',
        secure=False,
    )
    return response


@csrf_exempt
def get_user_data(request):
    """
    Endpoint: GET /api/user/
    Mengambil data user yang sedang login (Session Based).
    """
    if request.method == 'GET':
        user = request.user
        
        # Cek apakah user sedang login (punya session valid)
        if user.is_authenticated:
            try:
                # Handle potensi error jika profile tidak ada
                role = user.profile.role
                phone = user.profile.phone_number
            except:
                role = "USER"
                phone = ""

            return JsonResponse({
                "status": True,
                "username": user.username,
                "email": user.email,
                "role": role,
                "phone_number": phone,
                "is_facility_admin": user.groups.filter(name='Facility Administrator').exists()
            }, status=200)
        else:
            return JsonResponse({
                "status": False,
                "message": "User belum login."
            }, status=401)

    return JsonResponse({"status": False, "message": "Method not allowed."}, status=405)


@csrf_exempt
def logout(request):
    """
    Endpoint: POST /auth/logout/
    Logs out the current user.
    """
    username = request.user.username if request.user.is_authenticated else ""
    
    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logged out successfully!"
        }, status=200)
    except Exception:
        return JsonResponse({
            "status": False,
            "message": "Logout failed."
        }, status=500)
    
# authentication/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def check_admin(request):
    """Check if user is admin/staff"""
    is_admin = (
        request.user.is_superuser or 
        request.user.is_staff or
        request.user.groups.filter(name__iexact='admin').exists()
    )
    
    # Juga check role dari profile jika ada
    try:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN':
            is_admin = True
    except Exception:
        pass
    
    return JsonResponse({
        'is_admin': is_admin,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'username': request.user.username,
    })