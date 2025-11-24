import json
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from user_profile.models import UserProfile # Pastikan import ini ada

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
    """
    Endpoint: POST /auth/login/
    Handles form-encoded data from pbp_django_auth login() method.
    """
    if request.method == 'POST':
        # pbp_django_auth sends form data, not JSON
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return JsonResponse({
                "status": False,
                "message": "Username and password are required."
            }, status=400)

        # --- 1. Cek Username Ada atau Tidak ---
        if not User.objects.filter(username=username).exists():
            return JsonResponse({
                "status": False,
                "message": "Username not found."
            }, status=401)

        # --- 2. Coba Autentikasi (Cek Password) ---
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                # PENTING: auth_login membuat session cookie di server
                auth_login(request, user)
                
                # Get role safely
                try:
                    role = user.profile.role
                except:
                    role = 'USER'
                
                return JsonResponse({
                    "status": True,
                    "message": "Login successful!",
                    "username": user.username,
                    "role": role
                }, status=200)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Account is disabled."
                }, status=401)
        else:
            # Jika user ada tapi authenticate return None, berarti password salah
            return JsonResponse({
                "status": False,
                "message": "Invalid password."
            }, status=401)

    return JsonResponse({"status": False, "message": "Method not allowed."}, status=405)


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