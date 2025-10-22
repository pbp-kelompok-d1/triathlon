from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
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
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    