from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import update_session_auth_hash 
from django.core.validators import validate_email
from django.core.exceptions import ValidationError 
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile
from forum.models import ForumPost, ForumReply
from shop.models import Product, Wishlist
from place.models import Place
from ticket.models import Ticket          

# ==========================================================
# DECORATOR (TIDAK BERUBAH)
# ==========================================================
def role_required(roles):
    """Decorator untuk memastikan hanya role tertentu yang bisa akses view."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                messages.error(request, "Anda harus login untuk mengakses halaman ini.")
                return redirect('login')
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Akun belum memiliki profil.")
                return redirect('main:show_main')
            if request.user.profile.role not in roles:
                messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
                return redirect('main:show_main')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# ==========================================================
# 1. VIEW "SHELL" UTAMA (Menggantikan profile_view)
# ==========================================================
@login_required
def dashboard_shell_view(request):
    """
    HANYA me-render "Shell" dashboard.
    AJAX akan mengisi kontennya.
    """
    profile = request.user.profile
    role = profile.role

    # Handle role yang tidak punya dashboard
    if role == 'ADMIN':
        messages.info(request, "Gunakan panel admin untuk mengelola sistem.")
        return redirect('/admin/')
    if role not in ['USER', 'SELLER', 'FACILITY_ADMIN']:
        messages.warning(request, "Role tidak dikenali.")
        return redirect('main:show_main')

    # Tentukan 'initial_view' default per role
    default_views = {
        'USER': 'all',
        'SELLER': 'all',
        'FACILITY_ADMIN': 'all',
    }
    
    # Dapatkan filter awal dari URL untuk diteruskan ke JavaScript
    initial_view = request.GET.get('view', default_views.get(role, 'all'))
    initial_category = request.GET.get('category', '')
    
    context = {
        'initial_view': initial_view,
        'initial_category': initial_category,
        'user_role': role, # Penting untuk logika {% if %} di template shell
    }
    
    # Render SATU template shell untuk SEMUA role
    return render(request, 'user_profile/dashboard_shell.html', context)


# ==========================================================
# 2. VIEW "AJAX" KONTEN (Menggantikan 3 view lama)
# ==========================================================
@login_required
@role_required(['USER', 'SELLER', 'FACILITY_ADMIN']) # Melindungi view ini
def get_dashboard_content(request):
    """
    View ini dipanggil oleh AJAX dan mengembalikan HTML parsial
    berdasarkan role user.
    """
    user = request.user
    role = user.profile.role
    
    # Ambil filter dari parameter GET
    view_filter = request.GET.get('view', 'all')
    category_filter = request.GET.get('category', '') # Ini adalah Kategori Olahraga

    # Context dasar yang dipakai semua role
    context = {
        'view': view_filter,
        'filter_category': category_filter,
        'user': user,
    }
    
    # --- "OTAK" YANG MEMILIH KONTEN BERDASARKAN ROLE ---
    
    if role == 'USER':
        # 1. Ambil data USER
        posts = ForumPost.objects.filter(author=user)
        replies = ForumReply.objects.filter(author=user)
        wishlist = Wishlist.objects.filter(user=user)

        # 2. Terapkan filter
        if category_filter:
            posts = posts.filter(sport_category__icontains=category_filter)
            replies = replies.filter(post__sport_category__icontains=category_filter)
            try:
                wishlist = wishlist.filter(products__category__icontains=category_filter).distinct()
            except Exception: pass # Abaikan jika filter wishlist gagal
            
        # 3. Update context & render parsial USER
        context.update({
            'posts': posts,
            'replies': replies,
            'wishlist': wishlist,
        })
        return render(request, 'user_profile/_user_content.html', context)

    elif role == 'SELLER':
        # 1. Ambil data SELLER
        posts = ForumPost.objects.filter(author=user)
        products = Product.objects.filter(seller=user) # Asumsi field 'seller'

        # 2. Terapkan filter
        if category_filter:
            posts = posts.filter(sport_category__icontains=category_filter)
            # Asumsi model Product juga punya field 'category' untuk olahraga
            products = products.filter(category__icontains=category_filter) 
            
        # 3. Update context & render parsial SELLER
        context.update({
            'posts': posts,
            'products': products,
        })
        return render(request, 'user_profile/_seller_content.html', context)
        
    elif role == 'FACILITY_ADMIN':
        # 1. Ambil data FACILITY_ADMIN
        facilities = Place.objects.filter(admin=user)
        admin_place_ids = facilities.values_list('id', flat=True)
        tickets = Ticket.objects.filter(place_id__in=admin_place_ids)

        # 2. Terapkan filter category
        if category_filter:
            # Map category URL ke genre model
            category_map = {
                'swimming': 'Swimming Pool',
                'running': 'Running Track',
                'cycling': 'Bicycle Tracking'
            }
            
            genre_filter = category_map.get(category_filter)
            
            if genre_filter:
                # Filter facilities berdasarkan genre
                facilities = facilities.filter(genre=genre_filter)
                
                # Update admin_place_ids setelah filter
                admin_place_ids = facilities.values_list('id', flat=True)
                
                # Filter tickets berdasarkan place_id yang sudah difilter
                tickets = tickets.filter(place_id__in=admin_place_ids)

        # 3. Update context & render parsial FACILITY_ADMIN
        context.update({ 
            'facilities': facilities,
            'tickets': tickets
        })
        return render(request, 'user_profile/_facility_admin_content.html', context)

    # Fallback jika role tidak terdefinisi
    return HttpResponse("Role tidak valid atau tidak memiliki dashboard.", status=403)


# ==========================================================
# 3. EDIT PROFILE (AJAX)
# ==========================================================
@login_required
def edit_profile(request):
    """
    Menangani update profile (username, email, nama, bio) via AJAX POST.
    Password diurus oleh view terpisah.
    """
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 1. Ambil data form (TANPA PASSWORD)
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        bio = request.POST.get('bio', '').strip()

        # --- VALIDASI ---
        try:
            # 2. Validasi User (username & email)
            # Ini adalah FIX untuk error kamu: Cek di model 'User', bukan 'UserProfile'
            if not username:
                raise ValidationError('Username cannot be empty.')
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                raise ValidationError('This username is already taken.')

            if not email:
                raise ValidationError('Email cannot be empty.')
            validate_email(email) # Cek format email
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                raise ValidationError('This email is already in use.')

        except ValidationError as e:
            # Tangkap semua error validasi
            error_message = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message}, status=400)
            else:
                messages.error(request, error_message)
                return redirect('user_profile:profile')

        # --- PENYIMPANAN ---
        try:
            # 3. Simpan ke model User
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save() # Simpan perubahan User

            # 4. Simpan ke model UserProfile
            profile.phone_number = phone_number
            profile.bio = bio
            profile.save() # Simpan perubahan Profile
            
            if is_ajax:
                # 5. Kirim kembali data baru via JSON
                return JsonResponse({
                    'success': True, 
                    'message': 'Profile updated successfully!',
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': profile.phone_number,
                    'bio': profile.bio,
                })
            else:
                messages.success(request, "Profil berhasil diperbarui.")
                return redirect('user_profile:profile')

        except Exception as e:
            error_message = f"An error occurred: {e}"
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message}, status=500)
            else:
                messages.error(request, error_message)
                return redirect('user_profile:profile')

    # Jika request BUKAN POST
    return redirect('user_profile:profile')


# ==========================================================
# 4. VIEW BARU: GANTI PASSWORD (AJAX)
# ==========================================================
@login_required
def change_password(request):
    """
    Menangani ganti password via AJAX POST dari modal terpisah.
    """
    if request.method != 'POST' or not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    user = request.user
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    new_password_confirm = request.POST.get('new_password_confirm')

    try:
        # 1. Cek password lama
        if not user.check_password(current_password):
            raise ValidationError('Your current password was entered incorrectly.')
        
        # 2. Cek password baru
        if not new_password:
            raise ValidationError('New password cannot be empty.')
        if new_password != new_password_confirm:
            raise ValidationError('New passwords do not match.')
        
        # 3. Validasi kekuatan password
        validate_password(new_password, user)

        # 4. Simpan password baru
        user.set_password(new_password)
        user.save()
        
        # 5. Update sesi agar user tidak logout
        update_session_auth_hash(request, user)
        
        return JsonResponse({'success': True, 'message': 'Password changed successfully!'})

    except ValidationError as e:
        # Tangkap error validasi (password salah, tidak cocok, terlalu lemah)
        error_message = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    except Exception as e:
        # Tangkap error server lainnya
        return JsonResponse({'success': False, 'error': str(e)}, status=500)