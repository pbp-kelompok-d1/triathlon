# place/tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import json
import tempfile
from PIL import Image
import io

from .models import Place, Review
from .forms import PlaceForm
from main.models import UserProfile


class PlaceModelTest(TestCase):
    """Test Place Model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_place(self):
        """Test creating a place"""
        place = Place.objects.create(
            name='Test Swimming Pool',
            description='A great pool',
            city='Jakarta',
            province='DKI Jakarta',
            genre='Swimming Pool',
            price=Decimal('50000.00'),
            admin=self.user
        )
        
        self.assertEqual(place.name, 'Test Swimming Pool')
        self.assertEqual(place.genre, 'Swimming Pool')
        self.assertEqual(place.price, Decimal('50000.00'))
        self.assertEqual(str(place), 'Test Swimming Pool')
        
    def test_place_with_null_fields(self):
        """Test place with optional null fields"""
        place = Place.objects.create(
            name='Minimal Place',
            price=Decimal('0.00')
        )
        
        self.assertIsNone(place.description)
        self.assertIsNone(place.city)
        self.assertIsNone(place.province)
        self.assertIsNone(place.genre)
        self.assertIsNone(place.admin)


class ReviewModelTest(TestCase):
    """Test Review Model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='reviewer',
            password='reviewpass123'
        )
        self.place = Place.objects.create(
            name='Pool for Review',
            price=Decimal('25000.00')
        )
        
    def test_create_review(self):
        """Test creating a review"""
        review = Review.objects.create(
            place=self.place,
            user=self.user,
            rating=5,
            comment='Excellent pool!'
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent pool!')
        self.assertEqual(str(review), f'{self.user.username} - {self.place.name}')
        
    def test_review_rating_validation(self):
        """Test rating validators"""
        # Valid ratings
        for rating in [1, 2, 3, 4, 5]:
            review = Review(
                place=self.place,
                user=self.user,
                rating=rating
            )
            review.full_clean()  # Should not raise
            
    def test_review_cascade_delete(self):
        """Test review deleted when place deleted"""
        review = Review.objects.create(
            place=self.place,
            user=self.user,
            rating=4,
            comment='Good'
        )
        
        place_id = self.place.id
        self.place.delete()
        
        # Review should be deleted
        self.assertFalse(Review.objects.filter(id=review.id).exists())


class PlaceFormTest(TestCase):
    """Test PlaceForm"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'name': 'New Pool',
            'description': 'Nice pool',
            'city': 'Bandung',
            'province': 'Jawa Barat',
            'genre': 'Swimming Pool',
            'price': '30000'
        }
        form = PlaceForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_form_missing_name(self):
        """Test form without required name"""
        form_data = {
            'price': '10000'
        }
        form = PlaceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
    def test_form_with_image(self):
        """Test form with image upload"""
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            'test_image.jpg',
            image_file.read(),
            content_type='image/jpeg'
        )
        
        form_data = {
            'name': 'Pool with Image',
            'price': '15000'
        }
        form = PlaceForm(data=form_data, files={'image': uploaded_file})
        self.assertTrue(form.is_valid())


class PlaceListViewTest(TestCase):
    """Test place_list view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Create profile for user
        UserProfile.objects.create(user=self.user, role='USER')
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass'
        )
        UserProfile.objects.create(user=self.admin_user, role='ADMIN')
        
        # Create test places
        for i in range(5):
            Place.objects.create(
                name=f'Pool {i}',
                city='Jakarta',
                province='DKI Jakarta',
                genre='Swimming Pool',
                price=Decimal(f'{10000 + i * 5000}.00'),
                admin=self.user
            )
            
    def test_place_list_requires_login(self):
        """Test place list requires authentication"""
        response = self.client.get(reverse('place:place_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_place_list_authenticated(self):
        """Test authenticated user can access place list"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('place:place_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pool 0')
        self.assertTemplateUsed(response, 'place/place_list.html')
        
    def test_place_list_search(self):
        """Test search functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('place:place_list'), {'q': 'Pool 2'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pool 2')
        
    def test_place_list_genre_filter(self):
        """Test genre filtering"""
        # Create place with different genre
        Place.objects.create(
            name='Running Track 1',
            genre='Running Track',
            price=Decimal('5000.00')
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('place:place_list'),
            {'genre': 'Running Track'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Running Track 1')
        
    def test_place_list_my_places_filter(self):
        """Test 'My Places' filter"""
        other_user = User.objects.create_user(username='other', password='pass')
        Place.objects.create(
            name='Other User Pool',
            price=Decimal('20000.00'),
            admin=other_user
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('place:place_list'),
            {'filter': 'my_places'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Other User Pool')
        
    def test_place_list_ajax_request(self):
        """Test AJAX request returns partial template"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('place:place_list'),
            {'ajax': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'place/partials/venue_cards.html')


class AddPlaceViewTest(TestCase):
    """Test add_place view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='facility_admin',
            password='adminpass'
        )
        UserProfile.objects.create(user=self.user, role='FACILITY_ADMIN')
        
        self.regular_user = User.objects.create_user(
            username='regular',
            password='regularpass'
        )
        UserProfile.objects.create(user=self.regular_user, role='USER')
        
    def test_add_place_requires_login(self):
        """Test add place requires authentication"""
        response = self.client.get(reverse('place:add_place'))
        self.assertEqual(response.status_code, 302)
        
    def test_add_place_permission_denied_regular_user(self):
        """Test regular user cannot add place"""
        self.client.login(username='regular', password='regularpass')
        response = self.client.get(reverse('place:add_place'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
    def test_add_place_get_form(self):
        """Test GET request shows form"""
        self.client.login(username='facility_admin', password='adminpass')
        response = self.client.get(reverse('place:add_place'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], PlaceForm)
        
    def test_add_place_post_valid(self):
        """Test POST with valid data creates place"""
        self.client.login(username='facility_admin', password='adminpass')
        
        data = {
            'name': 'New Swimming Pool',
            'description': 'A fantastic pool',
            'city': 'Surabaya',
            'province': 'Jawa Timur',
            'genre': 'Swimming Pool',
            'price': '40000'
        }
        
        response = self.client.post(reverse('place:add_place'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(Place.objects.filter(name='New Swimming Pool').exists())
        
        place = Place.objects.get(name='New Swimming Pool')
        self.assertEqual(place.admin, self.user)


class PlaceDetailViewTest(TestCase):
    """Test place_detail view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user, role='USER')
        
        self.place = Place.objects.create(
            name='Test Pool',
            description='Nice pool',
            city='Jakarta',
            price=Decimal('25000.00'),
            admin=self.user
        )
        
        # Create reviews
        for i in range(3):
            reviewer = User.objects.create_user(
                username=f'reviewer{i}',
                password='pass'
            )
            Review.objects.create(
                place=self.place,
                user=reviewer,
                rating=4 + (i % 2),
                comment=f'Review {i}'
            )
            
    def test_place_detail_requires_login(self):
        """Test place detail requires authentication"""
        response = self.client.get(
            reverse('place:place_detail', args=[self.place.pk])
        )
        self.assertEqual(response.status_code, 302)
        
    def test_place_detail_authenticated(self):
        """Test authenticated user can view details"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('place:place_detail', args=[self.place.pk])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Pool')
        self.assertContains(response, 'Nice pool')
        self.assertEqual(len(response.context['reviews']), 3)
        
    def test_place_detail_is_owner(self):
        """Test is_place_owner flag"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('place:place_detail', args=[self.place.pk])
        )
        
        self.assertTrue(response.context['is_place_owner'])
        
    def test_place_detail_not_found(self):
        """Test 404 for non-existent place"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('place:place_detail', args=[99999])
        )
        
        self.assertEqual(response.status_code, 404)


class AddReviewViewTest(TestCase):
    """Test add_review view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.place = Place.objects.create(
            name='Pool for Review',
            price=Decimal('15000.00')
        )
        
    def test_add_review_requires_authentication(self):
        """Test unauthenticated user cannot add review"""
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data=json.dumps({'rating': 5, 'comment': 'Great!'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
    def test_add_review_valid(self):
        """Test adding valid review"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data=json.dumps({
                'rating': 5,
                'comment': 'Excellent pool!'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['rating'], 5)
        
        # Verify review created
        self.assertTrue(
            Review.objects.filter(
                place=self.place,
                user=self.user,
                rating=5
            ).exists()
        )
        
    def test_add_review_missing_rating(self):
        """Test error when rating missing"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data=json.dumps({'comment': 'No rating'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
    def test_add_review_invalid_rating(self):
        """Test error with invalid rating"""
        self.client.login(username='testuser', password='testpass123')
        
        # Rating too high
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data=json.dumps({'rating': 6, 'comment': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Rating too low
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data=json.dumps({'rating': 0, 'comment': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
    def test_add_review_duplicate(self):
        """Test cannot add duplicate review"""
        self.client.login(username='testuser', password='testpass123')
        
        # First review
        Review.objects.create(
            place=self.place,
            user=self.user,
            rating=4,
            comment='First review'
        )
        
        # Try to add second review
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data=json.dumps({'rating': 5, 'comment': 'Second review'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('sudah', data['error'].lower())
        
    def test_add_review_invalid_json(self):
        """Test error with invalid JSON"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('place:add_review', args=[self.place.pk]),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class DeleteReviewViewTest(TestCase):
    """Test delete_review view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='reviewer',
            password='reviewpass'
        )
        UserProfile.objects.create(user=self.user, role='USER')
        
        self.other_user = User.objects.create_user(
            username='other',
            password='otherpass'
        )
        
        self.place = Place.objects.create(
            name='Pool',
            price=Decimal('10000.00')
        )
        
        self.review = Review.objects.create(
            place=self.place,
            user=self.user,
            rating=4,
            comment='My review'
        )
        
    def test_delete_review_requires_authentication(self):
        """Test unauthenticated user cannot delete"""
        response = self.client.post(
            reverse('place:delete_review', args=[self.review.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_delete_review_success(self):
        """Test owner can delete review"""
        self.client.login(username='reviewer', password='reviewpass')
        
        response = self.client.post(
            reverse('place:delete_review', args=[self.review.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify review deleted
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())
        
    def test_delete_review_permission_denied(self):
        """Test other user cannot delete review"""
        self.client.login(username='other', password='otherpass')
        
        response = self.client.post(
            reverse('place:delete_review', args=[self.review.id])
        )
        
        self.assertEqual(response.status_code, 403)
        
        # Review should still exist
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())


class EditPlaceViewTest(TestCase):
    """Test edit_place view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner',
            password='ownerpass'
        )
        UserProfile.objects.create(user=self.user, role='FACILITY_ADMIN')
        
        self.other_user = User.objects.create_user(
            username='other',
            password='otherpass'
        )
        UserProfile.objects.create(user=self.other_user, role='FACILITY_ADMIN')
        
        self.place = Place.objects.create(
            name='Original Name',
            description='Original desc',
            price=Decimal('20000.00'),
            admin=self.user
        )
        
    def test_edit_place_get(self):
        """Test GET shows edit form"""
        self.client.login(username='owner', password='ownerpass')
        response = self.client.get(
            reverse('place:edit_place', args=[self.place.pk])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], PlaceForm)
        self.assertEqual(response.context['place'], self.place)
        
    def test_edit_place_post_valid(self):
        """Test POST with valid data updates place"""
        self.client.login(username='owner', password='ownerpass')
        
        data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'city': 'Bandung',
            'province': 'Jawa Barat',
            'genre': 'Running Track',
            'price': '30000'
        }
        
        response = self.client.post(
            reverse('place:edit_place', args=[self.place.pk]),
            data
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.place.refresh_from_db()
        self.assertEqual(self.place.name, 'Updated Name')
        self.assertEqual(self.place.description, 'Updated description')
        
    def test_edit_place_permission_denied(self):
        """Test other user cannot edit place"""
        self.client.login(username='other', password='otherpass')
        
        response = self.client.get(
            reverse('place:edit_place', args=[self.place.pk])
        )
        
        self.assertEqual(response.status_code, 403)


class DeletePlaceViewTest(TestCase):
    """Test delete_place view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='owner',
            password='ownerpass'
        )
        UserProfile.objects.create(user=self.user, role='FACILITY_ADMIN')
        
        self.place = Place.objects.create(
            name='To Delete',
            price=Decimal('10000.00'),
            admin=self.user
        )
        
    def test_delete_place_post(self):
        """Test POST deletes place"""
        self.client.login(username='owner', password='ownerpass')
        
        response = self.client.post(
            reverse('place:delete_place', args=[self.place.pk])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Place.objects.filter(id=self.place.pk).exists())


class HelperFunctionsTest(TestCase):
    """Test helper functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='pass'
        )
        
    def test_is_admin(self):
        """Test is_admin helper"""
        from place.views import is_admin
        
        UserProfile.objects.create(user=self.user, role='ADMIN')
        self.assertTrue(is_admin(self.user))
        
        self.user.profile.role = 'USER'
        self.user.profile.save()
        self.assertFalse(is_admin(self.user))
        
    def test_is_facility_admin(self):
        """Test is_facility_admin helper"""
        from place.views import is_facility_admin
        
        UserProfile.objects.create(user=self.user, role='FACILITY_ADMIN')
        self.assertTrue(is_facility_admin(self.user))
        
    def test_is_admin_or_facility_admin(self):
        """Test is_admin_or_facility_admin helper"""
        from place.views import is_admin_or_facility_admin
        
        UserProfile.objects.create(user=self.user, role='ADMIN')
        self.assertTrue(is_admin_or_facility_admin(self.user))
        
        self.user.profile.role = 'FACILITY_ADMIN'
        self.user.profile.save()
        self.assertTrue(is_admin_or_facility_admin(self.user))
        
        self.user.profile.role = 'USER'
        self.user.profile.save()
        self.assertFalse(is_admin_or_facility_admin(self.user))