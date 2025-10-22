from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import UserProfile
from forum.models import ForumPost, ForumReply  
from shop.models import Product, Wishlist      
from place.models import Place, Review  


def role_required(roles):
    """Decorator untuk memastikan hanya role tertentu yang bisa akses view."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Akun belum memiliki profil.")
                return redirect('main:show_main')
            if request.user.profile.role not in roles:
                messages.error(request, "Anda tidak memiliki izin untuk mengakses halaman ini.")
                return redirect('main:show_main')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# ========== USER PROFILE MAIN VIEW ==========

@login_required
def profile_view(request):
    """Menampilkan profil dan fitur spesifik sesuai role user."""
    profile = request.user.profile
    role = profile.role

    context = {'profile': profile, 'role': role}

    if role == 'USER':
        return user_dashboard(request, context)
    elif role == 'SELLER':
        return seller_dashboard(request, context)
    elif role == 'FACILITY_ADMIN':
        return facility_admin_dashboard(request, context)
    elif role == 'ADMIN':
        messages.info(request, "Gunakan panel admin untuk mengelola sistem.")
        return redirect('/admin/')
    else:
        messages.warning(request, "Role tidak dikenali.")
        return redirect('main:show_main')


# ========== EDIT PROFILE VIEW ==========

@login_required
def edit_profile(request):
    """User dapat mengubah data diri, tapi tidak bisa mengubah role."""
    profile = request.user.profile

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if phone_number:
            profile.phone_number = phone_number
            profile.save()
            messages.success(request, "Profil berhasil diperbarui.")
            return redirect('user_profile:profile')
    return render(request, 'user_profile/edit_profile.html', {'profile': profile})


# ============================================================
#                  DASHBOARD PER ROLE
# ============================================================

@role_required(['USER'])
def user_dashboard(request, context):
    user = request.user

    # Forum posts & replies oleh user
    posts = ForumPost.objects.filter(author=user)
    replies = ForumReply.objects.filter(author=user)

    # Wishlist products
    wishlist = Wishlist.objects.filter(user=user)

    # Filter kategori
    category = request.GET.get('category')
    if category:
        posts = posts.filter(category__iexact=category)
        replies = replies.filter(post__category__iexact=category)
        wishlist = wishlist.filter(product__category__iexact=category)

    context.update({
        'posts': posts,
        'replies': replies,
        'wishlist': wishlist,
        'filter_category': category,
    })
    return render(request, 'user_profile/user_dashboard.html', context)


@role_required(['SELLER'])
def seller_dashboard(request, context):
    user = request.user

    # Forum posts yang dibuat oleh seller
    posts = ForumPost.objects.filter(author=user)

    # Produk yang dijual oleh seller
    products = Product.objects.filter(seller=user)

    # Filter kategori
    category = request.GET.get('category')
    if category:
        posts = posts.filter(category__iexact=category)
        products = products.filter(category__iexact=category)

    context.update({
        'posts': posts,
        'products': products,
        'filter_category': category,
    })
    return render(request, 'user_profile/seller_dashboard.html', context)


@role_required(['FACILITY_ADMIN'])
def facility_admin_dashboard(request, context):
    user = request.user

    # Tempat (Place) yang dikelola oleh admin ini
    places = Place.objects.filter(admin=user)

    # Review yang diberikan user pada tempat yang ia kelola
    reviews = Review.objects.filter(place__in=places)

    # Filter kategori (swimming, running, cycling)
    category = request.GET.get('category')
    if category:
        places = places.filter(category__iexact=category)
        reviews = reviews.filter(place__category__iexact=category)

    context.update({
        'places': places,
        'reviews': reviews,
        'filter_category': category,
    })
    return render(request, 'user_profile/facility_admin_dashboard.html', context)
