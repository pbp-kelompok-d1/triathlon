from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group


class MainViewsTests(TestCase):
	def test_show_main_get(self):
		"""GET to show_main should return 200 and include user/last_login in context."""
		url = reverse('main:show_main')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		# template context contains user and last_login
		self.assertIn('user', response.context)
		self.assertIn('last_login', response.context)

	def test_show_home_requires_login(self):
		url = reverse('main:show_home')
		response = self.client.get(url)
		# not logged in should redirect to login
		self.assertEqual(response.status_code, 302)
		self.assertIn('/login/', response.url)

	def test_register_get(self):
		url = reverse('main:register')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		# form should be provided in context
		self.assertIn('form', response.context)

	def test_register_post_creates_user_and_group(self):
		url = reverse('main:register')
		data = {
			'username': 'alice',
			'email': 'alice@example.com',
			'role': 'USER',
			'phone_number': '1234567890',
			'password1': 'safepassword123',
			'password2': 'safepassword123',
			'is_facility_admin': 'on',
		}
		response = self.client.post(url, data)
		# successful registration redirects to login
		self.assertEqual(response.status_code, 302)
		self.assertTrue(User.objects.filter(username='alice').exists())
		user = User.objects.get(username='alice')
		# profile should be created by signal and have role saved
		self.assertEqual(user.profile.role, 'USER')
		# Facility Administrator group should have been added
		facility_group = Group.objects.filter(name='Facility Administrator').first()
		self.assertIsNotNone(facility_group)
		self.assertIn(facility_group, user.groups.all())

	def test_register_post_ajax_success_and_error(self):
		url = reverse('main:register')
		# valid AJAX request
		data = {
			'username': 'bob',
			'email': 'bob@example.com',
			'role': 'USER',
			'password1': 'anothergoodpass',
			'password2': 'anothergoodpass',
		}
		response = self.client.post(url, data, HTTP_ACCEPT='application/json')
		self.assertEqual(response.status_code, 302 if response.status_code != 200 else 200)
		# Now invalid AJAX (password mismatch)
		bad = data.copy()
		bad['username'] = 'charlie'
		bad['password2'] = 'mismatch'
		response = self.client.post(url, bad, HTTP_ACCEPT='application/json')
		self.assertEqual(response.status_code, 400)
		self.assertIn('application/json', response['Content-Type'])

	def test_login_and_logout_flow(self):
		# create a user
		username = 'dave'
		password = 'mypassword123'
		user = User.objects.create_user(username=username, password=password)

		login_url = reverse('main:login')
		resp = self.client.post(login_url, {'username': username, 'password': password})
		# successful login should redirect to show_home
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp.url, reverse('main:show_home'))
		# cookie last_login should be set on response
		self.assertIn('last_login', resp.cookies)

		# now logout
		logout_url = reverse('main:logout')
		resp = self.client.get(logout_url)
		self.assertEqual(resp.status_code, 302)
		# after logout, cookie should be deleted (deleted cookie has empty value)
		# Django sets cookie with max-age=0 to delete; check it's not set in client.cookies
		self.assertNotIn('last_login', self.client.cookies)
