"""B2C Social Features Models - Placeholder"""
from django.db import models
from .customer import Customer

class TravelStory(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_travel_story'

class TravelPhoto(models.Model):
    story = models.ForeignKey(TravelStory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='stories/')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_travel_photo'

class StoryLike(models.Model):
    story = models.ForeignKey(TravelStory, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_story_like'

class StoryComment(models.Model):
    story = models.ForeignKey(TravelStory, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_story_comment'
