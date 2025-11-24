import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .forms import ProductForm
from .models import Product, Cart, CartItem, Wishlist
from django.contrib import messages
from django.urls import reverse
from django.template.defaultfilters import truncatewords
from django.http import HttpResponseBadRequest
import pandas as pd
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.views.decorators.http import require_GET


def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    try:
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return True
    except Exception:
        pass
    return user.groups.filter(name__iexact='admin').exists()

def delete_all_products(request):
    Product.objects.all().delete()
    return JsonResponse({'status': 'success', 'message': 'Semua produk telah dihapus'})

#def delete_products_without_seller(request):
#    """Delete all products without seller"""
#    # Hitung jumlah produk tanpa seller
#    products_without_seller = Product.objects.filter(seller__isnull=True)
#    count = products_without_seller.count()
#    
#    if count == 0:
#        return JsonResponse({
#            'status': 'info',
#            'message': 'Tidak ada produk tanpa seller yang perlu dihapus.'
#        })
#    
#    # Hapus thumbnail files terlebih dahulu jika ada
#    for product in products_without_seller:
#        if product.thumbnail:
#            try:
#                if hasattr(product.thumbnail, 'path') and os.path.isfile(product.thumbnail.path):
#                    product.thumbnail.delete(save=False)
#            except Exception:
#                pass
#    
#    # Hapus semua produk tanpa seller
#    products_without_seller.delete()
#    
#    return JsonResponse({
#        'status': 'success',
#        'message': f'Berhasil menghapus {count} produk tanpa seller.',
#        'count': count
#    })

def load_dataset_cycling(request):
    # Gunakan path absolut berdasarkan BASE_DIR
    csv_path = os.path.join(settings.BASE_DIR, 'shop', 'specialized.csv')
    
    # Cek apakah file ada
    if not os.path.exists(csv_path):
        return JsonResponse({
            'status': 'error', 
            'message': f'File CSV tidak ditemukan di: {csv_path}'
        })
    
    # Load datasets
    products_df = pd.read_csv(csv_path, nrows=100)
    for data in products_df.itertuples():
        Product.objects.get_or_create(
            name=data.name,
            price=data.price * 1000,
            stock=100,
            description=data.p_subCategory3,
            category='cycling',
            thumbnail='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQH5yhRNqPTF6in-1CodH3p5Nn40H8pT6r72Q&s',
            seller= request.user if request.user.is_authenticated else None
        )
    
    # Convert DataFrame to list of dictionaries
    products_data = products_df.to_dict(orient='records')
    
    return JsonResponse({
        'status': 'success',
        'products': products_data,
        'message': f'Berhasil memuat {len(products_data)} produk'
    })



def load_dataset_running(request):
    csv_path = os.path.join(settings.BASE_DIR, 'shop', 'running.csv')
    
    if not os.path.exists(csv_path):
        return JsonResponse({
            'status': 'error', 
            'message': f'File CSV tidak ditemukan di: {csv_path}'
        })
    
    products_df = pd.read_csv(csv_path, nrows=100)

    running_products = products_df[products_df['name'].str.contains('Running', case=False, na=False)]
    
    for data in running_products.itertuples():
        Product.objects.get_or_create(
            name=data.name,
            price=data.actual_price * 1000,
            stock=150,
            description=data.main_category,
            category='running',
            thumbnail=data.image,
            seller= request.user if request.user.is_authenticated else None
        )
    
    products_data = running_products.to_dict(orient='records')
    
    return JsonResponse({
        'status': 'success',
        'products': products_data,
        'message': f'Berhasil memuat {len(products_data)} produk'
    })

def load_dataset_swimming(request):
    csv_path = os.path.join(settings.BASE_DIR, 'shop', 'swimming_ril.csv')
    
    if not os.path.exists(csv_path):
        return JsonResponse({
            'status': 'error', 
            'message': f'File CSV tidak ditemukan di: {csv_path}'
        })
    
    products_df = pd.read_csv(csv_path)
    
    for data in products_df.itertuples():
        Product.objects.get_or_create(
            name=data.name,
            price=data.price * 100,
            stock=120,
            description=data.product,
            category='swimming',
            thumbnail='https://www.orca.com/uploads/products/rrss/ra31ttsb-01-orca-killa-comfort-swimming-goggles-smoke-black_800x800.jpg',
            seller= request.user if request.user.is_authenticated else None
        )
    

    products_data = products_df.to_dict(orient='records')
    
    return JsonResponse({
        'status': 'success',
        'products': products_data,
        'message': f'Berhasil memuat {len(products_data)} produk'
    })

@login_required
def add_product(request):
    """Add new product to the shop"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product_entry = form.save(commit=False)
            if request.user.is_authenticated:
                product_entry.seller = request.user
            product_entry.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Produk berhasil ditambahkan!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
            
    form = ProductForm()
    context = {'form': form}
    return render(request, "add_product.html", context)

def show_product(request):
    if request.method == 'POST' and request.user.is_authenticated and is_admin(request.user):
        action = request.POST.get('action')
        if action == 'admin_delete':
            pid = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=pid)
            name = product.name

    
            try:
                if getattr(product, 'thumbnail', None) and hasattr(product.thumbnail, 'path') and os.path.isfile(product.thumbnail.path):
                    product.thumbnail.delete(save=False)
            except Exception:
                pass

            product.delete() 

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'product_id': str(pid), 'message': f'Produk "{name}" dihapus'})
            
            messages.success(request, f'Produk "{name}" dihapus')
            return redirect('shop:shop')

    filter_type = request.GET.get("filter", "all")
    category_filter = request.GET.get("category", None)

    products = Product.objects.all()
    if filter_type == "my" and request.user.is_authenticated:
        products = products.filter(seller=request.user)
    if category_filter:
        products = products.filter(category=category_filter)

    products = products.order_by('-id')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_list_json = []
        for product in products:
            product_list_json.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock': product.stock,
                'description': truncatewords(product.description, 15),
                'thumbnail': product.thumbnail,
                'detail_url': reverse('shop:product_detail', args=[product.id]),
                'cart_url': reverse('shop:add_to_cart', args=[product.id]),
                'wishlist_url': reverse('shop:toggle_wishlist', args=[product.id]),
            })
        return JsonResponse({'products': product_list_json})

    context = {
        'products': products,
        'user': request.user,
        'user_is_admin': is_admin(request.user),
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    return render(request, "shop.html", context)

def product_detail(request, id):
    product = get_object_or_404(Product, pk=id)

    in_wishlist = False

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            try:
                wishlist = Wishlist.objects.filter(user=request.user).first()
                if wishlist:
                    in_wishlist = wishlist.products.filter(pk=product.pk).exists()
            except Exception as e:
                in_wishlist = False
        
        data = {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'description': product.description, 
            'stock': product.stock,
            'category': product.category,
            'seller': (product.seller.username if getattr(product, 'seller', None) else None),
            'thumbnail': (
                product.thumbnail.url if getattr(product.thumbnail, 'url', None)
                else (str(product.thumbnail) if getattr(product, 'thumbnail', None) else '')
            ),
            'cart_url': reverse('shop:add_to_cart', args=[product.id]),
            'wishlist_url': reverse('shop:toggle_wishlist', args=[product.id]),
            'can_edit': (request.user.is_authenticated and (request.user == getattr(product, 'seller', None) or request.user.is_staff)),
            'edit_url': reverse('shop:edit_product', args=[product.id]),
            'delete_url': reverse('shop:delete_product', args=[product.id]),
            'in_wishlist': in_wishlist, 
        }
        
        return JsonResponse({'status': 'success', 'product': data})

    return render(request, 'product_detail.html', {
        'product': product,
        'product_id': product.id,
        'in_wishlist': in_wishlist,
    })

@login_required
def delete_product(request, id):
    """Delete product from the shop"""
    product = get_object_or_404(Product, pk=id)
    
    if not (is_admin(request.user) or request.user == product.seller):
        return JsonResponse({
            'status': 'error',
            'message': 'Anda tidak memiliki izin untuk menghapus produk ini.'
        }, status=403)
    
    if request.method == 'POST':
        if product.thumbnail:
            try:
                if os.path.isfile(product.thumbnail.path):
                    os.remove(product.thumbnail.path)
            except:
                pass
        
        product_name = product.name
        product_seller = product.seller.username
        product.delete()
        
        if request.user.is_staff and request.user != product.seller:
            return JsonResponse({
                'status': 'success',
                'message': f'[ADMIN] Produk "{product_name}" milik {product_seller} berhasil dihapus.'
            })
        else:
            return JsonResponse({
                'status': 'success',
                'message': f'Produk "{product_name}" berhasil dihapus.'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
        
@login_required
def edit_product(request, id):
    """Edit product in the shop"""
    product = get_object_or_404(Product, pk=id)

    if not (request.user.is_staff or request.user == product.seller):
        return JsonResponse({
            'status': 'error',
            'message': 'Anda tidak memiliki izin untuk mengedit produk ini.'
        }, status=403)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save()
            
            if request.user.is_staff and request.user != product.seller:
                return JsonResponse({
                    'status': 'success',
                    'message': f'[ADMIN] Produk "{updated_product.name}" milik {product.seller.username} berhasil diupdate.'
                })
            else:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Produk "{updated_product.name}" berhasil diupdate.'
                })
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'category': product.category,
                'price': str(product.price),
                'stock': product.stock,
                'thumbnail': product.thumbnail,
                'seller': product.seller.username
            }
        })
    
    form = ProductForm(instance=product)
    context = {'form': form, 'product': product}
    return render(request, "edit_product.html", context)
    
@login_required
def view_cart(request):
    """View cart items"""
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    items_data = []
    for item in cart_items:
        items_data.append({
            'id': item.id,
            'product': item.product,
            'quantity': item.quantity,
            'subtotal': item.product.price * item.quantity
        })
    
    context = {
        'cart': cart,
        'cart_items': items_data,
        'total': total
    }
    
    return render(request, 'cart_detail.html', context)

@login_required
def add_to_cart(request, product_id):
    """Add product to cart via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    product = get_object_or_404(Product, pk=product_id)
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            message = f'{product.name} quantity updated in cart'
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Cannot add more. Only {product.stock} items in stock'
            })
    else:
        message = f'{product.name} added to cart'
    
    return JsonResponse({'status': 'success', 'message': message})

@login_required
def remove_from_cart(request, product_id):
    """Remove product from cart"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        
        product_name = cart_item.product.name
        cart_item.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'{product_name} removed from cart'
            })
        
        messages.success(request, f'{product_name} removed from cart')
        return redirect('shop:view_cart')
        
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

@login_required
def toggle_wishlist(request, product_id):
    
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(pk=product.pk).exists():
        wishlist.products.remove(product)
        in_wishlist = False
        msg = f'{product.name} removed from wishlist'
        
        referer = request.META.get('HTTP_REFERER', '')
        if 'wishlist' in referer and not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            messages.success(request, msg)
            return redirect('shop:view_wishlist')
    else:
        wishlist.products.add(product)
        in_wishlist = True
        msg = f'{product.name} added to wishlist'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': msg,
            'in_wishlist': in_wishlist,
            'count': wishlist.products.count(),
        })
    
    # Fallback redirect
    return redirect('shop:view_wishlist')

@login_required
def view_wishlist(request):
    """Tampilkan wishlist user (M2M)"""
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products_qs = wishlist.products.all()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        products_data = [
            {
                'id': str(p.id),
                'name': p.name,
                'price': str(p.price),
                'thumbnail': p.thumbnail or '',
                'detail_url': reverse('shop:product_detail', args=[p.id]),
            }
            for p in products_qs
        ]
        return JsonResponse({
            'status': 'success',
            'count': len(products_data),
            'products': products_data
        })

    context = {
        'wishlist': wishlist,
        'products': products_qs,  
    }
    return render(request, 'wishlist_detail.html', context)

@login_required
@transaction.atomic
def checkout(request):
    # Cart user
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = list(CartItem.objects.filter(cart=cart).select_related('product'))
    if not cart_items:
        messages.error(request, 'Keranjang kosong')
        return redirect('shop:view_cart')

    total = sum(ci.product.price * ci.quantity for ci in cart_items)

    if request.method == 'POST':
        qty_map = {}
        for ci in cart_items:
            qty_map[ci.product_id] = qty_map.get(ci.product_id, 0) + ci.quantity

       
        products = list(Product.objects.select_for_update().filter(id__in=qty_map.keys()))

      
        kurang = []
        for p in products:
            if qty_map[p.id] > p.stock:
                kurang.append(f'{p.name} (butuh {qty_map[p.id]}, tersedia {p.stock})')
        if kurang:
            messages.error(request, 'Stok tidak cukup: ' + ', '.join(kurang))
            return redirect('shop:view_cart')

       
        for p in products:
            Product.objects.filter(id=p.id).update(stock=F('stock') - qty_map[p.id])

        
        CartItem.objects.filter(cart=cart).delete()

        total_items = sum(qty_map.values())
        messages.success(request, f'Pembelian berhasil! {total_items} item dengan total harga Rp {total:,.0f}.')
        return redirect('shop:shop')

    
    items_data = [
        {
            'id': ci.id,
            'product': ci.product,
            'quantity': ci.quantity, 
            'subtotal': ci.product.price * ci.quantity
        } for ci in cart_items
    ]
    return render(request, 'order_confirmation.html', {
        'cart_items': items_data,
        'total': total
    })

@login_required
def update_cart_quantity(request, item_id):
    """Update cart item quantity via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        new_quantity = int(data.get('quantity', 1))
        
        if new_quantity < 1:
            return JsonResponse({'status': 'error', 'message': 'Quantity must be at least 1'})
        
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        
        if new_quantity > cart_item.product.stock:
            return JsonResponse({
                'status': 'error', 
                'message': f'Only {cart_item.product.stock} items available in stock'
            })
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
       
        subtotal = cart_item.product.price * cart_item.quantity
        
       
        cart_items = CartItem.objects.filter(cart=cart)
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Quantity updated',
            'subtotal': float(subtotal),
            'total': float(total)
        })
        
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Cart item not found'}, status=404)
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid quantity'}, status=400)


# JSON API endpoints for Flutter app
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import requests
from django.http import HttpResponse


@require_GET
def show_json(request):
    """
    Return list of products as JSON.
    Optional query params:
      category=running|cycling|swimming
      mine=true   (produk milik user login)
    """
    qs = Product.objects.all()

    category = request.GET.get('category')
    if category:
        qs = qs.filter(category=category)

    if request.GET.get('mine') == 'true' and request.user.is_authenticated:
        qs = qs.filter(seller=request.user)

    data = []
    for p in qs:
        data.append({
            'id': str(p.id),
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'stock': p.stock,
            'category': p.category,
            'thumbnail': p.thumbnail or '',
            'seller': p.seller.username if p.seller else None,
        })

    return JsonResponse(data, safe=False)


def show_json_mine(request):
    """Return products owned by the current user as JSON."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    products = Product.objects.filter(seller=request.user)
    data = serializers.serialize('json', products)
    return HttpResponse(data, content_type='application/json')


@csrf_exempt
def create_product_flutter(request):
    """Create a new product from Flutter app via JSON."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
    
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required'}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    name = data.get('name', '').strip()
    price = data.get('price')
    description = data.get('description', '').strip()
    thumbnail = data.get('thumbnail', '').strip()
    category = data.get('category', '').strip()
    stock = data.get('stock', 0)
    
    if not name or not description:
        return JsonResponse({'status': 'error', 'message': 'Name and description required'}, status=400)
    
    try:
        price = float(price) if price else 0
        stock = int(stock) if stock else 0
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid price or stock'}, status=400)
    
    if price <= 0:
        return JsonResponse({'status': 'error', 'message': 'Price must be > 0'}, status=400)
    
    product = Product.objects.create(
        name=name,
        price=price,
        description=description,
        thumbnail=thumbnail or '',
        category=category or 'running',
        stock=stock,
        seller=request.user,
    )
    
    return JsonResponse({
        'status': 'success',
        'message': 'Product created',
        'product_id': str(product.id),
    }, status=201)


def proxy_image(request):
    """Proxy external images to avoid CORS issues in Flutter."""
    url = request.GET.get('url', '')
    if not url:
        return JsonResponse({'error': 'URL parameter required'}, status=400)
    
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return HttpResponse(response.content, content_type=response.headers.get('Content-Type', 'image/jpeg'))
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)