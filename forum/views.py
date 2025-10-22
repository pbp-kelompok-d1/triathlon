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

    context = {
        'post': post,
        'replies': replies
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
            'category': post.category,
            'category_display': post.get_category_display(),
            'sport_category': post.sport_category,
            'sport_category_display': post.get_sport_category_display(),
            'post_views': post.post_views,
            'is_pinned': post.is_pinned,
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
    is_pinned = request.POST.get("is_pinned") == 'on'
    product_id = request.POST.get("product_id")
    location_id = request.POST.get("location_id")
    user = request.user

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
