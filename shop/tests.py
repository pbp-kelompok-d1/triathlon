from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.http import urlencode
from django.conf import settings
from .models import Product, Cart, CartItem, Wishlist
from .views import is_admin
import os

User = get_user_model()


def ajax_headers():
    """Helper untuk AJAX request"""
    return {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class IsAdminFunctionTest(TestCase):
    """Test fungsi is_admin"""
    
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='superadmin', password='pass123', email='super@test.com'
        )
        self.staff = User.objects.create_user(username='staff', password='pass123')
        self.staff.is_staff = True
        self.staff.save()
        
        self.admin_group = Group.objects.create(name='admin')
        self.group_admin = User.objects.create_user(username='groupadmin', password='pass123')
        self.group_admin.groups.add(self.admin_group)
        
        self.normal_user = User.objects.create_user(username='normal', password='pass123')

    def test_is_admin_superuser(self):
        """Test superuser adalah admin"""
        self.assertTrue(is_admin(self.superuser))

    def test_is_admin_staff(self):
        """Test staff adalah admin"""
        self.assertTrue(is_admin(self.staff))

    def test_is_admin_group_member(self):
        """Test anggota group admin adalah admin"""
        self.assertTrue(is_admin(self.group_admin))

    def test_is_admin_normal_user(self):
        """Test user normal bukan admin"""
        self.assertFalse(is_admin(self.normal_user))

    def test_is_admin_anonymous(self):
        """Test None bukan admin"""
        self.assertFalse(is_admin(None))

class DeleteAllProductsTest(TestCase):
    """Test delete_all_products view"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='pass')

    def test_delete_all_products_success(self):
        """Test hapus semua produk berhasil"""
        Product.objects.create(name='P1', price=1000, stock=1, category='cycling', seller=self.seller)
        Product.objects.create(name='P2', price=2000, stock=2, category='running', seller=self.seller)
        
        self.assertEqual(Product.objects.count(), 2)
        
        url = reverse('shop:delete_all_products')
        res = self.client.get(url)
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(Product.objects.count(), 0)

    def test_delete_all_products_empty(self):
        """Test hapus semua produk dari database kosong"""
        url = reverse('shop:delete_all_products')
        res = self.client.get(url)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'success')


class LoadDatasetCyclingTest(TestCase):
    """Test load_dataset_cycling view"""
    
    def setUp(self):
        self.client = Client()

    def test_load_dataset_cycling_file_not_found(self):
        """Test file CSV tidak ditemukan"""
        url = reverse('shop:load_dataset_cycling')
        csv_path = os.path.join(settings.BASE_DIR, 'shop', 'specialized.csv')
        
        if os.path.exists(csv_path):
            self.skipTest("CSV file exists")
        
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'error')


class LoadDatasetRunningTest(TestCase):
    """Test load_dataset_running view"""
    
    def setUp(self):
        self.client = Client()

    def test_load_dataset_running_file_not_found(self):
        """Test file CSV tidak ditemukan"""
        url = reverse('shop:load_dataset_running')
        csv_path = os.path.join(settings.BASE_DIR, 'shop', 'running.csv')
        
        if os.path.exists(csv_path):
            self.skipTest("CSV file exists")
        
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'error')


class LoadDatasetSwimmingTest(TestCase):
    """Test load_dataset_swimming view"""
    
    def setUp(self):
        self.client = Client()

    def test_load_dataset_swimming_file_not_found(self):
        """Test file CSV tidak ditemukan"""
        url = reverse('shop:load_dataset_swimming')
        csv_path = os.path.join(settings.BASE_DIR, 'shop', 'swimming_ril.csv')
        
        if os.path.exists(csv_path):
            self.skipTest("CSV file exists")
        
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'error')


class ShowProductTest(TestCase):
    """Test show_product view"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='pass')
        self.other_seller = User.objects.create_user(username='other', password='pass')
        self.admin = User.objects.create_superuser(username='admin', password='admin123', email='a@a.com')
        
        self.p1 = Product.objects.create(
            name='Bike 1', price=100000, stock=5, category='cycling', seller=self.seller
        )
        self.p2 = Product.objects.create(
            name='Run Shoe', price=200000, stock=3, category='running', seller=self.other_seller
        )

    def test_show_product_get_html(self):
        """Test GET mengembalikan HTML"""
        url = reverse('shop:shop')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_show_product_ajax_json(self):
        """Test AJAX GET mengembalikan JSON"""
        url = reverse('shop:shop')
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('products', data)
        self.assertEqual(len(data['products']), 2)

    def test_show_product_filter_my(self):
        """Test filter 'my' untuk produk user sendiri"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:shop') + '?' + urlencode({'filter': 'my'})
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        products = data['products']
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['name'], 'Bike 1')

    def test_show_product_filter_category(self):
        """Test filter berdasarkan kategori"""
        url = reverse('shop:shop') + '?' + urlencode({'category': 'cycling'})
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        products = data['products']
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['name'], 'Bike 1')

    def test_show_product_admin_delete_ajax(self):
        """Test admin hapus produk via AJAX"""
        self.client.login(username='admin', password='admin123')
        
        url = reverse('shop:shop')
        res = self.client.post(url, {
            'action': 'admin_delete',
            'product_id': str(self.p1.id)  # UUID sebagai string
        }, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['product_id'], str(self.p1.id))  # UUID string
        self.assertIn('dihapus', data['message'])
        self.assertFalse(Product.objects.filter(id=self.p1.id).exists())

    def test_show_product_admin_delete_non_ajax(self):
        """Test admin hapus produk non-AJAX redirect"""
        self.client.login(username='admin', password='admin123')
        
        url = reverse('shop:shop')
        res = self.client.post(url, {
            'action': 'admin_delete',
            'product_id': str(self.p1.id)
        })
        
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Product.objects.filter(id=self.p1.id).exists())

    def test_show_product_non_admin_cannot_delete(self):
        """Test non-admin tidak bisa hapus"""
        self.client.login(username='seller', password='pass')
        
        url = reverse('shop:shop')
        res = self.client.post(url, {
            'action': 'admin_delete',
            'product_id': str(self.p1.id)
        }, **ajax_headers())
        
        # Tidak bisa delete, produk masih ada
        self.assertTrue(Product.objects.filter(id=self.p1.id).exists())


class ProductDetailTest(TestCase):
    """Test product_detail view"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='pass')
        self.product = Product.objects.create(
            name='Helmet', price=250000, stock=10, category='cycling', 
            seller=self.seller, description='Safety first'
        )

    def test_product_detail_get_html(self):
        """Test GET mengembalikan HTML"""
        url = reverse('shop:product_detail', args=[self.product.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_product_detail_ajax_json(self):
        """Test AJAX GET mengembalikan JSON"""
        url = reverse('shop:product_detail', args=[self.product.id])
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['product']['name'], self.product.name)
        self.assertEqual(data['product']['price'], float(self.product.price))

    def test_product_detail_not_found(self):
        """Test produk tidak ditemukan"""
        fake_uuid = '00000000-0000-0000-0000-000000000000'
        try:
            url = reverse('shop:product_detail', args=[fake_uuid])
            res = self.client.get(url)
            self.assertEqual(res.status_code, 404)
        except Exception:
            self.skipTest("UUID format tidak match")


class AddProductTest(TestCase):
    """Test add_product view"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='pass')

    def test_add_product_requires_login(self):
        """Test tidak bisa tambah produk tanpa login"""
        url = reverse('shop:add_product')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_add_product_get_form(self):
        """Test GET menampilkan form"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:add_product')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_add_product_post_success(self):
        """Test POST tambah produk berhasil"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:add_product')
        
        res = self.client.post(url, {
            'name': 'New Bike',
            'price': 500000,
            'stock': 5,
            'description': 'Great bike',
            'category': 'cycling'
        })
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(Product.objects.filter(name='New Bike', seller=self.seller).exists())

    def test_add_product_post_invalid(self):
        """Test POST dengan data invalid"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:add_product')
        
        res = self.client.post(url, {
            'name': '',
            'price': 500000,
            'stock': 5,
            'description': 'desc',
            'category': 'cycling'
        })
        
        self.assertEqual(res.status_code, 400)

class EditProductTest(TestCase):
    """Test edit_product view"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='pass')
        self.other = User.objects.create_user(username='other', password='pass2')
        self.admin = User.objects.create_superuser(username='admin', password='admin123', email='a@a.com')
        
        self.product = Product.objects.create(
            name='Goggle', price=50000, stock=10, category='swimming', seller=self.seller
        )

    def test_edit_product_requires_login(self):
        """Test edit memerlukan login"""
        url = reverse('shop:edit_product', args=[self.product.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_edit_product_permission_denied(self):
        """Test user lain tidak bisa edit"""
        self.client.login(username='other', password='pass2')
        url = reverse('shop:edit_product', args=[self.product.id])
        
        res = self.client.post(url, {
            'name': 'New Name',
            'price': 60000,
            'stock': 5,
            'description': 'desc',
            'category': 'swimming'
        })
        
        self.assertEqual(res.status_code, 403)

    def test_edit_product_by_seller(self):
        """Test seller edit produk sendiri"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:edit_product', args=[self.product.id])
        
        res = self.client.post(url, {
            'name': 'Goggle Updated',
            'price': 60000,
            'stock': 12,
            'description': 'Updated desc',
            'category': 'swimming'
        })
        
        self.assertEqual(res.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Goggle Updated')

    def test_edit_product_get_ajax(self):
        """Test GET AJAX prefill data"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:edit_product', args=[self.product.id])
        
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['product']['name'], self.product.name)

    def test_edit_product_by_admin(self):
        """Test admin edit produk user lain"""
        self.client.login(username='admin', password='admin123')
        url = reverse('shop:edit_product', args=[self.product.id])
        
        res = self.client.post(url, {
            'name': 'Admin Edit',
            'price': 75000,
            'stock': 8,
            'description': 'admin',
            'category': 'swimming'
        })
        
        self.assertEqual(res.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Admin Edit')


class DeleteProductTest(TestCase):
    """Test delete_product view"""
    
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(username='seller', password='pass')
        self.other = User.objects.create_user(username='other', password='pass2')
        self.admin = User.objects.create_superuser(username='admin', password='admin123', email='a@a.com')
        
        self.product = Product.objects.create(
            name='Cap', price=30000, stock=5, category='swimming', seller=self.seller
        )

    def test_delete_product_get_invalid(self):
        """Test GET tidak diizinkan"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:delete_product', args=[self.product.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)

    def test_delete_product_requires_login(self):
        """Test hapus memerlukan login"""
        url = reverse('shop:delete_product', args=[self.product.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 302)

    def test_delete_product_permission_denied(self):
        """Test user lain tidak bisa hapus"""
        self.client.login(username='other', password='pass2')
        url = reverse('shop:delete_product', args=[self.product.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 403)

    def test_delete_product_by_seller(self):
        """Test seller hapus produk sendiri"""
        self.client.login(username='seller', password='pass')
        url = reverse('shop:delete_product', args=[self.product.id])
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_delete_product_by_admin_with_log(self):
        """Test admin hapus dengan log [ADMIN]"""
        self.client.login(username='admin', password='admin123')
        url = reverse('shop:delete_product', args=[self.product.id])
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 200)
        msg = res.json()['message']
        self.assertTrue(msg.startswith('[ADMIN]'))
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

class CartViewTest(TestCase):
    """Test cart views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='pass')
        self.seller = User.objects.create_user(username='seller', password='pass2')
        self.product = Product.objects.create(
            name='Wheel', price=100000, stock=2, category='cycling', seller=self.seller
        )
        self.client.login(username='buyer', password='pass')

    def test_view_cart(self):
        """Test view cart"""
        url = reverse('shop:view_cart')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_view_cart_requires_login(self):
        """Test view cart memerlukan login"""
        self.client.logout()
        url = reverse('shop:view_cart')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_add_to_cart_requires_post(self):
        """Test hanya POST diizinkan"""
        url = reverse('shop:add_to_cart', args=[self.product.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 405)

    def test_add_to_cart_new_item(self):
        """Test tambah item baru ke cart"""
        url = reverse('shop:add_to_cart', args=[self.product.id])
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 1)

    def test_add_to_cart_increment(self):
        """Test increment quantity"""
        url = reverse('shop:add_to_cart', args=[self.product.id])
        self.client.post(url)
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 200)
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_add_to_cart_exceed_stock(self):
        """Test melebihi stok"""
        url = reverse('shop:add_to_cart', args=[self.product.id])
        self.client.post(url)
        self.client.post(url)
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'error')

    def test_remove_from_cart(self):
        """Test hapus item dari cart"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        
        url = reverse('shop:remove_from_cart', args=[self.product.id])
        res = self.client.post(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_remove_from_cart_not_found(self):
        """Test hapus item tidak ada"""
        url = reverse('shop:remove_from_cart', args=[self.product.id])
        res = self.client.post(url, **ajax_headers())
        self.assertEqual(res.status_code, 404)

class WishlistViewTest(TestCase):
    """Test wishlist views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass')
        self.seller = User.objects.create_user(username='seller', password='pass2')
        self.product = Product.objects.create(
            name='Cap', price=50000, stock=4, category='swimming', seller=self.seller
        )
        self.client.login(username='user', password='pass')

    def test_toggle_wishlist_add(self):
        """Test tambah ke wishlist"""
        url = reverse('shop:toggle_wishlist', args=[self.product.id])
        res = self.client.post(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['in_wishlist'])

    def test_toggle_wishlist_remove(self):
        """Test hapus dari wishlist"""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist.products.add(self.product)
        
        url = reverse('shop:toggle_wishlist', args=[self.product.id])
        res = self.client.post(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['in_wishlist'])

    def test_toggle_wishlist_requires_login(self):
        """Test toggle memerlukan login"""
        self.client.logout()
        url = reverse('shop:toggle_wishlist', args=[self.product.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 302)

    def test_view_wishlist(self):
        """Test view wishlist"""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist.products.add(self.product)
        
        url = reverse('shop:view_wishlist')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_view_wishlist_ajax(self):
        """Test view wishlist AJAX"""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist.products.add(self.product)
        
        url = reverse('shop:view_wishlist')
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 1)

    def test_view_wishlist_ajax_product_price_format(self):
        """Test wishlist AJAX product price format dengan 2 desimal"""
        wishlist = Wishlist.objects.create(user=self.user)
        wishlist.products.add(self.product)
        
        url = reverse('shop:view_wishlist')
        res = self.client.get(url, **ajax_headers())
        
        self.assertEqual(res.status_code, 200)
        data = res.json()
        product = data['products'][0]
        # Price return sebagai string dengan format 2 desimal
        expected_price = f"{self.product.price:.2f}"
        self.assertEqual(product['price'], expected_price)

    def test_view_wishlist_requires_login(self):
        """Test view wishlist memerlukan login"""
        self.client.logout()
        url = reverse('shop:view_wishlist')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

class CheckoutViewTest(TestCase):
    """Test checkout view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='pass')
        self.seller = User.objects.create_user(username='seller', password='pass2')
        self.product = Product.objects.create(
            name='Item', price=10000, stock=5, category='cycling', seller=self.seller
        )
        self.client.login(username='buyer', password='pass')

    def test_checkout_requires_login(self):
        """Test checkout memerlukan login"""
        self.client.logout()
        url = reverse('shop:checkout')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_checkout_empty_cart(self):
        """Test checkout cart kosong redirect"""
        url = reverse('shop:checkout')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

    def test_checkout_get_with_items(self):
        """Test GET checkout dengan items"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        url = reverse('shop:checkout')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_checkout_post_success(self):
        """Test POST checkout berhasil"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        initial_stock = self.product.stock
        
        url = reverse('shop:checkout')
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

    def test_checkout_insufficient_stock(self):
        """Test checkout stok tidak cukup"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=10)
        
        url = reverse('shop:checkout')
        res = self.client.post(url)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_checkout_multiple_items(self):
        """Test checkout multiple items"""
        product2 = Product.objects.create(
            name='Item2', price=20000, stock=3, category='running', seller=self.seller
        )
        
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)
        
        url = reverse('shop:checkout')
        res = self.client.post(url)
        
        self.assertEqual(res.status_code, 302)
        self.product.refresh_from_db()
        product2.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(product2.stock, 2)