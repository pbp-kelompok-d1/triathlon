import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Ganti ini dengan path ke chromedriver Anda jika tidak ada di PATH
# DRIVER_PATH = 'C:/path/to/chromedriver.exe'

class UserProfileDashboardTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Inisialisasi driver browser SEKALI untuk semua tes di class ini.
        """
        super().setUpClass()
        # Jika chromedriver tidak ada di PATH Anda, gunakan baris di bawah:
        # options = webdriver.ChromeOptions()
        # service = webdriver.ChromeService(executable_path=DRIVER_PATH)
        # cls.driver = webdriver.Chrome(service=service, options=options)
        
        # Jika chromedriver ada di PATH Anda:
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10) 

    @classmethod
    def tearDownClass(cls):
        """
        Tutup browser SEKALI setelah semua tes selesai.
        """
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """
        Setup data yang bersih SEBELUM SETIAP tes.
        """
        # 1. Buat User biasa
        self.user = User.objects.create_user(
            username='testuser', 
            email='testuser@example.com', 
            password='password123'
        )
        self.user.profile.role = 'USER'
        self.user.profile.first_name = 'Test'
        self.user.profile.last_name = 'User'
        self.user.profile.save()

        # 2. Buat Seller
        self.seller = User.objects.create_user(
            username='testseller', 
            email='testseller@example.com', 
            password='password123'
        )
        self.seller.profile.role = 'SELLER'
        self.seller.profile.save()

        # 3. Buat Facility Admin
        self.fac_admin = User.objects.create_user(
            username='testfacadmin', 
            email='testfacadmin@example.com', 
            password='password123'
        )
        self.fac_admin.profile.role = 'FACILITY_ADMIN'
        self.fac_admin.profile.save()
        
        # 4. Buat Admin (untuk tes redirect)
        self.admin = User.objects.create_user(
            username='testadmin', 
            email='testadmin@example.com', 
            password='password123'
        )
        self.admin.profile.role = 'ADMIN'
        self.admin.profile.save()

        # URL Dashboard dari user_profile app
        self.dashboard_url = self.live_server_url + reverse('user_profile:profile')
        
        # URL Login dari main app (SESUAI UPDATE DARI ANDA)
        self.login_url = self.live_server_url + reverse('main:login') 
        
        # URL Halaman utama (guest) dari main app (SESUAI UPDATE DARI ANDA)
        self.main_guest_url_path = reverse('main:show_main')
        
        # URL Halaman utama (logged-in) dari main app (SESUAI UPDATE DARI ANDA)
        self.main_home_url_path = reverse('main:show_home')

    def _login(self, username, password):
        """
        Helper method untuk login.
        Menggunakan 'name' attribute untuk form fields.
        """
        self.driver.get(self.login_url)
        # Menggunakan By.NAME agar cocok dengan request.POST.get('username')
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Tunggu sampai redirect ke 'main:show_home' (SESUAI UPDATE DARI ANDA)
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.main_home_url_path)
        )

    def _login_gagal(self, username, password):
        """
        Helper method untuk tes login gagal.
        """
        self.driver.get(self.login_url)
        self.driver.find_element(By.NAME, 'username').send_keys(username)
        self.driver.find_element(By.NAME, 'password').send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Tunggu sampai pesan error muncul di halaman login
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.login_url) # Pastikan tetap di halaman login
        )
        # Cek pesan error dari view login_user (SESUAI UPDATE DARI ANDA)
        self.assertIn(
            "Sorry, incorrect username or password", 
            self.driver.page_source
        )

    # ============================================
    # TES OTORISASI & ROLE
    # ============================================
    
    # (Tes ini tidak berubah)
    def test_guest_redirected_to_login(self):
        """
        Tes: User yang belum login harus diarahkan ke halaman login.
        """
        self.driver.get(self.dashboard_url)
        
        # Cek apakah kita diarahkan ke URL login
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.login_url)
        )
        self.assertIn(self.login_url, self.driver.current_url)

    # (Tes ini tidak berubah)
    def test_admin_redirected_from_dashboard(self):
        """
        Tes: Admin (role 'ADMIN') harus diarahkan keluar dari dashboard.
        """
        self._login('testadmin', 'password123')
        self.driver.get(self.dashboard_url)
        
        admin_url_path = '/admin/'
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(admin_url_path)
        )
        self.assertIn(admin_url_path, self.driver.current_url)
        self.assertIn("Gunakan panel admin", self.driver.page_source)

    # ============================================
    # TES KONTEN DINAMIS (AJAX)
    # ============================================

    # (Tidak ada perubahan di 3 tes berikutnya)
    def test_user_dashboard_loads_correct_content(self):
        """
        Tes: Login sebagai 'USER', pastikan konten AJAX untuk USER dimuat.
        """
        self._login('testuser', 'password123')
        self.driver.get(self.dashboard_url)
        
        # GANTI '#user-posts-section' dengan ID/Class unik dari template _user_content.html
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'user-posts-section'))
            )
        except TimeoutException:
            self.fail("Konten AJAX User (misal #user-posts-section) tidak ditemukan.")

        self.assertIn("My Wishlist", self.driver.page_source) 
        self.assertNotIn("My Products", self.driver.page_source) 
        self.assertNotIn("Total Revenue", self.driver.page_source) 

    def test_seller_dashboard_loads_correct_content(self):
        """
        Tes: Login sebagai 'SELLER', pastikan konten AJAX untuk SELLER dimuat.
        """
        self._login('testseller', 'password123')
        self.driver.get(self.dashboard_url)
        
        # GANTI '#seller-products-section' dengan ID unik dari _seller_content.html
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'seller-products-section'))
            )
        except TimeoutException:
            self.fail("Konten AJAX Seller (misal #seller-products-section) tidak ditemukan.")

        self.assertIn("My Products", self.driver.page_source)
        self.assertNotIn("My Wishlist", self.driver.page_source)

    def test_facility_admin_dashboard_loads_correct_content(self):
        """
        Tes: Login sebagai 'FACILITY_ADMIN', pastikan konten AJAX untuk FACILITY_ADMIN dimuat.
        """
        self._login('testfacadmin', 'password123')
        self.driver.get(self.dashboard_url)
        
        # GANTI '#facility-stats-section' dengan ID unik dari _facility_admin_content.html
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'facility-stats-section'))
            )
        except TimeoutException:
            self.fail("Konten AJAX Facility Admin (misal #facility-stats-section) tidak ditemukan.")

        self.assertIn("My Facilities", self.driver.page_source)
        self.assertIn("Total Revenue", self.driver.page_source)
        self.assertNotIn("My Wishlist", self.driver.page_source)

    # ============================================
    # TES FUNGSI AJAX (EDIT, PASSWORD, DELETE)
    # ============================================

    # (Tes ini tidak berubah, tergantung ID HTML Anda)
    def test_edit_profile_success(self):
        """
        Tes: Berhasil mengedit profil via AJAX.
        """
        self._login('testuser', 'password123')
        self.driver.get(self.dashboard_url)
        
        nama_awal = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'profile-first-name'))
        ).text
        self.assertEqual(nama_awal, 'Test')

        self.driver.find_element(By.ID, 'edit-profile-button').click()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'edit-profile-modal'))
        )
        
        nama_baru = "EditedName"
        field_nama = self.driver.find_element(By.ID, 'id_edit_first_name')
        field_nama.clear()
        field_nama.send_keys(nama_baru)
        
        self.driver.find_element(By.ID, 'save-profile-button').click()
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-success'))
        )
        
        nama_setelah_edit = self.driver.find_element(By.ID, 'profile-first-name').text
        self.assertEqual(nama_setelah_edit, nama_baru)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, nama_baru)

    # (Tes ini tidak berubah, tergantung ID HTML Anda)
    def test_edit_profile_fail_duplicate_username(self):
        """
        Tes: Gagal mengedit profil jika username sudah ada.
        """
        self._login('testuser', 'password123')
        self.driver.get(self.dashboard_url)
        
        self.driver.find_element(By.ID, 'edit-profile-button').click()
        modal = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'edit-profile-modal'))
        )
        
        # Asumsi ID input username adalah 'id_edit_username'
        field_username = self.driver.find_element(By.ID, 'id_edit_username')
        field_username.clear()
        field_username.send_keys('testseller') # Username ini sudah ada
        
        self.driver.find_element(By.ID, 'save-profile-button').click()
        
        error_msg = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        ).text
        
        self.assertIn("username is already taken", error_msg)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_change_password_success_and_relogin(self):
        """
        Tes: Berhasil ganti password, logout, dan login kembali dengan password baru.
        (DISESUAIKAN DENGAN VIEW LOGIN BARU)
        """
        self._login('testuser', 'password123')
        self.driver.get(self.dashboard_url)
        
        # 1. Buka modal ganti password
        self.driver.find_element(By.ID, 'change-password-button').click()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'change-password-modal'))
        )
        
        # 2. Isi form
        password_baru = 'new_password_456'
        self.driver.find_element(By.ID, 'id_current_password').send_keys('password123')
        self.driver.find_element(By.ID, 'id_new_password').send_keys(password_baru)
        self.driver.find_element(By.ID, 'id_new_password_confirm').send_keys(password_baru)
        
        # 3. Submit
        self.driver.find_element(By.ID, 'save-password-button').click()
        
        # 4. Tunggu pesan sukses
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-success'))
        )
        
        # 5. Logout 
        # (GANTI 'logout-link' dengan ID/link logout Anda)
        # View logout Anda me-redirect ke 'main:show_home', 
        # yang kemudian oleh decorator @login_required akan me-redirect ke login
        self.driver.find_element(By.ID, 'logout-link').click()
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.login_url) # Tunggu sampai di halaman login
        )

        # 6. Coba login dengan password BARU
        self._login('testuser', password_baru)
        # _login helper akan memverifikasi kita sampai di 'main:show_home'
        self.assertIn(self.main_home_url_path, self.driver.current_url)
        
        # 7. Coba login dengan password LAMA (harus gagal)
        self.driver.find_element(By.ID, 'logout-link').click() # Logout lagi
        WebDriverWait(self.driver, 10).until(EC.url_contains(self.login_url))
        
        # Gunakan helper login gagal
        self._login_gagal('testuser', 'password123')

    def test_delete_account_success(self):
        """
        Tes: Berhasil menghapus akun dan diarahkan ke main page (guest).
        (DISESUAIKAN DENGAN VIEW LOGIN/MAIN BARU)
        """
        # 1. Login sebagai user yang akan dihapus
        self._login('testseller', 'password123')
        self.driver.get(self.dashboard_url)
        
        # 2. Buka modal hapus
        self.driver.find_element(By.ID, 'delete-account-button').click()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'delete-account-modal'))
        )

        # 3. Isi konfirmasi password
        self.driver.find_element(By.ID, 'id_password_confirm_delete').send_keys('password123')
        
        # 4. Submit
        self.driver.find_element(By.ID, 'confirm-delete-button').click()
        
        # 5. Tunggu redirect ke main page (guest) 'main:show_main'
        # (Sesuai 'redirect_url' di view delete_user_account Anda)
        WebDriverWait(self.driver, 10).until(
            EC.url_contains(self.main_guest_url_path)
        )
        self.assertIn(self.main_guest_url_path, self.driver.current_url)
        
        # 6. Pastikan user telah terhapus dari DB
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='testseller')

    # (Tes ini tidak berubah, tergantung ID HTML Anda)
    def test_delete_account_fail_wrong_password(self):
        """
        Tes: Gagal hapus akun jika password konfirmasi salah.
        """
        self._login('testuser', 'password123')
        self.driver.get(self.dashboard_url)
        
        self.driver.find_element(By.ID, 'delete-account-button').click()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'delete-account-modal'))
        )

        self.driver.find_element(By.ID, 'id_password_confirm_delete').send_keys('password_salah')
        self.driver.find_element(By.ID, 'confirm-delete-button').click()
        
        error_msg = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        ).text
        
        self.assertIn("Password yang Anda masukkan salah", error_msg)
        self.assertEqual(self.driver.current_url, self.dashboard_url)
        
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)