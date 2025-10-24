from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from .models import ExerciseActivity, User
from .forms import ExerciseActivityForm

CALORY_STANDARDS = {
    'cycling' : 0.04,
    'running' : 0.075,
    'swimming' : 0.555,
}

def is_admin(user):
    return user.profile.role == 'ADMIN'


@login_required(login_url='/login/')
def show_activities(request):
    
    category_filter = request.GET.get("category", None)
    min_s = request.GET.get('distance_min')
    max_s = request.GET.get('distance_max')


    activity = ExerciseActivity.objects.all() if is_admin(request.user) else ExerciseActivity.objects.filter(author=request.user)
    
    if category_filter:
        activity = activity.filter(sport_category=category_filter)

    if min_s is not None and max_s is not None:
        min_m = int(min_s)
        max_m = int(max_s)
        if min_m > max_m:
            min_m, max_m = max_m, min_m
    if min_s is not None:
        min_m = int(min_s)
        activity = activity.filter(distance__gte=min_m)
    if max_s is not None:
        max_m = int(max_s)
        activity = activity.filter(distance__lte=max_m)
    if max_s is None:
        max_m = None
    if min_s is None:
        min_m = None
    
    activity = activity.select_related('author', 'place').order_by('-duration')

    context = {
        'activities': activity,
        'user': request.user,
        'filters': {
            'category': category_filter or '',
            'min': min_m or None,
            'max': max_m or None,
        }
    }
    return render(request, "activities.html", context)

# ======================== AJAX CRUD Functions ========================

# Create a new activity
@require_POST
@login_required(login_url='/login/')
def create_activity_ajax(request):
    form = ExerciseActivityForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    activity = form.save(commit=False)
    activity.author = request.user

    distance_m = int(activity.distance)

    factor = CALORY_STANDARDS.get(activity.sport_category.lower(), 0)
    activity.calories_burned = round(distance_m * factor, 2)

    activity.save()
    return HttpResponse(b"CREATED", status=201)

# Show activity list through AJAX
def show_json(request):
    if is_admin(request.user):
        activityList = ExerciseActivity.objects.all().order_by('-duration')
    else:
        activityList = ExerciseActivity.objects.filter(author=request.user).order_by('-duration')

    data = []
    for act in activityList:
        data.append({
            "id": str(act.id),
            "title": act.title,
            "duration": str(act.duration),
            "distance": act.distance,
            "notes_short": (act.notes[:100] + '...') if act.notes and len(act.notes) > 100 else (act.notes or ''),
            "sport_category": act.sport_category,
            "sport_label": act.get_sport_category_display(),
            "calories_burned": float(act.calories_burned or 0),
            "done_at_iso": act.done_at.strftime("%Y-%m-%d") if act.done_at else "",
            "done_at_display": act.done_at.strftime("%b %d, %Y") if act.done_at else "",
            # Place
            "place_id": act.place_id,
            "place_name": act.place.name if act.place else None,
        })
    return JsonResponse(data, safe=False)

# Edit activity through AJAX
@require_POST
@login_required(login_url='/login/')
def edit_activity_ajax(request, actid):

    activity = get_object_or_404(ExerciseActivity, pk=actid)

    if not (activity.author == request.user or is_admin(request.user)):
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    form = ExerciseActivityForm(request.POST, instance=activity)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    activity = form.save(commit=False)

    distance_m = int(activity.distance)
    factor = CALORY_STANDARDS.get(activity.sport_category.lower(), 0)
    activity.calories_burned = round(distance_m * factor, 2)

    activity.save()
    return HttpResponse(b"UPDATED", status=200)

# Delete activity through AJAX
@login_required(login_url='/login/')
def delete_activity_ajax(request, actid):
    act = get_object_or_404(ExerciseActivity, pk=actid)

    is_admin = getattr(getattr(request.user, "profile", None), "role", "") == "ADMIN"
    
    if not (act.author == request.user or is_admin):
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
    
    act.delete()
    return JsonResponse({'status': 'success', 'message': 'Activity deleted successfully'})

# ======================== Descriptive Statistics Section ========================
@login_required(login_url='/login/')
def stats_json(request):
    ActivityList = ExerciseActivity.objects.all() if is_admin(request.user) else ExerciseActivity.objects.filter(author=request.user)

    # same filters as show_activities
    category = request.GET.get("category")
    if category:
        ActivityList = ActivityList.filter(sport_category=category)

    def to_int(x):
        if x == None:
            return None
        return int(x)

    min_m = to_int(request.GET.get('distance_min'))
    max_m = to_int(request.GET.get('distance_max'))
    if min_m is not None and max_m is not None and min_m > max_m:
        min_m, max_m = max_m, min_m
    if min_m is not None:
        ActivityList = ActivityList.filter(distance__gte=min_m)
    if max_m is not None:
        ActivityList = ActivityList.filter(distance__lte=max_m)

    # aggregates
    cats = ['running','cycling','swimming']
    dist_sum = {c: 0 for c in cats}
    dist_ct  = {c: 0 for c in cats}
    dur_sum  = {c: 0 for c in cats}  
    dur_ct   = {c: 0 for c in cats}

    total_cals = 0.0
    total_secs = 0

    for a in ActivityList:
        c = a.sport_category
        if c in dist_sum:
            dist_sum[c] += int(a.distance or 0)
            dist_ct[c]  += 1
            secs = int(a.duration.total_seconds()) if a.duration else 0
            dur_sum[c]  += secs
            dur_ct[c]   += 1
            total_secs  += secs
        total_cals += float(a.calories_burned or 0)

    avg_distance = {c: (dist_sum[c] // dist_ct[c]) if dist_ct[c] else 0 for c in cats}
    avg_duration_seconds = {c: (dur_sum[c] // dur_ct[c]) if dur_ct[c] else 0 for c in cats}
    avg_cal_per_hour = (total_cals / (total_secs/3600.0)) if total_secs > 0 else 0.0

    return JsonResponse({
        "total_calories": round(total_cals, 2),
        "count_exercises": ActivityList.count(),
        "avg_distance": avg_distance,
        "avg_duration_seconds": avg_duration_seconds,
        "avg_calories_per_hour": round(avg_cal_per_hour, 2),
    }, status=200)

