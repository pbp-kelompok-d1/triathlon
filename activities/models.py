import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from place.models import Place

appname = 'activities'

class ExerciseActivity(models.Model):

    SPORT_CATEGORY_CHOICES = [
        ('running', 'Running'),
        ('cycling', 'Cycling'),
        ('swimming', 'Swimming'),
    ]

    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False, db_index=True)
    title = models.CharField(max_length=30, blank=False, null=False)
    # location_id = models.IntegerField()

    # How long did the exercise take
    duration = models.DurationField()                                                                   
    
    # Stored in meters
    distance = models.PositiveIntegerField(blank=False,null=False)                                       
    
    notes = models.TextField(blank=True,null=True)    
    sport_category = models.CharField(max_length=20, choices=SPORT_CATEGORY_CHOICES, default='running')

    # Calories calculations taken from:
    # https://www.vinmec.com/eng/blog/how-many-calories-does-running-1km-reduce-en 76/km pace 10
    # https://www.nutracheck.co.uk/calories_burned/swimming/swimming 556 avg
    # https://rinascltabike.com/cycling/benefits/calories/ 30/km pace 25
    calories_burned = models.FloatField(blank=True,)

    created_at = models.DateTimeField(default=timezone.now)
    done_at = models.DateField()

    def save(self, *args, **kwargs):
        self.calories_burned = round(self.calories_burned, 2)
        super().save(*args, **kwargs)
