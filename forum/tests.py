from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ForumPost, ForumReply
from .forms import ForumPostForm
from django.utils import timezone
from datetime import timedelta

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

	def test_show_forums_filters_and_context(self):
		# create a place and product to ensure context includes them
		from place.models import Place
		from shop.models import Product
		place = Place.objects.create(name='P1', price=1.0)
		product = Product.objects.create(name='Prod1', description='d', price=10.0, stock=5)
		# create posts by different authors
		post_user = ForumPost.objects.create(title='U', content='C', category='general', sport_category='running', author=self.user)
		post_admin = ForumPost.objects.create(title='A', content='C', category='general', sport_category='running', author=self.admin)
		# login as user and request all
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:show_forums')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# context contains places and products
		self.assertIn('places', resp.context)
		self.assertIn('products', resp.context)
		# filter=my should return only user's posts
		resp2 = self.client.get(url + '?filter=my')
		self.assertEqual(resp2.status_code, 200)
		posts = resp2.context['posts']
		self.assertTrue(all(p.author == self.user for p in posts))

	def test_add_post_ajax_parses_product_and_location(self):
		from shop.models import Product
		product = Product.objects.create(name='Ptest', description='d', price=5.0, stock=2)
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:add_post_ajax')
		# valid product uuid and numeric location
		resp = self.client.post(url, {
			'title': 'WithLinks', 'content': 'Content long enough', 'category': 'general', 'sport_category': 'running',
			'product_id': str(product.id), 'location_id': '42'
		}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 201)
		p = ForumPost.objects.get(title='WithLinks')
		self.assertEqual(str(p.product_id), str(product.id))
		self.assertEqual(p.location_id, 42)
		# invalid product uuid should result in None product_id
		resp2 = self.client.post(url, {
			'title': 'BadProd', 'content': 'Content long enough', 'category': 'general', 'sport_category': 'running',
			'product_id': 'not-a-uuid', 'location_id': ''
		}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp2.status_code, 201)
		p2 = ForumPost.objects.get(title='BadProd')
		self.assertIsNone(p2.product_id)

	def test_add_reply_empty_content_returns_400(self):
		post = ForumPost.objects.create(title='T3', content='C3', category='general', sport_category='running', author=self.user)
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:add_reply', args=[post.id])
		resp = self.client.post(url, {'content': '   '}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 400)

	def test_delete_post_unauthorized_user_cannot_delete(self):
		post = ForumPost.objects.create(title='Private', content='C', category='general', sport_category='running', author=self.user)
		other = User.objects.create_user(username='other2', password='pw')
		self.client.login(username='other2', password='pw')
		url = reverse('forum:delete_post', args=[post.id])
		resp = self.client.post(url, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 403)

	def test_delete_reply_admin_can_delete(self):
		post = ForumPost.objects.create(title='Dadmin', content='C', category='general', sport_category='running', author=self.user)
		reply = ForumReply.objects.create(post=post, author=self.user, content='to be removed')
		# ensure admin has profile role if profile exists
		if hasattr(self.admin, 'profile'):
			self.admin.profile.role = 'ADMIN'
			self.admin.profile.save()
		self.client.login(username='adminuser', password='adminpass')
		url = reverse('forum:delete_reply', args=[reply.id])
		resp = self.client.post(url, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		# either success (200) or JSON success
		self.assertIn(resp.status_code, (200,))

	def test_post_detail_linked_objects_and_counts(self):
		from shop.models import Product
		from place.models import Place
		# create product and place and link to post
		product = Product.objects.create(name='LinkProd', description='d', price=3.0, stock=1)
		place = Place.objects.create(name='PlaceX', price=1.0)
		# author has one other post and one reply to create counts
		other_post = ForumPost.objects.create(title='Other', content='Content other', category='general', sport_category='running', author=self.user)
		post = ForumPost.objects.create(title='Linked', content='Long content here', category='general', sport_category='running', author=self.user, product_id=product.id, location_id=place.id)
		# add a reply by same author to increase their reply count
		reply = ForumReply.objects.create(post=post, author=self.user, content='hello')
		# create an anonymous reply (author None)
		anon_reply = ForumReply.objects.create(post=post, author=None, content='anon')
		# call post_detail
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:post_detail', args=[post.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		ctx = resp.context
		self.assertIsNotNone(ctx['linked_product'])
		self.assertIsNotNone(ctx['linked_place'])
		# original poster total posts should account for the extra post + replies
		self.assertGreaterEqual(ctx['original_poster_total_posts'], 2)
		# replies in context should have total_posts attribute
		for r in ctx['replies']:
			self.assertTrue(hasattr(r, 'total_posts'))

	def test_post_detail_views_and_user_has_liked(self):
		post = ForumPost.objects.create(title='Views', content='C', category='general', sport_category='running', author=self.user)
		# initial views
		initial = post.post_views
		# user likes the post
		post.likes.add(self.user)
		self.client.login(username='testuser', password='testpass')
		url = reverse('forum:post_detail', args=[post.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		ctx = resp.context
		self.assertTrue(ctx['user_has_liked_post'])
		post.refresh_from_db()
		self.assertEqual(post.post_views, initial + 1)

	def test_delete_reply_updates_last_activity(self):
		post = ForumPost.objects.create(title='LA', content='C', category='general', sport_category='running', author=self.user)
		# create two replies with different timestamps
		r1 = ForumReply.objects.create(post=post, author=self.user, content='r1')
		r1.created_at = timezone.now() - timedelta(days=2)
		r1.save(update_fields=['created_at'])
		r2 = ForumReply.objects.create(post=post, author=self.user, content='r2')
		r2.created_at = timezone.now() - timedelta(days=1)
		r2.save(update_fields=['created_at'])
		# ensure last_activity is latest reply
		post.last_activity = r2.created_at
		post.save()
		# delete r2 as admin
		if hasattr(self.admin, 'profile'):
			self.admin.profile.role = 'ADMIN'
			self.admin.profile.save()
		self.client.login(username='adminuser', password='adminpass')
		url = reverse('forum:delete_reply', args=[r2.id])
		resp = self.client.post(url, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 200)
		post.refresh_from_db()
		# last_activity should now equal r1.created_at
		self.assertEqual(post.last_activity.replace(microsecond=0), r1.created_at.replace(microsecond=0))

	def test_edit_post_ajax_admin_author_can_pin(self):
		# make admin user an author and admin role
		if hasattr(self.admin, 'profile'):
			self.admin.profile.role = 'ADMIN'
			self.admin.profile.save()
		post = ForumPost.objects.create(title='AuthAdmin', content='C', category='general', sport_category='running', author=self.admin)
		self.client.login(username='adminuser', password='adminpass')
		url = reverse('forum:edit_post_ajax', args=[post.id])
		resp = self.client.post(url, {'title': 'AuthAdmin', 'content': 'C2', 'category': 'general', 'sport_category': 'running', 'is_pinned': 'on'}, HTTP_X_CSRFTOKEN=self.client.cookies.get('csrftoken',''))
		self.assertEqual(resp.status_code, 200)
		post.refresh_from_db()
		self.assertTrue(post.is_pinned)

	def test_show_json_includes_author_role_and_initial(self):
		# ensure profile exists and set role
		if hasattr(self.user, 'profile'):
			self.user.profile.role = 'ADMIN'
			self.user.profile.save()
		p = ForumPost.objects.create(title='JSONRole', content='Cjson', category='general', sport_category='running', author=self.user)
		url = reverse('forum:show_json')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		# find our post
		entry = next((e for e in data if e['title'] == 'JSONRole'), None)
		self.assertIsNotNone(entry)
		self.assertEqual(entry['author_initial'], self.user.username[0].upper())
		self.assertEqual(entry['author_role'], 'ADMIN')
