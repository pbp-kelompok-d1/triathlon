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
    is_pinned = models.BooleanField(default=False)
    
    # External connections for future apps
    product_id = models.IntegerField(null=True, blank=True)  # Will link to Product model later
    location_id = models.IntegerField(null=True, blank=True)  # Will link to Location model later
    
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
    
    def __str__(self):
        return f"Reply by {self.author} on {self.post.title}"
    

    
