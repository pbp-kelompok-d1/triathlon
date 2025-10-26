import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth import get_user_model

# Import model dari aplikasi Anda
from .models import UserProfile

# CATATAN: Tes ini mengasumsikan model dari aplikasi lain 
# (ForumPost, Product, Place, dll.) telah didefinisikan di app masing-masing
# dan database telah dimigrasi.

User = get_user_model()

class UserProfileTestBase(TestCase):
    """
    Base class untuk setup data tes yang dipakai berulang.
    Membuat 4 tipe user: USER, SELLER, FACILITY_ADMIN, dan ADMIN.
    """
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.password = 'password123'

        # 1. Buat User 'USER'
        cls.user_user = User.objects.create_user(
            username='testuser', 
            email='user@test.com', 
            password=cls.password
        )
        # Profil dibuat otomatis via signal, role default adalah 'USER'
        cls.user_profile = cls.user_user.profile 

        # 2. Buat User 'SELLER'
        cls.seller_user = User.objects.create_user(
            username='testseller', 
            email='seller@test.com', 
            password=cls.password
        )
        cls.seller_profile = cls.seller_user.profile
        cls.seller_profile.switch_role('SELLER')

        # 3. Buat User 'FACILITY_ADMIN'
        cls.facility_admin_user = User.objects.create_user(
            username='testfacility', 
            email='facility@test.com', 
            password=cls.password
        )
        cls.facility_admin_profile = cls.facility_admin_user.profile
        cls.facility_admin_profile.switch_role('FACILITY_ADMIN')

        # 4. Buat User 'ADMIN'
        cls.admin_user = User.objects.create_user(
            username='testadmin', 
            email='admin@test.com', 
            password=cls.password,
            is_staff=True,
            is_superuser=True
        )
        cls.admin_profile = cls.admin_user.profile
        cls.admin_profile.switch_role('ADMIN')


class TestUserProfileModel(UserProfileTestBase):
    """
    Tes untuk model UserProfile dan signal-nya.
    """
    
    def test_profile_created_on_user_creation(self):
        """Tes signal create_user_profile."""
        new_user = User.objects.create_user(
            username='newuser', 
            password='password123'
        )
        # Cek apakah profil otomatis terbuat
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsInstance(new_user.profile, UserProfile)
        # Cek apakah role default adalah 'USER'
        self.assertEqual(new_user.profile.role, 'USER')

    def test_profile_str_method(self):
        """Tes representasi string __str__."""
        self.assertEqual(
            str(self.user_profile), 
            "testuser - User"
        )
        self.assertEqual(
            str(self.seller_profile), 
            "testseller - Seller"
        )

    def test_role_helper_methods(self):
        """Tes method boolean is_admin, is_seller, dll."""
        self.assertTrue(self.user_profile.is_regular_user())
        self.assertFalse(self.user_profile.is_admin())

        self.assertTrue(self.seller_profile.is_seller())
        self.assertFalse(self.seller_profile.is_regular_user())

        self.assertTrue(self.facility_admin_profile.is_facility_admin())
        self.assertFalse(self.facility_admin_profile.is_seller())

        self.assertTrue(self.admin_profile.is_admin())
        self.assertFalse(self.admin_profile.is_facility_admin())

    def test_switch_role_method(self):
        """Tes fungsionalitas ganti role."""
        profile = self.user_profile
        self.assertEqual(profile.role, 'USER')

        # Tes ganti role yang valid
        success = profile.switch_role('SELLER')
        self.assertTrue(success)
        self.assertEqual(profile.role, 'SELLER')
        self.assertTrue(profile.is_seller())

        # Tes ganti role yang tidak valid
        fail = profile.switch_role('INVALID_ROLE')
        self.assertFalse(fail)
        self.assertEqual(profile.role, 'SELLER') # Role tidak berubah


class TestUserProfileViews(UserProfileTestBase):
    """
    Tes untuk semua view, URL, dan decorator di user_profile.
    """

    # --- Tes View: dashboard_shell_view ---
    
    def test_dashboard_shell_view_logged_out(self):
        """Tes akses /profile/ saat logged out -> redirect ke login."""
        response = self.client.get(reverse('user_profile:profile'))
        self.assertEqual(response.status_code, 302)
        # Asumsi LOGIN_URL Anda adalah 'main:login'
        self.assertRedirects(response, f"{reverse('main:login')}?next={reverse('user_profile:profile')}")

    def test_dashboard_shell_view_as_user(self):
        """Tes akses /profile/ sebagai 'USER'."""
        self.client.login(username='testuser', password=self.password)
        response = self.client.get(reverse('user_profile:profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/dashboard_shell.html')
        self.assertEqual(response.context['user_role'], 'USER')
        self.assertEqual(response.context['initial_view'], 'all') # Cek default view

    def test_dashboard_shell_view_as_admin(self):
        """Tes akses /profile/ sebagai 'ADMIN' -> redirect ke /admin/."""
        self.client.login(username='testadmin', password=self.password)
        response = self.client.get(reverse('user_profile:profile'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/')
    
    # --- Tes View: get_dashboard_content (AJAX) ---

    def test_get_dashboard_content_wrong_role(self):
        """Tes decorator role_required: 'ADMIN' tidak boleh akses."""
        self.client.login(username='testadmin', password=self.password)
        response = self.client.get(reverse('user_profile:get_dashboard_content'))
        
        self.assertEqual(response.status_code, 302)
        # Asumsi redirect ke main page jika role salah
        self.assertRedirects(response, reverse('main:show_main'))

    def test_get_dashboard_content_as_user(self):
        """Tes konten AJAX untuk 'USER'."""
        self.client.login(username='testuser', password=self.password)
        response = self.client.get(reverse('user_profile:get_dashboard_content'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/_user_content.html')

    def test_get_dashboard_content_as_seller(self):
        """Tes konten AJAX untuk 'SELLER'."""
        self.client.login(username='testseller', password=self.password)
        response = self.client.get(reverse('user_profile:get_dashboard_content'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/_seller_content.html')

    def test_get_dashboard_content_as_facility_admin(self):
        """Tes konten AJAX untuk 'FACILITY_ADMIN'."""
        self.client.login(username='testfacility', password=self.password)
        response = self.client.get(reverse('user_profile:get_dashboard_content'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_profile/_facility_admin_content.html')

    # --- Tes View: edit_profile (AJAX) ---
    
    def test_edit_profile_get_request(self):
        """Tes GET request ke edit_profile -> redirect ke profile."""
        self.client.login(username='testuser', password=self.password)
        response = self.client.get(reverse('user_profile:edit_profile'))
        self.assertRedirects(response, reverse('user_profile:profile'))

    def test_edit_profile_post_ajax_success(self):
        """Tes update profil via AJAX POST yang sukses."""
        self.client.login(username='testuser', password=self.password)
        
        new_data = {
            'username': 'new_username',
            'email': 'new.email@test.com',
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'phone_number': '08123456789',
            'bio': 'Ini adalah bio baru.'
        }
        
        response = self.client.post(
            reverse('user_profile:edit_profile'),
            new_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertTrue(response_json['success'])
        self.assertEqual(response_json['username'], 'new_username')
        self.assertEqual(response_json['bio'], 'Ini adalah bio baru.')
        
        # Cek data di database
        self.user_user.refresh_from_db()
        self.user_profile.refresh_from_db()
        
        self.assertEqual(self.user_user.username, 'new_username')
        self.assertEqual(self.user_user.first_name, 'NewFirst')
        self.assertEqual(self.user_profile.phone_number, '08123456789')
        self.assertEqual(self.user_profile.bio, 'Ini adalah bio baru.')

    def test_edit_profile_post_ajax_duplicate_username(self):
        """Tes update profil gagal (duplicate username)."""
        self.client.login(username='testuser', password=self.password)
        
        invalid_data = {
            'username': 'testseller', # Username ini sudah dipakai
            'email': 'new.email@test.com',
        }
        
        response = self.client.post(
            reverse('user_profile:edit_profile'),
            invalid_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        response_json = response.json()
        self.assertFalse(response_json['success'])
        self.assertIn('username is already taken', response_json['error'])

    # --- Tes View: change_password (AJAX) ---

    def test_change_password_ajax_success(self):
        """Tes ganti password via AJAX POST yang sukses."""
        self.client.login(username='testuser', password=self.password)
        
        pass_data = {
            'current_password': self.password,
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456',
        }
        
        response = self.client.post(
            reverse('user_profile:change_password'),
            pass_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Cek password baru
        self.user_user.refresh_from_db()
        self.assertTrue(self.user_user.check_password('newpassword456'))

    def test_change_password_ajax_wrong_current(self):
        """Tes ganti password gagal (password lama salah)."""
        self.client.login(username='testuser', password=self.password)
        
        pass_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456',
        }
        
        response = self.client.post(
            reverse('user_profile:change_password'),
            pass_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('current password was entered incorrectly', response.json()['error'])

    def test_change_password_ajax_mismatch(self):
        """Tes ganti password gagal (password baru tidak cocok)."""
        self.client.login(username='testuser', password=self.password)
        
        pass_data = {
            'current_password': self.password,
            'new_password': 'newpassword456',
            'new_password_confirm': 'mismatch456',
        }
        
        response = self.client.post(
            reverse('user_profile:change_password'),
            pass_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('New passwords do not match', response.json()['error'])

    # --- Tes View: delete_user_account (AJAX) ---

    def test_delete_account_ajax_success(self):
        """Tes hapus akun via AJAX POST yang sukses."""
        # Buat user baru khusus untuk tes ini agar tidak merusak tes lain
        user_to_delete = User.objects.create_user(
            username='deleteme', 
            email='delete@me.com', 
            password=self.password
        )
        user_id = user_to_delete.id
        
        self.client.login(username='deleteme', password=self.password)
        
        response = self.client.post(
            reverse('user_profile:delete_account'),
            {'password_confirm_delete': self.password},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertTrue(response_json['success'])
        # Cek URL redirect sudah benar
        self.assertEqual(response_json['redirect_url'], reverse('main:show_main'))
        
        # Cek apakah user benar-benar terhapus
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user_id)
            
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(UserProfile.objects.filter(user_id=user_id).exists())


    def test_delete_account_ajax_wrong_password(self):
        """Tes hapus akun gagal (konfirmasi password salah)."""
        user_id = self.user_user.id
        self.client.login(username='testuser', password=self.password)
        
        response = self.client.post(
            reverse('user_profile:delete_account'),
            {'password_confirm_delete': 'wrongpassword'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        response_json = response.json()
        self.assertFalse(response_json['success'])
        self.assertIn('Password yang Anda masukkan salah', response.json()['error'])
        
        # Pastikan user TIDAK terhapus
        self.assertTrue(User.objects.filter(id=user_id).exists())
    
    def test_role_required_user_without_profile(self):
        """Tes user login tapi tidak punya profil (misal, profil terhapus)."""
        # Buat user baru
        user_no_profile = User.objects.create_user(
            username='nouserprofile', 
            password=self.password
        )
        
        # Hapus profilnya secara manual untuk simulasi error
        try:
            user_no_profile.profile.delete()
        except UserProfile.DoesNotExist:
            pass # Profil mungkin sudah terhapus atau tidak terbuat

        # Login sebagai user tersebut
        self.client.login(username='nouserprofile', password=self.password)
        
        # Coba akses view yang dilindungi
        response = self.client.get(reverse('user_profile:get_dashboard_content'))
        
        # Harusnya redirect ke main (sesuai logika decorator)
        self.assertRedirects(response, reverse('main:show_main'))
    
    def test_dashboard_shell_view_with_get_params(self):
        """Tes /profile/ dengan parameter ?view=custom&category=test"""
        self.client.login(username='testuser', password=self.password)
        
        # Panggil URL dengan parameter GET
        response = self.client.get(reverse('user_profile:profile') + '?view=custom_view&category=test_cat')
        
        self.assertEqual(response.status_code, 200)
        
        # Cek apakah context di-passing dengan benar
        self.assertEqual(response.context['initial_view'], 'custom_view')
        self.assertEqual(response.context['initial_category'], 'test_cat')
    
    def test_edit_profile_post_ajax_empty_username(self):
        """Tes update profil gagal (username kosong)."""
        self.client.login(username='testuser', password=self.password)
        invalid_data = {'username': '', 'email': 'new.email@test.com'}
        
        response = self.client.post(
            reverse('user_profile:edit_profile'),
            invalid_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('Username cannot be empty', response.json()['error'])

    def test_edit_profile_post_ajax_duplicate_email(self):
        """Tes update profil gagal (email duplikat)."""
        self.client.login(username='testuser', password=self.password)
        # 'testseller' sudah ada dan punya email 'seller@test.com'
        invalid_data = {'username': 'testuser', 'email': 'seller@test.com'}
        
        response = self.client.post(
            reverse('user_profile:edit_profile'),
            invalid_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('email is already in use', response.json()['error'])

    def test_edit_profile_post_NON_AJAX(self):
        """Tes update profil via POST biasa (non-AJAX) -> harusnya redirect."""
        self.client.login(username='testuser', password=self.password)
        new_data = {'username': 'new_username_non_ajax', 'email': 'new@email.com'}
        
        # Panggil POST tanpa header AJAX
        response = self.client.post(reverse('user_profile:edit_profile'), new_data)
        
        # Harusnya redirect kembali ke halaman profile
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_profile:profile'))

    def test_change_password_ajax_weak_password(self):
        """Tes ganti password gagal (password baru terlalu lemah/umum)."""
        self.client.login(username='testuser', password=self.password)
        
        pass_data = {
            'current_password': self.password,
            'new_password': '123', # Password terlalu umum
            'new_password_confirm': '123',
        }
        
        response = self.client.post(
            reverse('user_profile:change_password'),
            pass_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        # Cek apakah ada pesan error dari validate_password
        self.assertIn('too common', response.json()['error'])

    def test_change_password_ajax_empty_new_password(self):
        """Tes ganti password gagal (password baru kosong)."""
        self.client.login(username='testuser', password=self.password)
        
        pass_data = {
            'current_password': self.password,
            'new_password': '', # Password baru kosong
            'new_password_confirm': '',
        }
        
        response = self.client.post(
            reverse('user_profile:change_password'),
            pass_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('New password cannot be empty', response.json()['error'])
