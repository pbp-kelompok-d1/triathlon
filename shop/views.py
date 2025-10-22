from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import ProductForm
from .models import Product, Cart, CartItem, Wishlist, Order, OrderItem
from django.contrib import messages

#@login_required
def add_product(request):
    """Add new product to the shop"""
    form = ProductForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
        product_entry = form.save(commit=False)
        if request.user.is_authenticated:
            product_entry.seller = request.user
        product_entry.save()
        return redirect('shop:shop')
        
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
    

#@login_required
def add_to_cart(request, product_id):
    # Dapatkan atau buat keranjang untuk user
    #cart, created = Cart.objects.get_or_create(user=request.user)
    ## Dapatkan atau buat item keranjang
    #cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    #
    ## Jika item sudah ada, tambah jumlahnya
    #if not created:
    #    cart_item.quantity += 1
    #    cart_item.save()
    #    
    #return redirect('shop:product_list')

    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    current_quantity = cart.get(product_id_str, 0)
    if product.stock < current_quantity + 1:
        messages.error(request, f"Stok produk '{product.name}' tidak mencukupi.")
        return redirect(request.META.get('HTTP_REFERER', 'shop:shop'))

    
    cart[product_id_str] = current_quantity + 1
    
   
    request.session['cart'] = cart
    messages.success(request, f"Produk '{product.name}' ditambahkan ke keranjang.")
    
    return redirect('shop:shop')

#@login_required
def view_cart(request):
    #cart, created = Cart.objects.get_or_create(user=request.user)
    #return render(request, 'shop/cart_detail.html', {'cart': cart})
    cart = request.session.get('cart', {})
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
    wishlist = request.session.get('wishlist', [])

    product_id_str = str(product_id)
    
    if product_id in wishlist:
        wishlist.remove(product_id_str)
        messages.info(request, "Produk dihapus dari wishlist.")
    else:
        wishlist.append(product_id_str)
        messages.success(request, "Produk ditambahkan ke wishlist.")
        
    request.session['wishlist'] = wishlist
    
    return redirect(request.META.get('HTTP_REFERER', 'shop:shop'))

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
        
 