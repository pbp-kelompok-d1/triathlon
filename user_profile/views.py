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
from django.urls import reverse
from .models import UserProfile
from forum.models import ForumPost, ForumReply
from shop.models import Product, Wishlist
from place.models import Place
from ticket.models import Ticket
from main.views import logout   
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt

# ==========================================================
# DECORATOR (TIDAK BERUBAH)
# ==========================================================
def role_required(roles):
    """Decorator untuk memastikan hanya role tertentu yang bisa akses view."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                messages.error(request, "Anda harus login untuk mengakses halaman ini.")
                return redirect('main:login')
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
        return redirect('user_profile:admin_dashboard')
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
            replies = replies.filter(post_sport_category_icontains=category_filter)
            try:
                wishlist = wishlist.filter(products_category_icontains=category_filter).distinct()
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

        ticket_stats = tickets.aggregate(
        total_quantity=Sum('ticket_quantity'),  # Menjumlahkan semua 'ticket_quantity'
        total_revenue=Sum('total_price')        # Menjumlahkan semua 'total_price'
        )

        total_ticket_quantity = ticket_stats['total_quantity'] or 0
        total_revenue_amount = ticket_stats['total_revenue'] or 0

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
            'tickets': tickets,
            'total_ticket_quantity': total_ticket_quantity,
            'total_revenue_amount': total_revenue_amount,
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
            if 'profile_picture' in request.FILES:
                new_picture = request.FILES['profile_picture']
                
                # Opsional: Hapus foto lama jika ada & bukan default
                if profile.profile_picture and profile.profile_picture.name != 'img/default_profile.png':
                    try:
                        profile.profile_picture.delete(save=False) # Hapus file lama dari storage
                    except Exception as e:
                        print(f"Error deleting old profile pic: {e}")
                
                profile.profile_picture = new_picture
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
                    'profile_picture_url': profile.profile_picture.url
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
    
# ==========================================================
# 5. VIEW BARU: HAPUS AKUN (AJAX)
# ==========================================================
@login_required
def delete_user_account(request):
    """
    Menangani penghapusan akun user via AJAX POST.
    Memerlukan konfirmasi password.
    """
    # Hanya izinkan via AJAX POST
    if request.method != 'POST' or not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    user = request.user
    # Ambil password dari form AJAX
    password_confirm = request.POST.get('password_confirm_delete')

    try:
        # 1. Validasi password
        if not password_confirm:
            raise ValidationError('Password Anda diperlukan untuk konfirmasi penghapusan akun.')
        
        if not user.check_password(password_confirm):
            raise ValidationError('Password yang Anda masukkan salah.')

        # 2. Siapkan URL redirect SEBELUM user dihapus
        # Sesuai permintaan Anda: redirect ke 'main' (guest)
        # Asumsi nama URL-nya adalah 'main:show_main' seperti di decorator Anda
        redirect_url = reverse('main:show_main')
        
        # 3. Hapus user
        # Ini akan otomatis menghapus UserProfile jika menggunakan on_delete=models.CASCADE
        user.delete()
        
        # 4. Logout user dari sesi saat ini
        logout(request)

        # 5. Kirim respon sukses beserta URL redirect
        return JsonResponse({
            'success': True, 
            'message': 'Akun Anda telah berhasil dihapus.',
            'redirect_url': redirect_url  # Kirim URL ini ke JavaScript
        })

    except ValidationError as e:
        # Tangkap error validasi (password salah, dll)
        error_message = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    
    except Exception as e:
        # Tangkap error server lainnya
        return JsonResponse({'success': False, 'error': f'Terjadi kesalahan: {str(e)}'}, status=500)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import UserProfile
from django.http import JsonResponse
from django.db import IntegrityError
from django.views.decorators.http import require_POST
import json


# --- VIEWS HALAMAN UTAMA ---

@login_required
@role_required(['ADMIN'])
def admin_dashboard_view(request):
    """
    Menampilkan halaman utama Admin Dashboard.
    Data tabel akan di-load via AJAX.
    """
    # Kirim role choices ke template untuk mengisi dropdown filter
    role_choices = UserProfile.ROLE_CHOICES
    context = {
        'user_role': request.user.profile.role, # Untuk sidebar
        'role_choices': role_choices
    }
    return render(request, 'user_profile/admin_dashboard.html', context)


# --- AJAX VIEWS (Dipanggil oleh JavaScript) ---

@login_required
@role_required(['ADMIN'])
def get_admin_user_list(request):
    """
    [AJAX GET] Mengambil daftar user (dalam bentuk partial HTML)
    untuk ditampilkan di tabel.
    """
    role_filter = request.GET.get('role', '')
    
    # Ambil semua profile, join dengan user
    users_list = UserProfile.objects.select_related('user').all().order_by('user__username')
    
    if role_filter:
        users_list = users_list.filter(role=role_filter)
        
    context = {
        'users_list': users_list,
        'current_admin_id': request.user.id # Untuk disable tombol delete diri sendiri
    }
    return render(request, 'user_profile/admin_user_list_partial.html', context)


@login_required
@role_required(['ADMIN'])
@require_POST
def admin_update_user_view(request):
    """
    [AJAX POST] Meng-update detail user dari modal edit admin.
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request.'}, status=400)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        user_to_edit = User.objects.get(id=user_id)
        profile_to_edit = user_to_edit.profile

        # Validasi data
        new_username = data.get('username')
        new_email = data.get('email')
        new_role = data.get('role')

        if not all([user_id, new_username, new_email, new_role]):
             return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)

        # Cek duplikat username
        if User.objects.filter(username=new_username).exclude(id=user_id).exists():
            return JsonResponse({'success': False, 'error': 'Username already taken.'}, status=400)
        
        # Cek duplikat email
        if User.objects.filter(email=new_email).exclude(id=user_id).exists():
            return JsonResponse({'success': False, 'error': 'Email already registered.'}, status=400)

        # Update User model
        user_to_edit.username = new_username
        user_to_edit.email = new_email
        user_to_edit.first_name = data.get('first_name', '')
        user_to_edit.last_name = data.get('last_name', '')
        user_to_edit.save()

        # Update UserProfile model
        profile_to_edit.role = new_role
        profile_to_edit.first_name = data.get('first_name', '') # Sinkronkan juga di profile
        profile_to_edit.last_name = data.get('last_name', '')  # Sinkronkan juga di profile
        profile_to_edit.phone_number = data.get('phone_number', '')
        profile_to_edit.bio = data.get('bio', '')
        profile_to_edit.save()

        # Siapkan data untuk dikirim kembali ke JS
        user_data = {
            'id': user_to_edit.id,
            'username': user_to_edit.username,
            'email': user_to_edit.email,
            'first_name': user_to_edit.first_name,
            'last_name': user_to_edit.last_name,
            'role_value': profile_to_edit.role,
            'role_display': profile_to_edit.get_role_display(),
            'phone_number': profile_to_edit.phone_number,
            'bio': profile_to_edit.bio,
            'created_at': profile_to_edit.created_at.strftime('%b %d, %Y'),
        }

        return JsonResponse({'success': True, 'message': f'Successfully updated user @{user_to_edit.username}', 'user_data': user_data})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    except IntegrityError as e:
         return JsonResponse({'success': False, 'error': f'Database error: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)


@login_required
@role_required(['ADMIN'])
@require_POST
def admin_delete_user_view(request):
    """
    [AJAX POST] Menghapus user dari modal delete admin.
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Bad request.'}, status=400)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')

        if not user_id:
            return JsonResponse({'success': False, 'error': 'User ID is required.'}, status=400)

        user_to_delete = User.objects.get(id=user_id)

        # Larang admin menghapus dirinya sendiri
        if user_to_delete.id == request.user.id:
            return JsonResponse({'success': False, 'error': 'You cannot delete your own account from the admin panel.'}, status=403)

        username = user_to_delete.username
        user_to_delete.delete()
        
        return JsonResponse({'success': True, 'message': f'User @{username} has been permanently deleted.'})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)

# ==========================================================
# FUNGSI BARU KHUSUS API UNTUK FLUTTER (MENGEMBALIKAN JSON)
# ==========================================================

def current_user_is_in_roles(user, roles):
    """Fungsi pembantu untuk cek role user."""
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role in roles

def get_current_user_api(request):
    """
    [API VIEW] Mengembalikan data user yang sedang login dalam format JSON untuk Flutter.
    """
    user = request.user
    
    try:
        # Pastikan user punya profile
        if not hasattr(user, 'profile'):
            return JsonResponse({
                'success': False, 
                'error': 'User profile not found'
            }, status=404)
        
        # Serialize data user
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.profile.role,
            'role_display': user.profile.get_role_display(),
            'phone_number': user.profile.phone_number,
            'bio': user.profile.bio,
            'profile_picture_url': user.profile.profile_picture.url if user.profile.profile_picture else None,
            'created_at': user.profile.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def get_author_initial(username):
    """Helper untuk mengambil inisial user."""
    return username[0].upper() if username else "?"

def serialize_post(post, current_user=None):
    """
    Serialisasi ForumPost sesuai Model Flutter 'ForumPost.dart'.
    """
    return {
        'id': str(post.id),
        'title': post.title,
        'content': post.content, # Digunakan untuk list view
        'full_content': post.content, # Digunakan untuk detail view (Flutter: fullContent)
        'category': post.category,
        'category_display': post.get_category_display(),
        'sport_category': post.sport_category,
        'sport_category_display': post.get_sport_category_display(),
        
        # Engagement Metrics
        'post_views': getattr(post, 'post_views', 0),
        'like_count': post.like_count() if hasattr(post, 'like_count') else 0,
        'user_has_liked': post.user_has_liked(current_user) if current_user and hasattr(post, 'user_has_liked') else False,
        
        # Status & Links
        'is_pinned': post.is_pinned,
        'product_id': str(post.product_id) if post.product_id else None,
        'location_id': post.location_id,
        
        # Timestamps
        'created_at': post.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'last_edited': post.last_edited.strftime('%Y-%m-%dT%H:%M:%SZ') if post.last_edited else None,
        
        # Author Info (WAJIB LENGKAP)
        'author': post.author.username if post.author else "Unknown",
        'author_id': post.author.id if post.author else None,
        'author_initial': get_author_initial(post.author.username if post.author else "?"),
        'author_role': post.author.profile.role if post.author and hasattr(post.author, 'profile') else "USER",
    }

def serialize_reply(reply):
    """
    Serialisasi ForumReply sesuai Model Flutter 'ForumReply.dart'.
    FIX: Menambahkan 'total_posts', 'author_role', 'author_initial'.
    """
    author_username = reply.author.username if reply.author else "Unknown"
    
    # Hitung total post author untuk field 'total_posts'
    total_posts = 0
    if reply.author:
        total_posts = ForumPost.objects.filter(author=reply.author).count()

    return {
        'id': str(reply.id),
        'content': reply.content,
        'created_at': reply.created_at.strftime('%b %d, %Y'), # Format sesuai contoh di Dart comment
        
        # Author Info (WAJIB LENGKAP agar tidak error)
        'author': author_username,
        'author_id': reply.author.id if reply.author else None,
        'author_initial': get_author_initial(author_username),
        'author_role': reply.author.profile.role if reply.author and hasattr(reply.author, 'profile') else "USER",
        'total_posts': total_posts, # [CRITICAL FIX] Field ini wajib di ForumReply.dart
        'post_id': str(reply.post.id), 
        'post_sport_category': reply.post.sport_category or "",
        'post_title': reply.post.title or "",
        # Quote Info (Optional)
        'quote_info': {
            'id': str(reply.quote_reply.id),
            'author': reply.quote_reply.author.username if reply.quote_reply.author else "Unknown",
            'content': reply.quote_reply.content[:50] + "..." if len(reply.quote_reply.content) > 50 else reply.quote_reply.content
        } if reply.quote_reply else None
    }

def serialize_product(product):
    """
    Serialisasi Product sesuai Model Flutter 'Product.dart'.
    """
    return {
        'id': str(product.id),
        'seller_username': product.seller.username if product.seller else None,
        'name': product.name or "Unnamed Product",
        'description': product.description or "",
        'price': float(product.price or 0),
        'stock': product.stock,
        'category': product.category or "other",
        'thumbnail': product.thumbnail or "", # Flutter Product.dart pakai 'thumbnail'
    }

# ==========================================================
# 2. VIEW API UTAMA
# ==========================================================

# user_profile/views.py

def get_dashboard_data_api(request):
    """
    [API VIEW] Mengembalikan data dashboard dalam format JSON untuk Flutter.
    HYBRID FIX: Bisa menangani f.image sebagai String (URLField) ATAU File (ImageField).
    """
    user = request.user
    role = getattr(user, 'profile', None).role if hasattr(user, 'profile') else 'USER'
    
    view_filter = request.GET.get('view', 'all')
    category_filter = request.GET.get('category', '')
    
    data = {
        'role': role,
        'view': view_filter,
    }
    
    try:
        if role == 'USER':
            # ... (Bagian USER tidak berubah, silakan copy dari kode sebelumnya) ...
            posts = ForumPost.objects.filter(author=user)
            replies = ForumReply.objects.filter(author=user)
            wishlist_items = Wishlist.objects.filter(user=user)

            if category_filter:
                posts = posts.filter(sport_category__icontains=category_filter)
                replies = replies.filter(post_sport_category_icontains=category_filter)
                wishlist_items = wishlist_items.filter(products_category_icontains=category_filter).distinct()
                
            data['posts'] = [serialize_post(p) for p in posts]
            data['replies'] = [{
                'id': r.id,
                'content_snippet': r.content[:100] + '...' if len(r.content) > 100 else r.content,
                'created_at': r.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'post_title': r.post.title,
                'post_id': r.post.id,
                'post_sport_category': r.post.sport_category,
            } for r in replies]
            
            wishlist_products = []
            for wl in wishlist_items:
                for product in wl.products.all():
                    if not category_filter or (category_filter and category_filter.lower() in product.category.lower()):
                        wishlist_products.append({
                            'id': product.id,
                            'name': product.name,
                            'category': product.category,
                            'price': float(product.price),
                            'thumbnail': product.thumbnail if hasattr(product, 'thumbnail') else '',
                        })
            data['wishlist_products'] = wishlist_products


        elif role == 'SELLER':
            # --- SELLER: Logic Hybrid Image ---
            posts = ForumPost.objects.filter(author=user)
            products = Product.objects.filter(seller=user)

            if category_filter:
                posts = posts.filter(sport_category__icontains=category_filter)
                products = products.filter(category__icontains=category_filter) 
                
            data['posts'] = [serialize_post(p) for p in posts]
            
            product_list = []
            for p in products:
                # HYBRID IMAGE LOGIC FOR PRODUCT
                img_url = None
                if hasattr(p, 'thumbnail') and p.thumbnail:
                    img_url = p.thumbnail # Jika field namanya thumbnail (string)
                elif hasattr(p, 'image'):
                    if p.image:
                        # Cek apakah string atau file
                        if isinstance(p.image, str):
                            img_url = p.image
                        elif hasattr(p.image, 'url'):
                            img_url = p.image.url
                            
                product_list.append({
                    'id': p.id,
                    'name': p.name,
                    'category': p.category,
                    'price': float(p.price),
                    'image_url': img_url,
                })
            data['products'] = product_list
            
            
        elif role == 'FACILITY_ADMIN':
            # --- FACILITY ADMIN: Logic Hybrid Image ---
            facilities = Place.objects.filter(admin=user)
            admin_place_ids = facilities.values_list('id', flat=True)
            tickets_base = Ticket.objects.filter(place_id__in=admin_place_ids)

            ticket_stats = tickets_base.aggregate(
                total_quantity=Sum('ticket_quantity'),
                total_revenue=Sum('total_price')
            )
            data['total_ticket_quantity'] = ticket_stats['total_quantity'] or 0
            data['total_revenue_amount'] = float(ticket_stats['total_revenue'] or 0) 
            
            tickets_filtered = tickets_base
            if category_filter:
                category_map = {
                    'swimming': 'Swimming Pool',
                    'running': 'Running Track',
                    'cycling': 'Bicycle Tracking'
                }
                genre_filter = category_map.get(category_filter)
                
                if genre_filter:
                    facilities = facilities.filter(genre=genre_filter)
                    admin_place_ids = facilities.values_list('id', flat=True)
                    tickets_filtered = tickets_base.filter(place_id__in=admin_place_ids)

            data['facilities'] = []
            for f in facilities:
                # --- HYBRID IMAGE LOGIC (INTI PERUBAHAN) ---
                image_val = None
                if f.image:
                    if hasattr(f.image, 'url'):
                        # Jika f.image adalah File (ImageField) -> ambil .url
                        image_val = f.image.url 
                    else:
                        # Jika f.image adalah String (URLField) -> ambil langsung
                        image_val = str(f.image)

                created_at_val = f.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if f.created_at else None

                data['facilities'].append({
                    'id': f.id,
                    'name': f.name,
                    'genre': f.genre,
                    'city': f.city,
                    'province': f.province,
                    'description': f.description,
                    'price': float(f.price) if getattr(f, 'price', None) else 0.0,
                    'created_at': created_at_val,
                    'image_url': image_val, # Hasil hybrid logic
                })
            
            data['tickets'] = [{
                'id': t.id,
                'customer_name': t.customer_name,
                'place_name': t.place.name,
                'created_at': t.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'booking_date': t.booking_date.strftime('%Y-%m-%d'),
                'ticket_quantity': t.ticket_quantity,
                'total_price': float(t.total_price),
                'status': t.status,
                'status_display': t.get_status_display(),
            } for t in tickets_filtered]
            
        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        print(f"Error in get_dashboard_data_api for role {role}: {e}")
        return JsonResponse({'success': False, 'error': f'Terjadi kesalahan: {str(e)}'}, status=500)
    
@csrf_exempt
def delete_user_account_api(request):
    """
    [API VIEW] Menghapus akun user yang sedang login.
    Support JSON dan Form Data.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)
    
    try:
        # --- PERBAIKAN: Handle JSON dan Form Data ---
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        # --------------------------------------------

        password_confirm = data.get('password_confirm_delete', '')
        user = request.user

        # 1. Validasi password
        if not password_confirm:
            return JsonResponse({'success': False, 'error': 'Password is required for account deletion.'}, status=400)
        
        if not user.check_password(password_confirm):
            return JsonResponse({'success': False, 'error': 'Incorrect password.'}, status=400)

        # 2. Hapus user
        user.delete()
        
        return JsonResponse({'success': True, 'message': 'Your account has been successfully deleted.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)


@csrf_exempt
def change_password_api(request):
    """
    [API VIEW] Mengganti password user yang sedang login.
    Support JSON dan Form Data.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)
    
    try:
        # --- PERBAIKAN: Handle JSON dan Form Data ---
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        # --------------------------------------------

        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        new_password_confirm = data.get('new_password_confirm', '')

        user = request.user

        # 1. Cek password lama
        if not user.check_password(current_password):
            return JsonResponse({'success': False, 'error': 'Your current password was entered incorrectly.'}, status=400)
        
        # 2. Cek password baru
        if not new_password:
            return JsonResponse({'success': False, 'error': 'New password cannot be empty.'}, status=400)
        if new_password != new_password_confirm:
            return JsonResponse({'success': False, 'error': 'New passwords do not match.'}, status=400)
        
        # 3. Validasi kekuatan password
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return JsonResponse({'success': False, 'error': '; '.join(e.messages)}, status=400)

        # 4. Simpan password baru
        user.set_password(new_password)
        user.save()
        
        # 5. Update sesi agar user tidak logout otomatis setelah ganti password
        update_session_auth_hash(request, user)
        
        return JsonResponse({'success': True, 'message': 'Password changed successfully!'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)

@csrf_exempt
def edit_profile_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)
    
    user = request.user
    profile = user.profile

    try:
        # --- PERBAIKAN DI SINI ---
        # Coba baca sebagai JSON dulu, kalau gagal berarti Form Data biasa
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        
        # Ambil data form
        username = data.get('username', user.username).strip()
        email = data.get('email', user.email).strip()
        first_name = data.get('first_name', user.first_name).strip()
        last_name = data.get('last_name', user.last_name).strip()
        phone_number = data.get('phone_number', profile.phone_number or '').strip()
        bio = data.get('bio', profile.bio or '').strip()

        # --- VALIDASI ---
        if not username:
            return JsonResponse({'success': False, 'error': 'Username cannot be empty.'}, status=400)
        # Exclude user sendiri saat cek unik
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            return JsonResponse({'success': False, 'error': 'This username is already taken.'}, status=400)

        if not email:
            return JsonResponse({'success': False, 'error': 'Email cannot be empty.'}, status=400)
        validate_email(email)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            return JsonResponse({'success': False, 'error': 'This email is already in use.'}, status=400)

        # --- PENYIMPANAN ---
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        profile.phone_number = phone_number
        profile.bio = bio
        profile.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Profile updated successfully!',
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': profile.phone_number,
            'bio': profile.bio,
            'profile_picture_url': profile.profile_picture.url if profile.profile_picture else ''
        })
    except ValidationError as e:
        error_message = '; '.join(e.messages) if hasattr(e, 'messages') else str(e)
        return JsonResponse({'success': False, 'error': error_message}, status=400)
    except Exception as e:
        print(f"ERROR: {e}") # Print error di terminal server biar kelihatan
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@csrf_exempt
def get_admin_user_list_api(request):
    """
    [API VIEW] Mengambil daftar semua user beserta detailnya dalam format JSON.
    Support filtering by role via GET parameter.
    """
    # 1. Cek Permission (Harus Login & Harus Admin)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthenticated'}, status=401)
    
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        role_filter = request.GET.get('role', '')
        
        # Ambil semua profile, join dengan user
        users_queryset = UserProfile.objects.select_related('user').all().order_by('user__username')
        
        if role_filter:
            users_queryset = users_queryset.filter(role__iexact=role_filter) # iexact agar case-insensitive

        # Serialize Data
        users_data = []
        for profile in users_queryset:
            users_data.append({
                'user_id': profile.user.id,
                'username': profile.user.username,
                'email': profile.user.email,
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'role': profile.role,
                'role_display': profile.get_role_display(),
                'phone_number': profile.phone_number,
                'bio': profile.bio,
                'profile_picture_url': profile.profile_picture.url if profile.profile_picture else '',
                'date_joined': profile.user.date_joined.strftime('%Y-%m-%d'),
            })

        return JsonResponse({
            'success': True,
            'current_admin_id': request.user.id, # Agar di Flutter tau ID sendiri (biar ga delete diri sendiri)
            'users': users_data
        }, status=200)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def admin_update_user_api(request):
    """
    [API VIEW] Admin meng-update data user lain.
    """
    # 1. Cek Permission
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthenticated'}, status=401)

    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        # Baca Data (Support JSON & Form Data)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        user_id = data.get('user_id')
        
        if not user_id:
             return JsonResponse({'success': False, 'error': 'User ID is required.'}, status=400)

        user_to_edit = User.objects.get(id=user_id)
        profile_to_edit = user_to_edit.profile

        # Ambil Data Baru
        new_username = data.get('username', '').strip()
        new_email = data.get('email', '').strip()
        new_role = data.get('role', '').strip()
        new_first_name = data.get('first_name', '').strip()
        new_last_name = data.get('last_name', '').strip()
        new_phone = data.get('phone_number', '').strip()
        new_bio = data.get('bio', '').strip()

        # Validasi Basic
        if not all([new_username, new_email, new_role]):
             return JsonResponse({'success': False, 'error': 'Username, Email, and Role are required.'}, status=400)

        # Cek Duplikat Username
        if User.objects.filter(username=new_username).exclude(id=user_id).exists():
            return JsonResponse({'success': False, 'error': 'Username already taken.'}, status=400)
        
        # Cek Duplikat Email
        if User.objects.filter(email=new_email).exclude(id=user_id).exists():
            return JsonResponse({'success': False, 'error': 'Email already registered.'}, status=400)

        # Validasi Format Email
        try:
            validate_email(new_email)
        except ValidationError:
            return JsonResponse({'success': False, 'error': 'Invalid email format.'}, status=400)

        # Update User model
        user_to_edit.username = new_username
        user_to_edit.email = new_email
        user_to_edit.first_name = new_first_name
        user_to_edit.last_name = new_last_name
        user_to_edit.save()

        # Update UserProfile model
        profile_to_edit.role = new_role
        profile_to_edit.phone_number = new_phone
        profile_to_edit.bio = new_bio
        profile_to_edit.save()

        return JsonResponse({
            'success': True, 
            'message': f'Successfully updated user {new_username}',
            # Kembalikan data baru jika Flutter perlu update local state
            'updated_data': {
                'username': new_username,
                'email': new_email,
                'role': new_role,
            }
        })

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def admin_delete_user_api(request):
    """
    [API VIEW] Admin menghapus user lain.
    """
    # 1. Cek Permission
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthenticated'}, status=401)

    if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        user_id = data.get('user_id')

        if not user_id:
            return JsonResponse({'success': False, 'error': 'User ID is required.'}, status=400)

        user_to_delete = User.objects.get(id=user_id)

        # Larang admin menghapus dirinya sendiri
        if user_to_delete.id == request.user.id:
            return JsonResponse({'success': False, 'error': 'You cannot delete your own account.'}, status=403)

        username = user_to_delete.username
        user_to_delete.delete()
        
        return JsonResponse({'success': True, 'message': f'User @{username} has been deleted.'})

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)