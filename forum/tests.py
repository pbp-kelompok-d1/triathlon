from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ForumPost, ForumReply
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By

User = get_user_model()

class ForumBasicTests(TestCase):
	"""Basic unit tests for forum post and reply functionality."""
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(username='testuser', password='testpass')
		self.admin = User.objects.create_user(username='adminuser', password='adminpass')
		self.admin.profile.role = 'ADMIN'
		self.admin.profile.save()

	def test_forum_post_creation(self):
		"""Test that a forum post can be created and saved."""
		post = ForumPost.objects.create(
			title='Test Post',
			content='Test Content',
			category='general',
			sport_category='RUNNING',
			author=self.user
		)
		self.assertEqual(ForumPost.objects.count(), 1)
		self.assertEqual(post.title, 'Test Post')

	def test_reply_creation(self):
		"""Test that a reply can be created for a forum post."""
		post = ForumPost.objects.create(
			title='Test Post',
			content='Test Content',
			category='general',
			sport_category='RUNNING',
			author=self.user
		)
		reply = ForumReply.objects.create(
			post=post,
			author=self.user,
			content='Reply Content'
		)
		self.assertEqual(post.replies.count(), 1)
		self.assertEqual(reply.content, 'Reply Content')

	def test_ajax_post_creation_requires_login(self):
		"""Test that AJAX post creation requires authentication."""
		url = reverse('forum:add_post_ajax')
		response = self.client.post(url, {
			'title': 'Ajax Post',
			'content': 'Ajax Content',
			'category': 'general',
			'sport_category': 'RUNNING',
		})
		self.assertEqual(response.status_code, 302)  # Redirect to login

	def test_ajax_post_creation_csrf(self):
		"""Test that AJAX post creation fails without CSRF token."""
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:add_post_ajax')
		# No CSRF token
		response = self.client.post(url, {
			'title': 'Ajax Post',
			'content': 'Ajax Content',
			'category': 'general',
			'sport_category': 'RUNNING',
		})
		self.assertEqual(response.status_code, 403)

	def test_ajax_post_creation_success(self):
		"""Test that AJAX post creation works with CSRF token and login."""
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:add_post_ajax')
		response = self.client.post(url, {
			'title': 'Ajax Post',
			'content': 'Ajax Content',
			'category': 'general',
			'sport_category': 'RUNNING',
		}, HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)
		self.assertEqual(response.status_code, 201)
		self.assertEqual(ForumPost.objects.count(), 1)

	def test_only_author_can_edit(self):
		"""Test that only the author can edit their post."""
		post = ForumPost.objects.create(
			title='Test Post',
			content='Test Content',
			category='general',
			sport_category='RUNNING',
			author=self.user
		)
		self.client.login(username='adminuser', password='adminpass')
		url = reverse('forum:edit_post_ajax', args=[post.id])
		response = self.client.post(url, {
			'title': 'Edited Title',
			'content': 'Edited Content',
			'category': 'general',
			'sport_category': 'RUNNING',
		}, HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)
		self.assertEqual(response.status_code, 403)

	def test_admin_can_pin(self):
		"""Test that only admin can pin a post."""
		self.client.login(username='adminuser', password='adminpass')
		url = reverse('forum:add_post_ajax')
		response = self.client.post(url, {
			'title': 'Pinned Post',
			'content': 'Content',
			'category': 'general',
			'sport_category': 'RUNNING',
			'is_pinned': 'on',
		}, HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)
		self.assertEqual(response.status_code, 201)
		post = ForumPost.objects.first()
		self.assertTrue(post.is_pinned)


from django.test import LiveServerTestCase
class ForumSeleniumTests(LiveServerTestCase):
#  modal open/close and form submit
	def setUp(self):
		self.driver = webdriver.Chrome()
		self.driver.implicitly_wait(5)
	def tearDown(self):
		self.driver.quit()
	def test_modal_open_close(self):
		self.driver.get(self.live_server_url + reverse('forum:forums'))
		add_post_btn = self.driver.find_element(By.ID, 'submitForumPost')
		add_post_btn.click()
		modal = self.driver.find_element(By.ID, 'crudModal')
		self.assertFalse(modal.get_attribute('class').find('hidden') != -1)
		close_btn = self.driver.find_element(By.ID, 'cancelButton')
		close_btn.click()
		self.assertTrue(modal.get_attribute('class').find('hidden') != -1)
