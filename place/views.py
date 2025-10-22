from django.shortcuts import render, redirect
from .models import Place
from .forms import PlaceForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Review
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import Place
from .forms import PlaceForm  # pastikan kamu punya PlaceForm
from django.contrib.auth.models import Group
from django.db import transaction
from django.core.exceptions import PermissionDenied

@transaction.atomic
def create_facility_admin_group():
    Group.objects.get_or_create(name='Facility Administrator')

def place_list(request):
    places = Place.objects.all()
    is_facility_admin = request.user.groups.filter(name='Facility Administrator').exists()  # misal pakai groups
    return render(request, 'place/place_list.html', {'places': places, 'is_facility_admin': is_facility_admin})


@login_required
def add_place(request):

    if request.method == 'POST':
        form = PlaceForm(request.POST, request.FILES)
        if form.is_valid():
            place = form.save(commit=False)
            place.admin = request.user
            place.save()
            #models si ticket
            return redirect('place:place_list')
    else:
        form = PlaceForm()
    return render(request, 'place/add_place.html', {'form': form})

def place_detail(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    reviews = place.reviews.all().order_by('-created_at')
    is_facility_admin = request.user.groups.filter(name='Facility Administrator').exists()

    return render(request, 'place/place_detail.html', {
        'place': place,
        'reviews': reviews,
        'is_facility_admin': is_facility_admin,
    })

@csrf_exempt
def add_review(request, place_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rating = int(data.get('rating', 5))
            comment = data.get('comment', '')

            review = Review.objects.create(
                place_id=place_id,
                user=request.user,
                rating=rating,
                comment=comment
            )

            return JsonResponse({
                'user': request.user.username,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%d %b %Y')
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def is_facility_admin(user):
    return user.groups.filter(name='Facility Administrator').exists()

@user_passes_test(is_facility_admin)
def edit_place(request, place_id):
    print("user is admin")
    place = get_object_or_404(Place, id=place_id)
    if request.method == 'POST':
        form = PlaceForm(request.POST, request.FILES, instance=place)
        if form.is_valid():
            form.save()
            return redirect('place_detail', place_id=place.id)
    else:
        form = PlaceForm(instance=place)
    return render(request, 'place/edit_place.html', {'form': form, 'place': place})

