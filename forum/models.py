import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ForumPost(models.Model):
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    
    CATEGORY_CHOICES = [
        ('general', 'General Discussion'),
        ('product_review', 'Product Review'),
        ('location_review', 'Location Review'), 
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('feedback', 'Feedback'),
    ]

    SPORT_CATEGORY_CHOICES = [
        ('running', 'Running'),
        ('cycling', 'Cycling'),
        ('swimming', 'Swimming'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    sport_category = models.CharField(max_length=20, choices=SPORT_CATEGORY_CHOICES, default='running')
    post_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    
    
    last_activity = models.DateTimeField(default=timezone.now)  # Track latest activity (post creation or reply)
    last_edited = models.DateTimeField(null=True, blank=True)  # Track when post was last edited
    is_pinned = models.BooleanField(default=False)
    
    # External connections for future apps
    # product_id uses UUIDs to match Product.id (Product uses a UUID primary key)
    product_id = models.UUIDField(null=True, blank=True)
    # location_id remains IntegerField because Place uses integer PKs
    location_id = models.IntegerField(null=True, blank=True)  # Will link to Location model later

    # each user can like a post only once
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def like_count(self):
        return self.likes.count()

    def user_has_liked(self, user):
        return self.likes.filter(id=user.id).exists()
    
    def __str__(self):
        return self.title
    
    # @property
    # def is_post_hot(self):
    #     return self.post_views > 50
        
    def increment_views(self):
        self.post_views += 1
        self.save()


class ForumReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(ForumPost, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    quote_reply = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='quoted_by')

    def __str__(self):
        return f"Reply by {self.author} on {self.post.title}"
    

    
