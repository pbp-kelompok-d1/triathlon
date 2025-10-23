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
from .forms import PlaceForm 
from django.contrib.auth.models import Group
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.db.models import Avg

@transaction.atomic
def create_facility_admin_group():
    Group.objects.get_or_create(name='Facility Administrator')

   # views.py

def place_list(request):
    genres_list = ["Swimming Pool", "Running Track", "Bicycle Tracking"]
    
    selected_genre = request.GET.get('genre')
    search_query = request.GET.get('q')
    filter_type = request.GET.get('filter')

    # --- PERBAIKAN DI SINI ---
    # Ganti nama variabel lokalnya, misal jadi 'user_is_admin'
    user_is_admin = is_facility_admin(request.user)
    # -------------------------

    places = Place.objects.annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-created_at')

    # --- DAN GANTI DI SINI ---
    # Gunakan variabel baru 'user_is_admin'
    if filter_type == 'my_places' and user_is_admin:
        places = places.filter(admin=request.user)
    elif selected_genre:
        places = places.filter(genre=selected_genre)

    if search_query:
        places = places.filter(name__icontains=search_query) 

    context = {
        'places': places,
        # --- DAN GANTI DI SINI ---
        # Kirim variabel baru ini ke template (template HTML tidak perlu diubah)
        'is_facility_admin': user_is_admin, 
        'genres': genres_list,
        'selected_genre': selected_genre,
        'filter_type': filter_type,
    }
    return render(request, 'place/place_list.html', context)

# views.py

@login_required
def add_place(request):
    
    # --- TAMBAHKAN PENGECEKAN INI ---
    if not is_facility_admin(request.user):
        # Jika bukan admin, lempar error Dilarang Masuk
        raise PermissionDenied("Hanya Facility Administrator yang bisa menambah tempat.")
    # -------------------------------

    if request.method == 'POST':
        form = PlaceForm(request.POST, request.FILES)
        if form.is_valid():
            place = form.save(commit=False)
            place.admin = request.user
            place.save()
            return redirect('place:place_list')
    else:
        form = PlaceForm()
    return render(request, 'place/add_place.html', {'form': form})

def place_detail(request, pk):
    place = get_object_or_404(Place, id=pk)
    reviews = place.reviews.all().order_by('-created_at')
    
    is_place_owner = False
    if request.user.is_authenticated:
        # 6. CEK APAKAH USER YANG LOGIN ADALAH PEMILIK TEMPAT INI
        is_place_owner = (request.user == place.admin)

    return render(request, 'place/place_detail.html', {
        'place': place,
        'reviews': reviews,
        'is_place_owner': is_place_owner, # <-- 7. KIRIM STATUS PEMILIK KE TEMPLATE
    })

# views.py

@csrf_exempt
def add_review(request, pk): # <-- Ganti ke pk
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rating = int(data.get('rating', 5))
            comment = data.get('comment', '')

            review = Review.objects.create(
                place_id=pk, # <-- Ganti ke pk
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
    if not user.is_authenticated:
        return False
    return hasattr(user, 'profile') and user.profile.role == "FACILITY_ADMIN"

# views.py

@login_required # Ganti decoratornya jadi @login_required
def edit_place(request, pk):
    # --- TAMBAHKAN PENGECEKAN INI ---
    if not is_facility_admin(request.user):
        raise PermissionDenied("Anda bukan Facility Administrator.")
    # -------------------------------

    place = get_object_or_404(Place, id=pk)

    # Pengecekan ini SUDAH BENAR (hanya pemilik yang bisa edit)
    if request.user != place.admin:
        raise PermissionDenied("Anda tidak memiliki izin untuk mengedit tempat ini.")

    if request.method == 'POST':
        form = PlaceForm(request.POST, request.FILES, instance=place)
        if form.is_valid():
            form.save()
            return redirect('place:place_detail', pk=place.pk)
    else:
        form = PlaceForm(instance=place)
    return render(request, 'place/edit_place.html', {'form': form, 'place': place})


@login_required # Ganti decoratornya jadi @login_required
def delete_place(request, pk):
    # --- TAMBAHKAN PENGECEKAN INI ---
    if not is_facility_admin(request.user):
        raise PermissionDenied("Anda bukan Facility Administrator.")
    # -------------------------------
    
    place = get_object_or_404(Place, pk=pk)
    
    # Pengecekan ini SUDAH BENAR (hanya pemilik yang bisa hapus)
    if request.user != place.admin:
        raise PermissionDenied("Anda tidak memiliki izin untuk menghapus tempat ini.")

    if request.method == 'POST':
        place.delete()
        return redirect('place:place_list')
    
    return redirect('place:place_detail', pk=pk)