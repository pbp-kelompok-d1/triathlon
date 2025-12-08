from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import json
import uuid

# ================================ LIKE/UNLIKE POST ================================
@require_POST
@csrf_exempt
def toggle_like(request, post_id):
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required'}, status=401)
    
    post = get_object_or_404(ForumPost, pk=post_id)
    user = request.user
    if post.user_has_liked(user):
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True
    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': post.like_count(),
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ForumPost, ForumReply
from ticket.models import Ticket
from .forms import ForumPostForm
from place.models import Place
from shop.models import Product
import uuid
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from shop.models import Wishlist


# ================================ SHOWING FORUM POSTS AND DETAILS AND JSON DATA ================================

@login_required(login_url='/login/')
def show_forums(request):
    
    filter_type = request.GET.get("filter", "all")
    category_filter = request.GET.get("category", None)

    posts = ForumPost.objects.all()
    
    # Apply filters
    if filter_type == "my" and request.user.is_authenticated:
        posts = posts.filter(author=request.user)
    
    if category_filter:
        posts = posts.filter(sport_category=category_filter)
    
    # ordering by pinned first, then by last activity
    posts = posts.order_by('-is_pinned', '-last_activity')

    context = {
        'posts': posts,
        'user': request.user,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    # Include available places and products for the create-post modal dropdowns
    context['places'] = Place.objects.all()
    context['products'] = Product.objects.all()
    return render(request, "forums.html", context)


def post_detail(request, id):
   
    post = get_object_or_404(ForumPost, pk=id)
    post.increment_views()

    # Get replies from ForumReply model
    replies = post.replies.all().order_by('created_at')
    
    # Calculate post count for each reply author
    replies_with_counts = []
    for reply in replies:
        if reply.author:
            # Count forum posts + replies by this author
            forum_posts_count = ForumPost.objects.filter(author=reply.author).count()
            replies_count = ForumReply.objects.filter(author=reply.author).count()
            total_posts = forum_posts_count + replies_count
            reply.total_posts = total_posts
        else:
            reply.total_posts = 0
        replies_with_counts.append(reply)

    # Calculate total posts for original poster
    if post.author:
        forum_posts_count = ForumPost.objects.filter(author=post.author).count()
        replies_count = ForumReply.objects.filter(author=post.author).count()
        original_poster_total_posts = forum_posts_count + replies_count
    else:
        original_poster_total_posts = 0

    user_has_liked_post = False
    if request.user.is_authenticated:
        user_has_liked_post = post.user_has_liked(request.user)
    # Try to resolve linked Product and Place objects (if any)
    linked_product = None
    linked_place = None
    try:
        if post.product_id:
            linked_product = Product.objects.filter(pk=post.product_id).first()
    except Exception:
        linked_product = None
    try:
        if post.location_id:
            linked_place = Place.objects.filter(pk=post.location_id).first()
    except Exception:
        linked_place = None

    # Check if JSON response is requested (for Flutter app)
    is_json_request = (
        request.GET.get('format') == 'json' or 
        'application/json' in request.headers.get('Accept', '')
    )
    
    if is_json_request:
        # Return JSON response for Flutter
        post_data = {
            'id': str(post.id),
            'title': post.title,
            'content': post.content[:150] + '...' if len(post.content) > 150 else post.content,
            'full_content': post.content,  # Add full_content field
            'category': post.category,
            'category_display': post.get_category_display(),
            'sport_category': post.sport_category,
            'sport_category_display': post.get_sport_category_display(),
            'post_views': post.post_views,
            'is_pinned': post.is_pinned,
            'product_id': str(post.product_id) if post.product_id else None,
            'location_id': post.location_id,
            'created_at': post.created_at.strftime('%b %d, %Y'),
            'author': post.author.username if post.author else 'Anonymous',
            'author_id': post.author.id if post.author else None,
            'author_initial': post.author.username[0].upper() if post.author else 'A',
            'author_role': post.author.profile.role if post.author and hasattr(post.author, 'profile') else 'USER',
            'like_count': post.like_count(),
            'user_has_liked': user_has_liked_post,
            'original_poster_total_posts': original_poster_total_posts,
        }
        
        replies_data = [
            {
                'id': str(reply.id),
                'content': reply.content,
                'created_at': reply.created_at.strftime('%b %d, %Y %I:%M %p'),
                'author': reply.author.username if reply.author else 'Anonymous',
                'author_id': reply.author.id if reply.author else None,
                'author_initial': reply.author.username[0].upper() if reply.author else 'A',
                'author_role': reply.author.profile.role if reply.author and hasattr(reply.author, 'profile') else 'USER',
                'total_posts': reply.total_posts,
                'quote_info': {
                    'id': str(reply.quote_reply.id),
                    'author': reply.quote_reply.author.username if reply.quote_reply.author else 'Anonymous',
                    'content': reply.quote_reply.content[:100] + ('...' if len(reply.quote_reply.content) > 100 else '')
                } if reply.quote_reply else None,
            }
            for reply in replies_with_counts
        ]
        
        return JsonResponse({
            'post': post_data,
            'replies': replies_data,
            'user_has_liked': user_has_liked_post,
        })

    # For web browser HTML view, require login
    if not request.user.is_authenticated:
        return redirect('/login/')

    context = {
        'post': post,
        'replies': replies_with_counts,
        'original_poster_total_posts': original_poster_total_posts,
        'user_has_liked_post': user_has_liked_post,
        'linked_product': linked_product,
        'linked_place': linked_place,
    }
    return render(request, "forum_thread.html", context)

def show_json(request):
    # Return all forum posts as JSON
    post_list = ForumPost.objects.all().order_by('-is_pinned', '-last_activity')
    data = [
        {
            'id': str(post.id),
            'title': post.title,
            'content': post.content[:150] + '...' if len(post.content) > 150 else post.content,
            'full_content': post.content,  # Include full content for editing
            'category': post.category,
            'category_display': post.get_category_display(),
            'sport_category': post.sport_category,
            'sport_category_display': post.get_sport_category_display(),
            'post_views': post.post_views,
            'is_pinned': post.is_pinned,
            'product_id': str(post.product_id) if post.product_id else None,
            'location_id': post.location_id,
            'created_at': post.created_at.strftime('%b %d, %Y'),
            'author': post.author.username if post.author else 'Anonymous',
            'author_id': post.author.id if post.author else None,
            'author_initial': post.author.username[0].upper() if post.author else 'A',
            'author_role': post.author.profile.role if post.author and hasattr(post.author, 'profile') else 'USER',
            'like_count': post.like_count(),
        }
        for post in post_list
    ]
    return JsonResponse(data, safe=False)



# =================================== ADDING FORUMS AND REPLIES ================================

@require_POST
@csrf_exempt
def add_post_ajax(request):
    # Add new forum post via AJAX or JSON (for Flutter)
    
    # Check authentication
    if not request.user.is_authenticated:
        # For JSON requests (Flutter), return JSON error
        if request.content_type == 'application/json':
            return JsonResponse({'status': 'error', 'message': 'Login required'}, status=401)
        # For web requests, redirect to login
        return redirect('/login/')
    
    # Check if JSON body or form data
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            category = data.get('category')
            sport_category = data.get('sport_category')
            product_id = data.get('product_id')
            location_id = data.get('location_id')
            is_pinned_raw = data.get('is_pinned', False)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        # Form data (existing web interface)
        title = request.POST.get("title")
        content = request.POST.get("content")
        category = request.POST.get("category")
        sport_category = request.POST.get("sport_category")
        product_id = request.POST.get("product_id")
        location_id = request.POST.get("location_id")
        is_pinned_raw = request.POST.get("is_pinned") == 'on'
    
    user = request.user
    
    # Only allow admins to pin posts
    is_admin = hasattr(user, 'profile') and user.profile.role == 'ADMIN'
    is_pinned = is_pinned_raw if is_admin else False

    # Convert product/location IDs safely
    def _to_uuid_or_none(val):
        try:
            return uuid.UUID(val) if val else None
        except (ValueError, TypeError, AttributeError):
            return None

    def _to_int_or_none(val):
        try:
            return int(val) if val else None
        except (ValueError, TypeError):
            return None

    new_post = ForumPost(
        title=title,
        content=content,
        category=category,
        sport_category=sport_category,
        is_pinned=is_pinned,
        author=user,
        product_id=_to_uuid_or_none(product_id),
        location_id=_to_int_or_none(location_id),
    )
    new_post.save()
    
    # Return JSON for Flutter, simple response for web
    if request.content_type == 'application/json':
        return JsonResponse({
            'status': 'success',
            'message': 'Post created successfully',
            'post_id': str(new_post.id)
        }, status=201)
    
    return HttpResponse(b"CREATED", status=201)

@require_POST
@csrf_exempt
def add_reply(request, post_id):
    # Add reply to forum post
    
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)
    
    try:
        post = get_object_or_404(ForumPost, pk=post_id)
        content = request.POST.get('content', '')
        quote_reply_id = request.POST.get('quote_reply_id')
        
        if not content.strip():
            return JsonResponse({'error': 'Content cannot be empty'}, status=400)
        
        # Create Reply object
        reply = ForumReply.objects.create(
            post=post,
            author=request.user if request.user.is_authenticated else None,
            content=content
        )

        # If a quote_reply_id was provided, attach the quoted reply (ensure it belongs to same post)
        if quote_reply_id:
            try:
                quoted = ForumReply.objects.get(pk=quote_reply_id)
                if quoted.post_id == post.id:
                    reply.quote_reply = quoted
                    reply.save()
            except ForumReply.DoesNotExist:
                # ignore invalid quote id
                pass
        
        # Update the post's last activity time
        post.last_activity = timezone.now()
        post.save()
        
        # Calculate total posts (forum posts + replies) for this author
        if request.user.is_authenticated:
            forum_posts_count = ForumPost.objects.filter(author=request.user).count()
            replies_count = ForumReply.objects.filter(author=request.user).count()
            total_posts = forum_posts_count + replies_count
        else:
            total_posts = 0
        
        # Prepare quote info for response if present
        quote_info = None
        if reply.quote_reply:
            quote_info = {
                'id': str(reply.quote_reply.id),
                'author': reply.quote_reply.author.username if reply.quote_reply.author else 'Anonymous',
                'content': reply.quote_reply.content,
                'created_at': reply.quote_reply.created_at.strftime('%b %d, %Y at %I:%M %p')
            }

        return JsonResponse({
            'success': True,
            'message': 'Reply added successfully',
            'reply_id': str(reply.id),
            'reply_data': {
                'author': request.user.username if request.user.is_authenticated else 'Anonymous',
                'author_initial': request.user.username[0].upper() if request.user.is_authenticated else 'A',
                'author_joined': request.user.date_joined.strftime('%b %Y') if request.user.is_authenticated else '',
                'author_role': request.user.profile.role if request.user.is_authenticated and hasattr(request.user, 'profile') else None,
                'content': content,
                'created_at': reply.created_at.strftime('%b %d, %Y at %I:%M %p'),
                'reply_number': post.replies.count() + 1,
                'total_posts': total_posts,
                'quote': quote_info,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_exempt
def delete_post(request, post_id):
    """
    Delete forum post - only author or admin can delete.
    Uses @csrf_exempt for Flutter compatibility with manual auth check.
    """
    # Check authentication (manual check for Flutter compatibility)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required'}, status=401)
    
    post = get_object_or_404(ForumPost, pk=post_id)
    
    # Check if user is the author or admin
    is_author = post.author == request.user
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
    
    if not (is_author or is_admin):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    post.delete()
    
    return JsonResponse({'success': True, 'message': 'Forum post deleted successfully'})


@require_POST
@csrf_exempt
def edit_post_ajax(request, post_id):
    """
    Edit forum post via AJAX/Flutter - only author can edit.
    Admins can additionally pin/unpin posts.
    Uses @csrf_exempt for Flutter compatibility with manual auth check.
    """
    # Check authentication (manual check for Flutter compatibility)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required'}, status=401)
    
    post = get_object_or_404(ForumPost, pk=post_id)
    
    # Check if user is the author (ONLY author, not admin)
    if post.author != request.user:
        return JsonResponse({'success': False, 'error': 'Unauthorized - only the author can edit'}, status=403)
    
    # Handle both form data (web) and JSON body (Flutter)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    else:
        data = request.POST
    
    # Update post fields
    post.title = data.get("title", post.title)
    post.content = data.get("content", post.content)
    post.category = data.get("category", post.category)
    post.sport_category = data.get("sport_category", post.sport_category)
    
    # Only allow admins to pin/unpin posts
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
    if is_admin:
        is_pinned_value = data.get("is_pinned")
        if is_pinned_value is not None:
            # Handle both 'on' (web form) and boolean (Flutter JSON)
            post.is_pinned = is_pinned_value == 'on' or is_pinned_value == True
    # If not admin, don't change the pin status
    
    # Update product_id and location_id
    product_id = data.get("product_id")
    location_id = data.get("location_id")
    def _to_uuid_or_none(val):
        try:
            return uuid.UUID(val) if val else None
        except (ValueError, TypeError, AttributeError):
            return None

    def _to_int_or_none(val):
        try:
            return int(val) if val else None
        except (ValueError, TypeError):
            return None

    post.product_id = _to_uuid_or_none(product_id)
    post.location_id = _to_int_or_none(location_id)
    
    # Set last_edited timestamp
    post.last_edited = timezone.now()
    
    post.save()
    
    # Return JSON response for Flutter
    return JsonResponse({
        'success': True,
        'message': 'Post updated successfully',
        'post_id': str(post.id)
    })


@require_POST
@csrf_exempt
def delete_reply(request, reply_id):
    """
    Delete forum reply - only author or admin can delete.
    Uses @csrf_exempt for Flutter compatibility with manual auth check.
    """
    # Check authentication (manual check for Flutter compatibility)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Login required'}, status=401)
    
    reply = get_object_or_404(ForumReply, pk=reply_id)
    
    # Check if user is the author or admin
    is_author = reply.author == request.user
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
    
    if not (is_author or is_admin):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    # Store post info before deleting reply
    post = reply.post
    
    reply.delete()
    
    # Update post's last activity to the most recent reply or post creation
    latest_reply = post.replies.order_by('-created_at').first()
    if latest_reply:
        post.last_activity = latest_reply.created_at
    else:
        post.last_activity = post.created_at
    post.save()
    
    return JsonResponse({'success': True, 'message': 'Reply deleted successfully'})


def user_profile_view(request, username):
    """Public view of a user's profile - reuses user_profile partials for content.
    This view lives in the forum app so clicking a username from a thread can open it.
    
    Supports JSON response for Flutter app when format=json is requested.
    Returns user profile data including:
    - User info (username, role, join date)
    - Posts by this user
    - Replies by this user
    - Stats (total posts, total replies)
    """
    user_obj = get_object_or_404(User, username=username)

    # Read view and category filters from GET params (so public page can filter)
    view = request.GET.get('view', 'all')
    category = request.GET.get('category', '')

    # Gather forum-related data for this user
    posts = ForumPost.objects.filter(author=user_obj).order_by('-created_at')
    replies = ForumReply.objects.filter(author=user_obj).order_by('-created_at')

    # Apply category filter if provided
    if category:
        posts = posts.filter(sport_category__icontains=category)
        replies = replies.filter(post__sport_category__icontains=category)

    # Wishlist may not exist in some projects; attempt to fetch if available
    wishlist = []
    try:
        wishlist = Wishlist.objects.filter(user=user_obj)
    except Exception:
        wishlist = []
    
    # Get user role
    target_user_role = getattr(getattr(user_obj, 'profile', None), 'role', 'USER')
    
    # =========================================================================
    # JSON Response for Flutter App
    # =========================================================================
    # Check if JSON response is requested (for Flutter mobile app)
    is_json_request = (
        request.GET.get('format') == 'json' or 
        'application/json' in request.headers.get('Accept', '')
    )
    
    if is_json_request:
        # Serialize user posts for JSON response
        posts_data = [
            {
                'id': str(post.id),
                'title': post.title,
                'content': post.content[:150] + '...' if len(post.content) > 150 else post.content,
                'category_display': post.get_category_display(),
                'sport_category_display': post.get_sport_category_display(),
                'created_at': post.created_at.strftime('%b %d, %Y'),
                'is_pinned': post.is_pinned,
                'post_views': post.post_views,
                'like_count': post.like_count(),
                'reply_count': post.replies.count(),
            }
            for post in posts
        ]
        
        # Serialize user replies for JSON response
        replies_data = [
            {
                'id': str(reply.id),
                'content': reply.content[:150] + '...' if len(reply.content) > 150 else reply.content,
                'created_at': reply.created_at.strftime('%b %d, %Y'),
                'post_id': str(reply.post.id),
                'post_title': reply.post.title,
            }
            for reply in replies
        ]
        
        # Return comprehensive user profile JSON
        return JsonResponse({
            'user': {
                'username': user_obj.username,
                'initial': user_obj.username[0].upper() if user_obj.username else 'U',
                'role': target_user_role,
                'date_joined': user_obj.date_joined.strftime('%b %d, %Y'),
            },
            'stats': {
                'total_posts': ForumPost.objects.filter(author=user_obj).count(),
                'total_replies': ForumReply.objects.filter(author=user_obj).count(),
            },
            'posts': posts_data,
            'replies': replies_data,
        })

    # =========================================================================
    # HTML Response for Web Browser
    # =========================================================================
    context = {
        'target_user': user_obj,
        'posts': posts,
        'replies': replies,
        'wishlist': wishlist,
        'view': view,
        'initial_category': category,
        'target_user_role': target_user_role,
    }

    return render(request, 'forum/user_profile_public.html', context)


def user_profile_content(request, username):
    """AJAX endpoint to return the appropriate user_profile partial for a public profile.
    Returns the same partial templates used by user_profile.get_dashboard_content so the UI is consistent.
    """
    user_obj = get_object_or_404(User, username=username)
    view = request.GET.get('view', 'all')
    category = request.GET.get('category', '')

    context = {
        'view': view,
        'filter_category': category,
    }

    # USER
    if getattr(getattr(user_obj, 'profile', None), 'role', 'USER') == 'USER':
        posts = ForumPost.objects.filter(author=user_obj)
        replies = ForumReply.objects.filter(author=user_obj)
        wishlist = []
        try:
            wishlist = Wishlist.objects.filter(user=user_obj)
        except Exception:
            wishlist = []

        if category:
            posts = posts.filter(sport_category__icontains=category)
            replies = replies.filter(post__sport_category__icontains=category)

        context.update({'posts': posts, 'replies': replies, 'wishlist': wishlist})
        return render(request, 'user_profile/_user_content.html', context)

    # SELLER
    if getattr(getattr(user_obj, 'profile', None), 'role', 'USER') == 'SELLER':
        posts = ForumPost.objects.filter(author=user_obj)
        products = Product.objects.filter(seller=user_obj) if hasattr(Product, 'seller') else Product.objects.none()

        if category:
            posts = posts.filter(sport_category__icontains=category)
            products = products.filter(category__icontains=category)

        context.update({'posts': posts, 'products': products})
        return render(request, 'user_profile/_seller_content.html', context)

    # FACILITY_ADMIN
    if getattr(getattr(user_obj, 'profile', None), 'role', 'USER') == 'FACILITY_ADMIN':
        facilities = Place.objects.filter(admin=user_obj)
        admin_place_ids = facilities.values_list('id', flat=True)
        tickets = Ticket.objects.filter(place_id__in=admin_place_ids)

        if category:
            # Map category URL to genre if needed (best-effort)
            category_map = {
                'swimming': 'Swimming Pool',
                'running': 'Running Track',
                'cycling': 'Bicycle Tracking'
            }
            genre_filter = category_map.get(category)
            if genre_filter:
                facilities = facilities.filter(genre=genre_filter)
                admin_place_ids = facilities.values_list('id', flat=True)
                tickets = tickets.filter(place_id__in=admin_place_ids)

        ticket_stats = tickets.aggregate(total_quantity=Sum('ticket_quantity'), total_revenue=Sum('total_price'))
        total_ticket_quantity = ticket_stats['total_quantity'] or 0
        total_revenue_amount = ticket_stats['total_revenue'] or 0

        context.update({'facilities': facilities, 'tickets': tickets, 'total_ticket_quantity': total_ticket_quantity, 'total_revenue_amount': total_revenue_amount})
        return render(request, 'user_profile/_facility_admin_content.html', context)

    # Fallback: render user partial
    posts = ForumPost.objects.filter(author=user_obj)
    replies = ForumReply.objects.filter(author=user_obj)
    context.update({'posts': posts, 'replies': replies, 'wishlist': []})
    return render(request, 'user_profile/_user_content.html', context)

