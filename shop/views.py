from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import ProductForm
from .models import Product

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
