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
from django.contrib import messages
import pandas as pd
import os
from django.conf import settings
# place/views.py
from django.views.decorators.http import require_POST
import pandas as pd
import os
import re
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required # Sebaiknya hanya admin
from django.contrib import messages
from .models import Place # <-- IMPOR MODEL PLACE KAMU
from django.contrib.auth.models import User # Untuk field admin
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Place, Review
import json
from django.shortcuts import render
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from .models import Place
import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import PlaceSerializer, ReviewSerializer

# Add to place/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count

# API to add place from Flutter
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_add_place(request):
    try:
        data = request.data
        place = Place.objects.create(
            name=data.get('name'),
            price=data.get('price', 0),
            description=data.get('description', ''),
            city=data.get('city', ''),
            province=data.get('province', ''),
            genre=data.get('genre', ''),
            image_url=data.get('image_url'),
            admin=request.user
        )
        return Response({'success': True, 'id': place.id, 'message': 'Place created successfully'}, status=201)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=400)

# API for province stats
@api_view(['GET'])
def api_province_stats(request):
    stats = Place.objects.values('province').annotate(
        count=Count('id')
    ).exclude(province__isnull=True).exclude(province='').order_by('-count')
    
    return Response([{
        'province': s['province'],
        'count': s['count'],
        'image_url': None  # Add image URLs if you have them
    } for s in stats])

# API to add review from Flutter
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_add_review(request, pk):
    try:
        place = get_object_or_404(Place, pk=pk)
        data = request.data
        
        # Check if user already reviewed
        if Review.objects.filter(place=place, user=request.user).exists():
            return Response({'success': False, 'error': 'Anda sudah memberikan review'}, status=400)
        
        review = Review.objects.create(
            place=place,
            user=request.user,
            rating=int(data.get('rating', 0)),
            comment=data.get('comment', '')
        )
        return Response({'success': True, 'id': review.id})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=400)

# API to delete review
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_delete_review(request, review_id):
    try:
        review = get_object_or_404(Review, pk=review_id)
        if review.user != request.user and not is_admin(request.user):
            return Response({'success': False, 'error': 'Unauthorized'}, status=403)
        review.delete()
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=400)

# 1. API untuk List Tempat (Flutter Home)
@api_view(['GET'])
def api_place_list(request):
    places = Place.objects.all()
    serializer = PlaceSerializer(places, many=True)
    return Response(serializer.data)

# 2. API untuk Detail Tempat (Flutter Detail Page)
@api_view(['GET'])
def api_place_detail(request, pk):
    try:
        place = Place.objects.get(pk=pk)
    except Place.DoesNotExist:
        return Response({'error': 'Place not found'}, status=404)

    serializer = PlaceSerializer(place)
    return Response(serializer.data)

# 3. API untuk Lihat Review di suatu tempat
@api_view(['GET'])
def api_place_reviews(request, pk):
    try:
        place = Place.objects.get(pk=pk)
        reviews = Review.objects.filter(place=place)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    except Place.DoesNotExist:
        return Response({'error': 'Place not found'}, status=404)

@transaction.atomic
def create_facility_admin_group():
    Group.objects.get_or_create(name='Facility Administrator')

   # views.py


@login_required(login_url='/login/')
def place_list(request):
    """
    View to display and filter places with AJAX support
    Includes featured places and province statistics
    """
    places = Place.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).select_related('admin')
    
    search_query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '')
    filter_type = request.GET.get('filter', '')
    province_filter = request.GET.get('province', '')
    is_ajax = request.GET.get('ajax', '') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if search_query:
        places = places.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(province__icontains=search_query)
        )
    
    if selected_genre:
        places = places.filter(genre=selected_genre)
    
    if province_filter:
        places = places.filter(province=province_filter)
    
    # "My Places" filter - show user's own places
    if filter_type == 'my_places' and request.user.is_authenticated:
        places = places.filter(admin=request.user)
    
    places = places.order_by('-avg_rating', '-created_at')
    
    # Check if user can add/manage places (Admin OR Facility Admin)
    is_facility_admin_user = is_admin_or_facility_admin(request.user)
    
    genres = Place.objects.values_list('genre', flat=True).distinct().order_by('genre')
    
    featured_places = []
    if not is_ajax and not search_query and not selected_genre and not filter_type:
        top_places = Place.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(
            Q(avg_rating__gte=4.0) | Q(avg_rating__isnull=True)
        )[:20]
        
        top_places_list = list(top_places)
        if len(top_places_list) >= 3:
            featured_places = random.sample(top_places_list, 3)
        else:
            featured_places = top_places_list
    
    province_stats = []
    if not is_ajax:
        province_stats = Place.objects.values('province').annotate(
            count=Count('id')
        ).filter(
            province__isnull=False
        ).exclude(
            province=''
        ).order_by('-count')[:10]
    
    context = {
        'places': places,
        'genres': genres,
        'selected_genre': selected_genre,
        'filter_type': filter_type,
        'is_facility_admin': is_facility_admin_user,  # Both Admin and Facility Admin
        'is_admin': is_admin(request.user),
        'featured_places': featured_places,
        'province_stats': province_stats,
    }
    
    if is_ajax:
        return render(request, 'place/partials/venue_cards.html', context)
    
    return render(request, 'place/place_list.html', context)


@login_required
def add_place(request):
    """
    Add a new place (Admin OR Facility Admin)
    """
    # Check if user is Admin OR Facility Admin
    if not is_admin_or_facility_admin(request.user):
        raise PermissionDenied("Hanya Admin atau Facility Administrator yang bisa menambah tempat.")

    if request.method == 'POST':
        form = PlaceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                place = form.save(commit=False)
                place.admin = request.user
                place.save()
                
                messages.success(request, f"✅ Tempat '{place.name}' berhasil ditambahkan!")
                return redirect('place:place_list')
                
            except Exception as e:
                messages.error(request, f"❌ Gagal menambahkan tempat: {str(e)}")
                print(f"Error adding place: {e}")
        else:
            messages.error(request, "⚠️ Gagal menambahkan tempat. Periksa form Anda.")
            print(f"Form errors: {form.errors}")
    else:
        form = PlaceForm()
    
    return render(request, 'place/add_place.html', {'form': form})

@login_required(login_url='/login/')
# Update your place_detail function in views.py

@login_required(login_url='/login/')
def place_detail(request, pk):
    """
    View to display place details with reviews and featured places sidebar
    """
    # Get the place object
    place = get_object_or_404(Place, pk=pk)
    
    # Get all reviews for this place, ordered by newest first
    reviews = Review.objects.filter(place=place).select_related('user').order_by('-created_at')
    
    # Check if current user is the place owner
    is_place_owner = request.user.is_authenticated and request.user == place.admin
    
    # Check if user is admin (can delete any review)
    user_is_admin = is_admin(request.user)
    
    # Get featured places for sidebar (exclude current place)
    featured_places_qs = Place.objects.exclude(
        pk=place.pk
    ).annotate(
        avg_rating=Avg('reviews__rating')
    ).filter(
        Q(avg_rating__gte=4.0) | Q(avg_rating__isnull=True)
    )[:20]
    
    featured_places_list = list(featured_places_qs)
    
    if len(featured_places_list) >= 5:
        featured_places = random.sample(featured_places_list, 5)
    elif len(featured_places_list) >= 3:
        featured_places = random.sample(featured_places_list, 3)
    else:
        featured_places = featured_places_list
    
    context = {
        'place': place,
        'reviews': reviews,
        'is_place_owner': is_place_owner,
        'is_admin': user_is_admin,  # ADD THIS - untuk delete review
        'featured_places': featured_places,
    }
    
    return render(request, 'place/place_detail.html', context)

@csrf_exempt # Tetap pakai ini karena AJAX dari template berbeda
@require_POST # Hanya izinkan POST request
@login_required(login_url='/login/')
@require_POST
def add_review(request, pk):
    """Add a review for a place - ALWAYS returns JSON"""
    
    # Check authentication
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Anda harus login terlebih dahulu.'
        }, status=401)
    
    # Get place
    try:
        place = get_object_or_404(Place, pk=pk)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Tempat tidak ditemukan: {str(e)}'
        }, status=404)
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid JSON: {str(e)}'
        }, status=400)
    
    # Get and validate rating
    rating_value = data.get('rating')
    
    if rating_value is None:
        return JsonResponse({
            'success': False,
            'error': 'Rating tidak boleh kosong.'
        }, status=400)
    
    # Convert to integer
    try:
        rating = int(rating_value)
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'error': f'Rating harus berupa angka: {str(e)}'
        }, status=400)
    
    # Validate rating range
    if not 1 <= rating <= 5:
        return JsonResponse({
            'success': False,
            'error': 'Rating harus antara 1 dan 5.'
        }, status=400)
    
    # Get comment
    comment = data.get('comment', '').strip()
    
    # Check if user already reviewed
    existing_review = Review.objects.filter(
        place=place, 
        user=request.user
    ).first()
    
    if existing_review:
        return JsonResponse({
            'success': False,
            'error': 'Anda sudah memberikan ulasan untuk tempat ini.'
        }, status=400)
    
    # Create review
    try:
        review = Review.objects.create(
            place=place,
            user=request.user,
            rating=rating,
            comment=comment
        )
        
        # Return success response
        return JsonResponse({
            'success': True,
            'review_id': review.id,
            'user': request.user.username,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%d %b %Y, %H:%M')
        }, status=201)
        
    except Exception as e:
        # Log the full error
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': f'Gagal membuat review: {str(e)}'
        }, status=500)
    
@require_POST # Hanya izinkan POST
@login_required(login_url='/login/')
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)

    # Autorisasi: Hanya user yang buat review yang bisa hapus
    if request.user != review.user:
        return JsonResponse({'success': False, 'error': 'Anda tidak punya izin menghapus ulasan ini.'}, status=403) # 403 Forbidden

    try:
        review.delete()
        return JsonResponse({'success': True, 'message': 'Ulasan berhasil dihapus.'})
    except Exception as e:
        print(f"Error saat delete_review: {e}")
        return JsonResponse({'success': False, 'error': 'Gagal menghapus ulasan.'}, status=500)
    
def is_facility_admin(user):
    """Check if user is a Facility Admin"""
    if not user.is_authenticated:
        return False
    return hasattr(user, 'profile') and user.profile.role == "FACILITY_ADMIN"

def is_admin(user):
    """Check if user is an Admin"""
    if not user.is_authenticated:
        return False
    return hasattr(user, 'profile') and user.profile.role == "ADMIN"

def is_admin_or_facility_admin(user):
    """Check if user is either Admin or Facility Admin"""
    if not user.is_authenticated:
        return False
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role in ["ADMIN", "FACILITY_ADMIN"]

def can_manage_place(user, place):
    """
    Check if user can manage a specific place
    - Admin can manage ALL places
    - Facility Admin can only manage their OWN places
    """
    if not user.is_authenticated:
        return False
    
    # Admin can manage everything
    if is_admin(user):
        return True
    
    # Facility Admin can only manage their own places
    if is_facility_admin(user):
        return user == place.admin
    
    return False

@login_required(login_url='/login/')
def edit_place(request, pk):
    """
    Edit an existing place
    - Admin can edit ANY place
    - Facility Admin can only edit THEIR OWN places
    """
    place = get_object_or_404(Place, id=pk)
    
    # Check permission using helper function
    if not can_manage_place(request.user, place):
        raise PermissionDenied("Anda tidak memiliki izin untuk mengedit tempat ini.")

    if request.method == 'POST':
        form = PlaceForm(request.POST, request.FILES, instance=place) 
        
        if form.is_valid():
            try:
                place_instance = form.save(commit=False) 
                clear_checked = form.cleaned_data.get('clear_image')
                
                if clear_checked:
                    if place_instance.image:
                        print(f"Menghapus gambar: {place_instance.image.name}")
                        place_instance.image.delete(save=False)
                    place_instance.image = None

                place_instance.save()
                
                messages.success(request, f"✅ Tempat '{place.name}' berhasil diperbarui!")
                return redirect('place:place_list')
                
            except Exception as e:
                messages.error(request, f"❌ Gagal memperbarui tempat: {str(e)}")
                print(f"Error updating place: {e}")
        else:
            messages.error(request, "⚠️ Gagal memperbarui tempat. Periksa error di bawah.")
            print("Form errors:", form.errors)
            
    else:
        form = PlaceForm(instance=place)

    return render(request, 'place/edit_place.html', {'form': form, 'place': place})


@login_required(login_url='/login/')
def delete_place(request, pk):
    """
    Delete a place
    - Admin can delete ANY place
    - Facility Admin can only delete THEIR OWN places
    """
    place = get_object_or_404(Place, pk=pk)
    
    # Check permission using helper function
    if not can_manage_place(request.user, place):
        raise PermissionDenied("Anda tidak memiliki izin untuk menghapus tempat ini.")

    if request.method == 'POST':
        place_name = place.name
        
        try:
            place.delete()
            messages.success(request, f"✅ Tempat '{place_name}' berhasil dihapus!")
        except Exception as e:
            messages.error(request, f"❌ Gagal menghapus tempat: {str(e)}")
        
        return redirect('place:place_list')
    
    return redirect('place:place_detail', pk=pk)

@login_required(login_url='/login/')
def delete_image(request, pk):
    """
    Delete place image
    - Admin can delete ANY place's image
    - Facility Admin can only delete THEIR OWN place's image
    """
    place = get_object_or_404(Place, id=pk)

    # Check permission using helper function
    if not can_manage_place(request.user, place):
        raise PermissionDenied("Anda tidak memiliki izin menghapus gambar tempat ini.")

    if place.image:
        place.image.delete(save=False)
        place.image = None
        place.save()
        messages.success(request, f"✅ Gambar untuk tempat '{place.name}' telah dihapus.")
    else:
        messages.info(request, f"ℹ️ Tempat '{place.name}' tidak memiliki gambar.")
    
    return redirect('place:edit_place', pk=pk)




SWIMMING_IMAGE_URL = "https://img.freepik.com/free-photo/five-male-swimmers-racing-against-each-other_171337-7922.jpg?semt=ais_hybrid&w=740&q=80"
RUNNING_IMAGE_URL = "https://gallantsports.in/wp-content/uploads/2025/05/running-track-.webp"
CYCLING_IMAGE_URL = "https://assets.usacycling.org/prod/assets/_1200xAUTO_crop_center-center_none/How-to-Get-Started-with-Track.jpg"


def _load_places_helper(request, csv_filename, genre_name, column_mapping, default_price=0, price_multiplier=1, default_image_url=None):
    """
    Helper untuk memuat tempat dari file CSV dengan mapping kolom fleksibel
    dan menetapkan gambar default berbasis URL untuk masing-masing kategori.
    """
    base_data_path = os.path.join(settings.BASE_DIR, 'place', 'data') # Path ke folder data
    csv_path = os.path.join(base_data_path, csv_filename)

    if not os.path.exists(csv_path):
        return {'status': 'error', 'message': f'File CSV tidak ditemukan di: {csv_path}'}

    try:
        # Baca CSV, coba tangani encoding & separator umum
        try:
            places_df = pd.read_csv(csv_path)
        except UnicodeDecodeError:
            places_df = pd.read_csv(csv_path, encoding='latin1') # Coba encoding lain
        except pd.errors.ParserError:
             places_df = pd.read_csv(csv_path, sep=';') # Coba separator ;

        # Normalisasi header (hilangkan spasi & BOM) supaya kolom 'name' terbaca di semua file
        places_df.rename(columns=lambda c: str(c).strip().lstrip('\ufeff'), inplace=True)

        # Opsi: Batasi jumlah baris untuk testing
        # places_df = places_df.head(10)

    except Exception as e:
        return {'status': 'error', 'message': f'Gagal membaca file CSV "{csv_filename}": {e}'}

    loaded_count = 0
    updated_count = 0
    skipped_count = 0
    image_assigned_count = 0
    admin_user = request.user if request.user.is_authenticated else None

    # Iterasi per baris DataFrame
    for index, data in places_df.iterrows():
        name = None # Inisialisasi name untuk logging error
        try:
            # Ambil data dari CSV sesuai mapping
            name = data.get(column_mapping.get('name'))
            description_raw = data.get(column_mapping.get('description'))
            city_raw = data.get(column_mapping.get('city'))
            province_raw = data.get(column_mapping.get('province'))
            price_raw = data.get(column_mapping.get('price'))

            # --- Validasi Data Penting ---
            if not name or pd.isna(name):
                print(f"Baris {index+2} dilewati: Nama tempat kosong.")
                skipped_count += 1
                continue
            name = str(name).strip() # Pastikan string & hapus spasi

            print(f"--- Baris {index+2} ({name}) ---") # DEBUG PRINT 1: Awal proses baris
            print(f"Harga RAW dari CSV: '{price_raw}' (Tipe: {type(price_raw)})") # DEBUG PRINT 2: Harga mentah

            # --- Logika Harga (Jika ada di CSV) ---
            price = Decimal(default_price) # Mulai dengan default
            if price_raw is not None and not pd.isna(price_raw):
                try:
                    price_str = str(price_raw).strip() # Jadikan string & hapus spasi
                    # Regex untuk ambil angka (termasuk desimal jika ada), hapus non-digit kecuali .
                    # Modifikasi regex agar lebih kuat (tangani Rp, titik ribuan, koma desimal)
                    price_match_rp = re.search(r'([\d.]+)[,.]?(\d{2})?$', price_str.replace('.', '')) # Hapus titik ribuan dulu
                    price_match_num = re.search(r'([\d,]+)[.,]?(\d{2})?$', price_str) # Tangani koma sbg pemisah ribuan

                    cleaned_price_str = None
                    if price_match_rp:
                         cleaned_price_str = price_match_rp.group(1).replace(',', '.') # Ganti koma desimal jadi titik
                    elif price_match_num:
                         cleaned_price_str = price_match_num.group(1).replace(',', '') # Hapus koma ribuan
                    else:
                        raise ValueError("Format harga tidak dikenali regex.")

                    print(f"Harga setelah dibersihkan: '{cleaned_price_str}'") # DEBUG PRINT 3: Harga bersih
                    
                    # Konversi ke Decimal & kalikan multiplier
                    price = (Decimal(cleaned_price_str) * Decimal(price_multiplier)).quantize(Decimal('0.01')) # Pastikan 2 desimal
                    print(f"Harga FINAL (setelah multiplier {price_multiplier}): {price}") # DEBUG PRINT 4: Harga jadi

                except (ValueError, InvalidOperation, AttributeError) as e:
                    # JIKA ERROR KONVERSI, akan pakai default_price (0)
                    print(f"-> GAGAL konversi harga: {e}. Menggunakan harga default ({price})") # DEBUG PRINT 5: Error konversi
                    # price tetap bernilai default_price
            else:
                 print(f"-> Harga RAW kosong atau NaN. Menggunakan harga default ({price})") # DEBUG PRINT 6: Harga kosong

            # --- Siapkan data defaults termasuk image URL jika disediakan ---
            defaults = {
                'description': str(description_raw).strip() if description_raw and not pd.isna(description_raw) else None,
                'city': str(city_raw).strip() if city_raw and not pd.isna(city_raw) else None,
                'province': str(province_raw).strip() if province_raw and not pd.isna(province_raw) else None,
                'genre': genre_name,
                'price': price,
                'admin': admin_user
            }

            if default_image_url:
                defaults['image'] = default_image_url

            # Hapus key dari defaults jika nilainya None (agar tidak menimpa data yang sudah ada)
            defaults_non_null = {k: v for k, v in defaults.items() if v is not None}

            # --- Gunakan update_or_create ---
            place_instance, created = Place.objects.update_or_create(
                name=name, # Cari berdasarkan nama
                defaults=defaults_non_null # Update hanya field yang ada nilainya
            )

            if default_image_url:
                image_assigned_count += 1

            if created:
                loaded_count += 1
            else:
                updated_count += 1

        except Exception as e:
            print(f"!! ERROR Gagal memproses baris {index+2} ({name}): {e}") # Log error umum
            skipped_count += 1
            continue # Lanjut ke baris berikutnya

    return {
        'status': 'success', 'loaded': loaded_count, 'updated': updated_count,
        'skipped': skipped_count, 'images_assigned': image_assigned_count, 'filename': csv_filename,
        'message': f'File "{csv_filename}": {loaded_count} tempat baru, {updated_count} update, {image_assigned_count} gambar/url ditetapkan, {skipped_count} dilewati.'
    }
    
@login_required(login_url='/login/')
def load_places_cycling(request):
    """Load cycling places from CSV (Admin OR Facility Admin)"""
    if not is_admin_or_facility_admin(request.user):
        raise PermissionDenied("Hanya Admin atau Facility Administrator yang dapat memuat data.")
    
    csv_filename = 'cycling_track.csv' 
    genre = 'Bicycle Tracking' 

    column_mapping = {
        'name': 'name', 
        'description': 'description',
        'city': 'city',
        'province': 'province',
        'price': 'price' 
    }
   
    result = _load_places_helper(
        request, csv_filename, genre, column_mapping,
        price_multiplier=1,
        default_image_url=CYCLING_IMAGE_URL
    )

    messages.info(request, result['message'])
    return redirect('place:place_list')


@login_required(login_url='/login/')
def load_places_running(request):
    """Load running places from CSV (Admin OR Facility Admin)"""
    if not is_admin_or_facility_admin(request.user):
        raise PermissionDenied("Hanya Admin atau Facility Administrator yang dapat memuat data.")
    
    csv_filename = 'running_tracks.csv'
    genre = 'Running Track'

    column_mapping = {
        'name': 'name',
        'price': 'price',
        'description': 'description',
        'city': 'city',          
        'province': 'province'      
    }

    result = _load_places_helper(
        request, csv_filename, genre, column_mapping,
        price_multiplier=1, 
        default_image_url=RUNNING_IMAGE_URL
    )

    messages.info(request, result['message'])
    return redirect('place:place_list')


@login_required(login_url='/login/')
def load_places_swimming(request):
    """Load swimming places from CSV (Admin OR Facility Admin)"""
    if not is_admin_or_facility_admin(request.user):
        raise PermissionDenied("Hanya Admin atau Facility Administrator yang dapat memuat data.")
    
    csv_filename = 'swimming_pool.csv'
    genre = 'Swimming Pool'

    column_mapping = {
        'name': 'name',
        'price': 'price',
        'description': 'description',
        'city': 'city',          
        'province': 'province'      
    }

    result = _load_places_helper(
        request, csv_filename, genre, column_mapping,
        price_multiplier=1, 
        default_image_url=SWIMMING_IMAGE_URL
    )

    messages.info(request, result['message'])
    return redirect('place:place_list')


@login_required(login_url='/login/')
@require_POST
def delete_all_places(request):
    """Remove every place; only Admin can trigger this."""
    if not is_admin(request.user):
        raise PermissionDenied("Hanya Admin yang dapat menghapus semua tempat.")

    deleted_count, _ = Place.objects.all().delete()
    messages.success(request, f"✅ Semua {deleted_count} tempat berhasil dihapus.")
    return redirect('place:place_list')

from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Q
from .models import Place, Review
import random

@login_required(login_url='/login/')
def place_detail(request, pk):
    """
    View to display place details with reviews and featured places sidebar
    """
    # Get the place object
    place = get_object_or_404(Place, pk=pk)
    
    # Get all reviews for this place, ordered by newest first
    reviews = Review.objects.filter(place=place).select_related('user').order_by('-created_at')
    
    # Check if current user is the place owner
    is_place_owner = request.user.is_authenticated and request.user == place.admin
    
    # Get featured places for sidebar (exclude current place)
    # Get top-rated places or random selection
    featured_places_qs = Place.objects.exclude(
        pk=place.pk  # Exclude current place
    ).annotate(
        avg_rating=Avg('reviews__rating')
    ).filter(
        Q(avg_rating__gte=4.0) | Q(avg_rating__isnull=True)  # Top rated or new
    )[:20]  # Get top 20
    
    # Convert to list and randomly select 3-5 places
    featured_places_list = list(featured_places_qs)
    
    if len(featured_places_list) >= 5:
        featured_places = random.sample(featured_places_list, 5)
    elif len(featured_places_list) >= 3:
        featured_places = random.sample(featured_places_list, 3)
    else:
        featured_places = featured_places_list
    
    context = {
        'place': place,
        'reviews': reviews,
        'is_place_owner': is_place_owner,
        'featured_places': featured_places,
    }
    
    return render(request, 'place/place_detail.html', context)

