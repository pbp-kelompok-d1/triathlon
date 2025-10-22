from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import ProductForm
from .models import Product, Cart, CartItem, Wishlist, Order, OrderItem
from django.contrib import messages
from django.urls import reverse
from django.template.defaultfilters import truncatewords
from django.http import HttpResponseBadRequest
import pandas as pd


def load_datasets(request):
    # Load datasets
    products_df = pd.read_csv('https://drive.google.com/file/d/1fsPmjhnXxkk7pY1h7QoNWMNr9TN-h0I_/view?usp=drive_link')
    for data in products_df.itertuples():
        Product.objects.get_or_create(
            name=data.name,
            price=data.price,
            stock=data.stock,
            description=data.description,
            category=data.category,
            thumbnail=data.thumbnail
        )
    # You can load more datasets as needed

    # Convert DataFrame to list of dictionaries
    products_data = products_df.to_dict(orient='records')

    return JsonResponse({'products': products_data})

#@login_required
def add_product(request):
    """Add new product to the shop"""
    form = ProductForm(request.POST or None)

    if request.method == 'POST':
        form = ProductForm(request.POST or None)

        if form.is_valid():
            product_entry = form.save(commit=False)
            if request.user.is_authenticated:
                product_entry.seller = request.user
            product_entry.save()
            
            # Kirim respons sukses sebagai JSON
            return JsonResponse({
                'status': 'success',
                'message': 'Produk berhasil ditambahkan!'
            })
        else:
            # Kirim error validasi form sebagai JSON
            # status=400 (Bad Request) penting agar 'catch' di fetch JS terpicu
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
            
    # Jika method == 'GET', tampilkan halaman form seperti biasa
    form = ProductForm()
    context = {

        'form': form
    }
    return render(request, "add_product.html", context)

def show_product(request):
    filter_type = request.GET.get("filter", "all")
    category_filter = request.GET.get("category", None)

    products = Product.objects.all()

    # Apply filters
    if filter_type == "my" and request.user.is_authenticated:
        products = products.filter(seller=request.user)

    if category_filter:
        products = products.filter(category=category_filter)

    products = products.order_by('-id')

    # AJAX
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
        'last_login': request.COOKIES.get('last_login', 'Never')
    }
    return render(request, "shop.html", context)

def product_detail(request, id):
    """Show individual product detail"""

    product = get_object_or_404(Product, pk=id)

    context = {
        'product': product
    }
    return render(request, "product_detail.html", context)

@login_required
def delete_product(request, id):
    if request.method == 'DELETE':
        try:
            product = get_object_or_404(Product, pk=id)
            if request.user == product.seller:
                product.delete()
                return JsonResponse({'status': 'success', 'message': 'Product deleted successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'You do not have permission to delete this product.'}, status=403)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found.'}, status=404)
        
@login_required
def edit_product(request, id):
    """Edit product in the shop"""
    product = get_object_or_404(Product, pk=id)

    if request.user == product.seller:
        if request.method == 'POST':
            form = ProductForm(request.POST or None, instance=product)
            if form.is_valid():
                form.save()
                return redirect('shop:shop')
        else:
            form = ProductForm(instance=product)
        context = {
            'form': form,
            'product': product
        }
        return render(request, "edit_product.html", context)
    else:
        return JsonResponse({'message': 'You are not authorized to edit this product.'}, status=403)
    

@login_required
def add_to_cart(request, product_id):
    # Dapatkan atau buat keranjang untuk user
    cart = Cart.objects.get_or_create(user=request.user)
    ## Dapatkan atau buat item keranjang
    #cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    #
    ## Jika item sudah ada, tambah jumlahnya
    #if not created:
    #    cart_item.quantity += 1
    #    cart_item.save()
    #    
    #return redirect('shop:product_list')

    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product_id_str = str(product_id)
        
        current_quantity = cart.get(product_id_str, 0)
        if product.stock < current_quantity + 1:
            return JsonResponse({
                'status': 'error',
                'message': f"Stok produk '{product.name}' tidak mencukupi."
            }, status=400) # status 400 Bad Request

        cart[product_id_str] = current_quantity + 1
        request.session['cart'] = cart
        
        return JsonResponse({
            'status': 'success',
            'message': f"Produk '{product.name}' ditambahkan ke keranjang."
        })
    
    return HttpResponseBadRequest("Invalid request method")

@login_required
def view_cart(request):
    cart= Cart.objects.get_or_create(user=request.user)
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    
    cart_items_data = []
    total_price = 0
    
    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total_price += subtotal
        cart_items_data.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })
        
    context = {
        'cart_items': cart_items_data,
        'total_price': total_price,
    }
    return render(request, "cart_detail.html", context)

#@login_required
def remove_from_cart(request, product_id):
    #cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    #cart_item.delete()
    #return redirect('shop:view_cart')
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, "Produk telah dihapus dari keranjang.")
        
    return redirect('shop:view_cart')

#@login_required
def toggle_wishlist(request, product_id):
    #product = get_object_or_404(Product, id=product_id)
    #wishlist, created = Wishlist.objects.get_or_create(user=request.user)
#
    #if product in wishlist.products.all():
    #    wishlist.products.remove(product)
    #else:
    #    wishlist.products.add(product)
    #    
    #return redirect(request.META.get('HTTP_REFERER', 'shop:product_list'))
    if request.method == 'POST':
        wishlist = request.session.get('wishlist', [])
        product_id_str = str(product_id)
        
        if product_id_str in wishlist: # Hapus dari wishlist
            wishlist.remove(product_id_str)
            message = "Produk dihapus dari wishlist."
        else: # Tambah ke wishlist
            wishlist.append(product_id_str)
            message = "Produk ditambahkan ke wishlist."
            
        request.session['wishlist'] = wishlist
        
        return JsonResponse({
            'status': 'success',
            'message': message
        })

    return HttpResponseBadRequest("Invalid request method")

#@login_required
def view_wishlist(request):
    #wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    #return render(request, 'shop/wishlist_detail.html', {'wishlist': wishlist})
    wishlist_ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist_ids)
    
    context = {
        'products': products
    }
    return render(request, "wishlist_detail.html", context)

#@login_required
def checkout(request):
    #cart = get_object_or_404(Cart, user=request.user)
    #if not cart.items.exists():
    #    return redirect('shop:view_cart')
#
    ## Buat Order baru
    #order = Order.objects.create(user=request.user, total_price=cart.get_total_price, is_paid=True) # Anggap langsung lunas
#
    ## Pindahkan item dari keranjang ke OrderItem
    #for item in cart.items.all():
    #    OrderItem.objects.create(
    #        order=order,
    #        product=item.product,
    #        quantity=item.quantity,
    #        price=item.product.price
    #    )
    #    # Kurangi stok produk
    #    item.product.stock -= item.quantity
    #    item.product.save()
#
    ## Kosongkan keranjang
    #cart.items.all().delete()
    #
    #return render(request, 'shop/order_confirmation.html', {'order': order})
    if 'cart' in request.session:
        # Di aplikasi nyata, di sini Anda akan memproses pembayaran 
        # dan mungkin meminta email/alamat pengiriman
        
        # Simulasi pengurangan stok
        cart = request.session.get('cart', {})
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            quantity_purchased = cart[str(product.id)]
            if product.stock >= quantity_purchased:
                product.stock -= quantity_purchased
                product.save()
        
        # Kosongkan keranjang setelah checkout
        del request.session['cart']
    
    # Render halaman konfirmasi
    return render(request, 'order_confirmation.html')


        
 