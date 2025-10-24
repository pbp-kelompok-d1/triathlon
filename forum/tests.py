from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ForumPost, ForumReply
from .forms import ForumPostForm

User = get_user_model()


class ForumUnitTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(username='testuser', password='testpass')
		self.admin = User.objects.create_user(username='adminuser', password='adminpass')
		# if profile exists, set admin role
		if hasattr(self.admin, 'profile'):
			self.admin.profile.role = 'ADMIN'
			self.admin.profile.save()

	def test_toggle_like_requires_login(self):
		post = ForumPost.objects.create(title='T', content='C', category='general', sport_category='running', author=self.user)
		url = reverse('forum:toggle_like', args=[post.id])
		resp = self.client.post(url)
		self.assertIn(resp.status_code, (302, 401, 403))

	def test_toggle_like_adds_and_removes(self):
		post = ForumPost.objects.create(title='T', content='C', category='general', sport_category='running', author=self.user)
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:toggle_like', args=[post.id])
		resp = self.client.post(url, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken', '') )
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data['success'])
		self.assertTrue(data['liked'])
		self.assertEqual(data['like_count'], 1)
		# toggle again
		resp2 = self.client.post(url, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken', ''))
		data2 = resp2.json()
		self.assertFalse(data2['liked'])
		self.assertEqual(data2['like_count'], 0)

	def test_add_reply_with_quote(self):
		post = ForumPost.objects.create(title='T', content='C', category='general', sport_category='running', author=self.user)
		r1 = ForumReply.objects.create(post=post, author=self.user, content='first')
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:add_reply', args=[post.id])
		resp = self.client.post(url, {'content': 'quoted reply', 'quote_reply_id': str(r1.id)}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken', ''))
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data['success'])
		self.assertIsNotNone(data['reply_data'].get('quote'))
		r2 = ForumReply.objects.get(content='quoted reply')
		self.assertIsNotNone(r2.quote_reply)

	def test_show_json_includes_like_count(self):
		p1 = ForumPost.objects.create(title='T1', content='C1', category='general', sport_category='running', author=self.user)
		p2 = ForumPost.objects.create(title='T2', content='C2', category='general', sport_category='running', author=self.user)
		p2.likes.add(self.user)
		url = reverse('forum:show_json')
		resp = self.client.get(url, HTTP_ACCEPT='application/json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		mapping = {item['title']: item['like_count'] for item in data}
		self.assertEqual(mapping['T1'], 0)
		self.assertEqual(mapping['T2'], 1)

	def test_post_detail_contains_like_label(self):
		p = ForumPost.objects.create(title='T', content='C', category='general', sport_category='running', author=self.user)
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:post_detail', args=[p.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# expecting Like label to be present (initial state)
		self.assertIn(b'Like', resp.content)

	def test_add_post_ajax_admin_and_nonadmin(self):
		# non-admin cannot pin
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:add_post_ajax')
		resp = self.client.post(url, {
			'title': 'P', 'content': 'Content here ok', 'category': 'general', 'sport_category': 'running', 'is_pinned': 'on'
		}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 201)
		post = ForumPost.objects.get(title='P')
		self.assertFalse(post.is_pinned)

		# admin can pin
		if hasattr(self.admin, 'profile'):
			self.client.login(username='adminuser', password='adminpass')
			resp2 = self.client.post(url, {
				'title': 'P2', 'content': 'Content here ok', 'category': 'general', 'sport_category': 'running', 'is_pinned': 'on'
			}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
			self.assertEqual(resp2.status_code, 201)
			post2 = ForumPost.objects.get(title='P2')
			self.assertTrue(post2.is_pinned)

	def test_edit_post_ajax_author_and_unauthorized(self):
		post = ForumPost.objects.create(title='E', content='C', category='general', sport_category='running', author=self.user)
		url = reverse('forum:edit_post_ajax', args=[post.id])
		# unauthorized user
		self.client.login(username='adminuser', password='adminpass')
		resp = self.client.post(url, {'title': 'New', 'content': 'New content', 'category': 'general', 'sport_category': 'running'}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 403)
		# author can edit
		self.client.login(username='testuser', password='testpass')
		resp2 = self.client.post(url, {'title': 'New', 'content': 'New content', 'category': 'general', 'sport_category': 'running'}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp2.status_code, 200)

	def test_delete_post_and_reply_permissions(self):
		post = ForumPost.objects.create(title='D', content='C', category='general', sport_category='running', author=self.user)
		reply = ForumReply.objects.create(post=post, author=self.user, content='r')
		url_delete_post = reverse('forum:delete_post', args=[post.id])
		url_delete_reply = reverse('forum:delete_reply', args=[reply.id])
		# unauthorized delete by other user
		self.client.login(username='adminuser', password='adminpass')
		# admin should be allowed
		resp = self.client.post(url_delete_post, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 200)
		# create another post/reply to test reply deletion
		post2 = ForumPost.objects.create(title='D2', content='C', category='general', sport_category='running', author=self.user)
		reply2 = ForumReply.objects.create(post=post2, author=self.user, content='r2')
		url_delete_reply2 = reverse('forum:delete_reply', args=[reply2.id])
		# non-author non-admin cannot delete
		other = User.objects.create_user(username='other', password='p')
		self.client.login(username='other', password='p')
		resp2 = self.client.post(url_delete_reply2, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp2.status_code, 403)

	def test_forumpostform_validation(self):
		# title too short
		form = ForumPostForm({'title': 'abc', 'content': 'long enough content', 'category': 'general', 'sport_category': 'running'})
		self.assertFalse(form.is_valid())
		self.assertIn('title', form.errors)
		# content too short
		form2 = ForumPostForm({'title': 'valid title', 'content': 'short', 'category': 'general', 'sport_category': 'running'})
		self.assertFalse(form2.is_valid())
		self.assertIn('content', form2.errors)
		# valid form
		form3 = ForumPostForm({'title': 'valid title', 'content': 'sufficiently long content', 'category': 'general', 'sport_category': 'running'})
		self.assertTrue(form3.is_valid())
