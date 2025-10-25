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
from django.core.files import File
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



@transaction.atomic
def create_facility_admin_group():
    Group.objects.get_or_create(name='Facility Administrator')

   # views.py

from django.shortcuts import render
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from .models import Place
import random

def place_list(request):
    """
    View to display and filter places with AJAX support
    Includes featured places and province statistics
    """
    # Get all places with average rating and review count
    places = Place.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).select_related('admin')
    
    # Get filter parameters
    search_query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '')
    filter_type = request.GET.get('filter', '')
    province_filter = request.GET.get('province', '')
    is_ajax = request.GET.get('ajax', '') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Apply search filter
    if search_query:
        places = places.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(province__icontains=search_query)
        )
    
    # Apply genre filter
    if selected_genre:
        places = places.filter(genre=selected_genre)
    
    # Apply province filter (from province statistics cards)
    if province_filter:
        places = places.filter(province=province_filter)
    
    # Apply "My Places" filter
    if filter_type == 'my_places' and request.user.is_authenticated:
        places = places.filter(admin=request.user)
    
    # Order by rating and date
    places = places.order_by('-avg_rating', '-created_at')
    
    # Check if user is facility admin
    is_facility_admin = False
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            is_facility_admin = request.user.profile.role == 'facility_admin'
        # Fallback: check if user has created any places
        elif Place.objects.filter(admin=request.user).exists():
            is_facility_admin = True
    
    # Get all available genres for filter buttons
    genres = Place.objects.values_list('genre', flat=True).distinct().order_by('genre')
    
    # Get featured/recommended places (random selection of top-rated venues)
    # Only show on main page, not on filtered/AJAX requests
    featured_places = []
    if not is_ajax and not search_query and not selected_genre and not filter_type:
        # Get top-rated places (rating >= 4.0 or new places)
        top_places = Place.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(
            Q(avg_rating__gte=4.0) | Q(avg_rating__isnull=True)
        )[:20]  # Get top 20
        
        # Randomly select 3 places
        top_places_list = list(top_places)
        if len(top_places_list) >= 3:
            featured_places = random.sample(top_places_list, 3)
        else:
            featured_places = top_places_list
    
    # Get province statistics (count of venues per province)
    province_stats = []
    if not is_ajax:
        province_stats = Place.objects.values('province').annotate(
            count=Count('id')
        ).filter(
            province__isnull=False
        ).exclude(
            province=''
        ).order_by('-count')[:10]  # Top 10 provinces
    
    context = {
        'places': places,
        'genres': genres,
        'selected_genre': selected_genre,
        'filter_type': filter_type,
        'is_facility_admin': is_facility_admin,
        'featured_places': featured_places,
        'province_stats': province_stats,
    }
    
    # If AJAX request, return only the venue cards partial
    if is_ajax:
        return render(request, 'place/partials/venue_cards.html', context)
    
    # Otherwise return the full page
    return render(request, 'place/place_list.html', context)

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

@csrf_exempt # Tetap pakai ini karena AJAX dari template berbeda
@require_POST # Hanya izinkan POST request
@login_required # User harus login untuk review
def add_review(request, pk):
    place = get_object_or_404(Place, pk=pk)
    try:
        data = json.loads(request.body)
        
        # Ambil rating, pastikan integer
        try:
            rating = int(data.get('rating')) # JANGAN pakai default=5
        except (ValueError, TypeError):
             return JsonResponse({'error': 'Rating tidak valid.'}, status=400)

        # Validasi rating 1-5
        if not 1 <= rating <= 5:
            return JsonResponse({'error': 'Rating harus antara 1 dan 5.'}, status=400)
            
        comment = data.get('comment', '').strip() # Ambil comment & trim

        # Opsional: Validasi comment tidak boleh kosong
        # if not comment:
        #     return JsonResponse({'error': 'Ulasan tidak boleh kosong.'}, status=400)

        # Cek apakah user sudah pernah review tempat ini (opsional, tergantung aturan)
        # existing_review = Review.objects.filter(place=place, user=request.user).first()
        # if existing_review:
        #     return JsonResponse({'error': 'Anda sudah pernah memberikan ulasan untuk tempat ini.'}, status=400)

        review = Review.objects.create(
            place=place, # Gunakan instance Place
            user=request.user,
            rating=rating,
            comment=comment
        )

        # Kirim balik data yang dibutuhkan frontend, termasuk ID review baru
        return JsonResponse({
            'review_id': review.id, # <-- Kirim ID review baru
            'user': request.user.username,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%d %b %Y, %H:%M') # Format waktu
        }, status=201) # Status 201 Created

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format data JSON tidak valid.'}, status=400)
    except Exception as e:
        print(f"Error saat add_review: {e}") # Log error di server
        return JsonResponse({'error': 'Terjadi kesalahan internal.'}, status=500)

# --- TAMBAHKAN VIEW DELETE REVIEW ---
@require_POST # Hanya izinkan POST
@login_required
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
    if not user.is_authenticated:
        return False
    return hasattr(user, 'profile') and user.profile.role == "FACILITY_ADMIN"

@login_required
def edit_place(request, pk):
    # Pengecekan izin (pastikan ini sudah benar sesuai sistem profile kamu)
    if not is_facility_admin(request.user):
        raise PermissionDenied("Anda bukan Facility Administrator.")
    
    place = get_object_or_404(Place, id=pk) # Gunakan id=pk atau pk=pk, konsisten

    # Pengecekan kepemilikan
    if request.user != place.admin:
        raise PermissionDenied("Anda tidak memiliki izin untuk mengedit tempat ini.")

    if request.method == 'POST':
        # Pastikan request.FILES diteruskan ke form
        form = PlaceForm(request.POST, request.FILES, instance=place) 
        
        if form.is_valid():
            # ============================================
            # CEK LOGIKA HAPUS GAMBAR DI SINI
            # ============================================
            
            # 1. Ambil instance TAPI JANGAN save ke DB dulu
            place_instance = form.save(commit=False) 

            # 2. Cek nilai checkbox DARI cleaned_data
            clear_checked = form.cleaned_data.get('clear_image')
            
            # Debugging: Cetak nilai checkbox
            print(f"Checkbox 'clear_image' dicentang: {clear_checked}") 

            if clear_checked:
                # 3. Hapus file fisiknya JIKA ADA
                if place_instance.image: # Pastikan ada file untuk dihapus
                   print(f"Menghapus gambar: {place_instance.image.name}")
                   place_instance.image.delete(save=False) # save=False penting!
                
                # 4. Set field image di instance menjadi None
                place_instance.image = None
                print("Field image di instance diset ke None")

            # 5. BARU simpan instance ke DB setelah semua modifikasi
            place_instance.save() 
            print("Instance disimpan ke DB")
            
            # form.save_m2m() # (Tidak perlu jika tidak ada ManyToMany)
            
            # ============================================

            messages.success(request, f"Tempat '{place.name}' berhasil diperbarui.") # Tambahkan pesan sukses
            return redirect('place:place_list')
        else:
            # Tetap cetak error jika form tidak valid
            print("Form errors:", form.errors) 
            messages.error(request, "Gagal memperbarui tempat. Periksa error di bawah.") # Tambahkan pesan error
            
    else: # GET request
        form = PlaceForm(instance=place)

    # Pastikan messages framework di-setup di base.html agar pesan muncul
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

@login_required
def delete_image(request, pk):
    if not is_facility_admin(request.user):
        raise PermissionDenied("Anda bukan Facility Administrator.")

    place = get_object_or_404(Place, id=pk)

    if request.user != place.admin:
        raise PermissionDenied("Anda tidak memiliki izin menghapus gambar tempat ini.")

    if place.image:
        place.image.delete(save=False)
        place.image = None
        place.save()
    
    messages.success(request, f"Gambar untuk tempat '{place.name}' telah dihapus.")
    return redirect('place:edit_place', pk=pk)



def _load_places_helper(request, csv_filename, genre_name, column_mapping, default_price=0, price_multiplier=1, image_filename=None):
    """
    Helper untuk memuat tempat dari file CSV dengan mapping kolom fleksibel
    dan opsi menambahkan gambar default dari file lokal.
    """
    base_data_path = os.path.join(settings.BASE_DIR, 'place', 'data') # Path ke folder data
    csv_path = os.path.join(base_data_path, csv_filename)

    if not os.path.exists(csv_path):
        return {'status': 'error', 'message': f'File CSV tidak ditemukan di: {csv_path}'}

    # --- Persiapan Path Gambar ---
    image_full_path = None
    if image_filename:
        temp_path = os.path.join(base_data_path, image_filename)
        if os.path.exists(temp_path):
            image_full_path = temp_path
            print(f"Gambar ditemukan: {image_full_path}")
        else:
            print(f"Peringatan: File gambar '{image_filename}' tidak ditemukan di {base_data_path}. Gambar tidak akan ditambahkan.")
    # ---------------------------

    try:
        # Baca CSV, coba tangani encoding & separator umum
        try:
            places_df = pd.read_csv(csv_path)
        except UnicodeDecodeError:
            places_df = pd.read_csv(csv_path, encoding='latin1') # Coba encoding lain
        except pd.errors.ParserError:
             places_df = pd.read_csv(csv_path, sep=';') # Coba separator ;

        # Opsi: Batasi jumlah baris untuk testing
        # places_df = places_df.head(10)

    except Exception as e:
        return {'status': 'error', 'message': f'Gagal membaca file CSV "{csv_filename}": {e}'}

    loaded_count = 0
    updated_count = 0
    skipped_count = 0
    image_added_count = 0 # Counter gambar
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

            # --- Siapkan data defaults (tanpa image dulu) ---
            defaults = {
                'description': str(description_raw).strip() if description_raw and not pd.isna(description_raw) else None,
                'city': str(city_raw).strip() if city_raw and not pd.isna(city_raw) else None,
                'province': str(province_raw).strip() if province_raw and not pd.isna(province_raw) else None,
                'genre': genre_name,
                'price': price,
                'admin': admin_user
            }
            # Hapus key dari defaults jika nilainya None (agar tidak menimpa data yang sudah ada)
            defaults_non_null = {k: v for k, v in defaults.items() if v is not None}

            # --- Gunakan update_or_create ---
            place_instance, created = Place.objects.update_or_create(
                name=name, # Cari berdasarkan nama
                defaults=defaults_non_null # Update hanya field yang ada nilainya
            )

            # --- TAMBAHKAN GAMBAR SETELAH INSTANCE ADA ---
            image_saved = False
            if image_full_path and (created or not place_instance.image):
                try:
                    with open(image_full_path, 'rb') as img_file:
                        django_file = File(img_file)
                        place_instance.image.save(image_filename, django_file, save=True) # save=True agar langsung update DB
                        image_saved = True
                        image_added_count += 1
                        print(f"Gambar '{image_filename}' ditambahkan ke '{place_instance.name}'")
                except Exception as img_e:
                    print(f"Gagal menambahkan gambar ke '{place_instance.name}': {img_e}")
            # -----------------------------------------------

            if created:
                loaded_count += 1
            # Hitung update hanya jika instance TIDAK baru dibuat DAN gambar TIDAK baru ditambahkan
            elif not created and not image_saved: 
                updated_count += 1

        except Exception as e:
            print(f"!! ERROR Gagal memproses baris {index+2} ({name}): {e}") # Log error umum
            skipped_count += 1
            continue # Lanjut ke baris berikutnya

    return {
        'status': 'success', 'loaded': loaded_count, 'updated': updated_count,
        'skipped': skipped_count, 'images_added': image_added_count, 'filename': csv_filename,
        'message': f'File "{csv_filename}": {loaded_count} tempat baru, {updated_count} update, {image_added_count} gambar ditambah, {skipped_count} dilewati.'
    }
    """
    Helper untuk memuat tempat dari file CSV dengan mapping kolom fleksibel
    dan opsi menambahkan gambar default dari file lokal.
    """
    base_data_path = os.path.join(settings.BASE_DIR, 'place', 'data') # Path ke folder data
    csv_path = os.path.join(base_data_path, csv_filename)

    if not os.path.exists(csv_path):
        return {'status': 'error', 'message': f'File CSV tidak ditemukan di: {csv_path}'}

    # --- Persiapan Path Gambar ---
    image_full_path = None
    if image_filename:
        temp_path = os.path.join(base_data_path, image_filename)
        if os.path.exists(temp_path):
            image_full_path = temp_path
            print(f"Gambar ditemukan: {image_full_path}")
        else:
            print(f"Peringatan: File gambar '{image_filename}' tidak ditemukan di {base_data_path}. Gambar tidak akan ditambahkan.")
    # ---------------------------

    try:
        # ... (Kode baca CSV tidak berubah) ...
        try:
            places_df = pd.read_csv(csv_path)
        except UnicodeDecodeError:
            places_df = pd.read_csv(csv_path, encoding='latin1')
        except pd.errors.ParserError:
             places_df = pd.read_csv(csv_path, sep=';')

    except Exception as e:
        return {'status': 'error', 'message': f'Gagal membaca file CSV "{csv_filename}": {e}'}

    loaded_count = 0
    updated_count = 0
    skipped_count = 0
    image_added_count = 0 # Counter gambar
    admin_user = request.user if request.user.is_authenticated else None

    # Iterasi per baris DataFrame
    for index, data in places_df.iterrows():
        try:
            # ... (Kode ambil data name, description, city, province, price tidak berubah) ...
            name = data.get(column_mapping.get('name'))
            # ... (Validasi name) ...
            name = str(name).strip()
            # ... (Logika harga) ...
            price = Decimal(default_price)
            # ... (Try-except harga) ...

            # --- Siapkan data defaults (tanpa image dulu) ---
            defaults = {
                'description': str(data.get(column_mapping.get('description'), '')).strip(),
                'city': str(data.get(column_mapping.get('city'), '')).strip() or None, # Jadi None jika string kosong
                'province': str(data.get(column_mapping.get('province'), '')).strip() or None,
                'genre': genre_name,
                'price': price,
                'admin': admin_user
            }
            defaults = {k: v for k, v in defaults.items() if v is not None} # Hapus None

            # --- Gunakan update_or_create ---
            place_instance, created = Place.objects.update_or_create(
                name=name, # Cari berdasarkan nama
                defaults=defaults
            )

            # --- TAMBAHKAN GAMBAR SETELAH INSTANCE ADA ---
            image_saved = False
            # Hanya tambahkan jika ada path gambar, instance baru dibuat ATAU instance lama tapi belum punya gambar
            if image_full_path and (created or not place_instance.image):
                try:
                    with open(image_full_path, 'rb') as img_file:
                        # Buat Django File object
                        django_file = File(img_file)
                        # Simpan ke ImageField, gunakan nama file asli
                        place_instance.image.save(image_filename, django_file, save=True)
                        image_saved = True
                        image_added_count += 1
                        print(f"Gambar '{image_filename}' ditambahkan ke '{place_instance.name}'")
                except Exception as img_e:
                    print(f"Gagal menambahkan gambar ke '{place_instance.name}': {img_e}")
            # -----------------------------------------------

            if created:
                loaded_count += 1
            elif not image_saved: # Hanya hitung update jika gambar tidak baru ditambahkan
                updated_count += 1

        except Exception as e:
            print(f"Gagal memproses baris {index+2} ({name}): {e}")
            skipped_count += 1
            continue

    return {
        'status': 'success', 'loaded': loaded_count, 'updated': updated_count,
        'skipped': skipped_count, 'images_added': image_added_count, 'filename': csv_filename,
        'message': f'File "{csv_filename}": {loaded_count} tempat baru, {updated_count} update, {image_added_count} gambar ditambah, {skipped_count} dilewati.'
    }

def load_places_cycling(request):
    csv_filename = 'cycling_track.csv' 
    genre = 'Bicycle Tracking' 
    image_filename_to_load = 'cycling_track.png'

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
        image_filename=image_filename_to_load 
    )

    messages.info(request, result['message'])
    return redirect('place:place_list')

def load_places_running(request):
    csv_filename = 'running_tracks.csv'
    genre = 'Running Track'
    image_filename_to_load = 'running_track.png' 


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
        image_filename=image_filename_to_load 
    )

    messages.info(request, result['message'])
    return redirect('place:place_list')



def load_places_swimming(request):
    csv_filename = 'swimming_pool.csv'
    genre = 'Swimming Pool'
    image_filename_to_load = 'swimming_pool.png' 


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
        image_filename=image_filename_to_load 
    )

    messages.info(request, result['message'])
    return redirect('place:place_list')

