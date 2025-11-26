import json
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from user_profile.models import UserProfile 

@csrf_exempt
def register(request):
    if request.method != 'POST':
        return JsonResponse({
            "status": False,
            "message": "Method not allowed."
        }, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        phone_number = data.get('phone_number', '')        
        role = data.get('role', 'USER')

        # 1. Input validation
        if not username or not password or not email:
            return JsonResponse({
                "status": False,
                "message": "Username, email, dan password wajib diisi."
            }, status=400)

        # 2. Email format validation
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                "status": False,
                "message": "Format email tidak valid."
            }, status=400)

        # 3. Uniqueness
        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": False, "message": "Username sudah terdaftar."}, status=409)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"status": False, "message": "Email sudah terdaftar."}, status=409)

        # 4. Role validation
        valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
        if role not in valid_roles:
            return JsonResponse({
                "status": False,
                "message": "Role tidak valid."
            }, status=400)

        # 5. Create user
        user = User.objects.create_user(username=username, email=email, password=password)

        # 6. Update auto-created profile
        profile = user.profile
        profile.phone_number = phone_number
        profile.role = role
        profile.save()

        return JsonResponse({
            "status": True,
            "message": "Registrasi berhasil!",
            "username": user.username
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON."}, status=400)

    except Exception as e:

        return JsonResponse({"status": False, "message": str(e)}, status=500)

@csrf_exempt
def login(request):
    """
    Endpoint: POST /api/login/
    """
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')

            # --- 1. Cek Username Ada atau Tidak ---
            # Kita cek manual dulu ke DB untuk pesan error yang spesifik
            if not User.objects.filter(username=username).exists():
                return JsonResponse({
                    "status": False,
                    "message": "Username tidak ditemukan."
                }, status=401)

            # --- 2. Coba Autentikasi (Cek Password) ---
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    # PENTING: auth_login membuat session cookie di server
                    auth_login(request, user)
                    
                    return JsonResponse({
                        "status": True,
                        "message": "Login berhasil!",
                        "username": user.username,
                        "role": user.profile.role
                    }, status=200)
                else:
                    return JsonResponse({
                        "status": False,
                        "message": "Akun dinonaktifkan."
                    }, status=401)
            else:
                # Jika user ada tapi authenticate return None, berarti password salah
                return JsonResponse({
                    "status": False,
                    "message": "Password salah."
                }, status=401)

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON."}, status=400)

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