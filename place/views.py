from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Place, Review
from .forms import PlaceForm, ReviewForm

def place_list(request):
    query = request.GET.get('q')
    if query:
        places = Place.objects.filter(name__icontains=query)
    else:
        places = Place.objects.all()
    return render(request, 'place/place_list.html', {'places': places})

def place_detail(request, pk):
    place = get_object_or_404(Place, pk=pk)
    reviews = place.reviews.all().order_by('-created_at')
    return render(request, 'place/place_detail.html', {'place': place, 'reviews': reviews})

@login_required
def add_place(request):
    if request.method == 'POST':
        form = PlaceForm(request.POST)
        if form.is_valid():
            place = form.save(commit=False)
            place.created_by = request.user
            place.save()
            return redirect('place:place_detail', pk=place.pk)
    else:
        form = PlaceForm()
    return render(request, 'place/add_place.html', {'form': form})

@login_required
def add_review(request, pk):
    place = get_object_or_404(Place, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.place = place
            review.user = request.user
            review.save()
            place.update_rating()
            return redirect('place:place_detail', pk=pk)
    else:
        form = ReviewForm()
    return render(request, 'place/add_review.html', {'form': form, 'place': place})
