from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ForumPost, ForumReply
from .forms import ForumPostForm


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
    return render(request, "forums.html", context)

@login_required(login_url='/login/')
def create_forum_post(request):
  
    form = ForumPostForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        post_entry = form.save(commit=False)
        if request.user.is_authenticated:
            post_entry.author = request.user
        post_entry.save()
        return redirect('forum:forums')

    context = {
        'form': form
    }
    return render(request, "create_forum_post.html", context)

@login_required(login_url='/login/')
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

    context = {
        'post': post,
        'replies': replies_with_counts
    }
    return render(request, "forum_thread.html", context)


@csrf_exempt
@require_POST
@login_required(login_url='/login/')
def add_reply(request, post_id):
    """Add reply to forum post"""
    try:
        post = get_object_or_404(ForumPost, pk=post_id)
        content = request.POST.get('content', '')
        
        if not content.strip():
            return JsonResponse({'error': 'Content cannot be empty'}, status=400)
        
        # Create Reply object
        reply = ForumReply.objects.create(
            post=post,
            author=request.user if request.user.is_authenticated else None,
            content=content
        )
        
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
        
        return JsonResponse({
            'success': True,
            'message': 'Reply added successfully',
            'reply_id': str(reply.id),
            'reply_data': {
                'author': request.user.username if request.user.is_authenticated else 'Anonymous',
                'author_initial': request.user.username[0].upper() if request.user.is_authenticated else 'A',
                'author_joined': request.user.date_joined.strftime('%b %Y') if request.user.is_authenticated else '',
                'content': content,
                'created_at': reply.created_at.strftime('%b %d, %Y at %I:%M %p'),
                'reply_number': post.replies.count() + 1,
                'total_posts': total_posts,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# AJAX VIEWS FOR FORUM POSTS ====================================================

def show_json(request):
    """Return all forum posts as JSON"""
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
            'product_id': post.product_id,
            'location_id': post.location_id,
            'created_at': post.created_at.strftime('%b %d, %Y'),
            'author': post.author.username if post.author else 'Anonymous',
            'author_id': post.author.id if post.author else None,
            'author_initial': post.author.username[0].upper() if post.author else 'A',
        }
        for post in post_list
    ]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_POST
@login_required(login_url='/login/')
def add_post_ajax(request):
    """Add new forum post via AJAX"""
    title = request.POST.get("title")
    content = request.POST.get("content")
    category = request.POST.get("category")
    sport_category = request.POST.get("sport_category")
    product_id = request.POST.get("product_id")
    location_id = request.POST.get("location_id")
    user = request.user
    
    # Only allow admins to pin posts
    is_admin = hasattr(user, 'profile') and user.profile.role == 'ADMIN'
    is_pinned = (request.POST.get("is_pinned") == 'on') if is_admin else False

    new_post = ForumPost(
        title=title,
        content=content,
        category=category,
        sport_category=sport_category,
        is_pinned=is_pinned,
        author=user,
        product_id=int(product_id) if product_id else None,
        location_id=int(location_id) if location_id else None,
    )
    new_post.save()
    return HttpResponse(b"CREATED", status=201)


@csrf_exempt
@require_POST
@login_required(login_url='/login/')
def delete_post(request, post_id):
    """Delete forum post - only author or admin can delete"""
    post = get_object_or_404(ForumPost, pk=post_id)
    
    # Check if user is the author or admin
    is_author = post.author == request.user
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
    
    if not (is_author or is_admin):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    post.delete()
    
    # Return JSON response for AJAX requests
    if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Forum post deleted successfully'})
    
    return JsonResponse({'success': True, 'message': 'Forum post deleted successfully'})


@csrf_exempt
@require_POST
@login_required(login_url='/login/')
def edit_post_ajax(request, post_id):
    """Edit forum post via AJAX - only author can edit"""
    post = get_object_or_404(ForumPost, pk=post_id)
    
    # Check if user is the author (ONLY author, not admin)
    if post.author != request.user:
        return JsonResponse({'error': 'Unauthorized - only the author can edit'}, status=403)
    
    # Update post fields
    post.title = request.POST.get("title")
    post.content = request.POST.get("content")
    post.category = request.POST.get("category")
    post.sport_category = request.POST.get("sport_category")
    
    # Only allow admins to pin/unpin posts
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
    if is_admin:
        post.is_pinned = request.POST.get("is_pinned") == 'on'
    # If not admin, don't change the pin status
    
    # Update product_id and location_id
    product_id = request.POST.get("product_id")
    location_id = request.POST.get("location_id")
    post.product_id = int(product_id) if product_id else None
    post.location_id = int(location_id) if location_id else None
    
    # Set last_edited timestamp
    post.last_edited = timezone.now()
    
    post.save()
    
    return HttpResponse(b"UPDATED", status=200)


@csrf_exempt
@require_POST
@login_required(login_url='/login/')
def delete_reply(request, reply_id):
    """Delete forum reply - only author or admin can delete"""
    reply = get_object_or_404(ForumReply, pk=reply_id)
    
    # Check if user is the author or admin
    is_author = reply.author == request.user
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'
    
    if not (is_author or is_admin):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
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
