# hackernews/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Story(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(blank=True)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    score = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
    
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('story_detail', kwargs={'pk': self.pk})
    
    def get_domain(self):
        if self.url:
            from urllib.parse import urlparse
            return urlparse(self.url).netloc
        return None
    
    def calculate_score(self):
        # Simple score calculation based on votes
        self.score = self.votes.filter(vote_type=Vote.UPVOTE).count()
        self.save()
        return self.score

class Comment(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.user.username} on {self.story.title}'

class Vote(models.Model):
    UPVOTE = 'upvote'
    VOTE_TYPES = [
        (UPVOTE, 'Upvote'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_TYPES, default=UPVOTE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'story']
    
    def __str__(self):
        return f'{self.vote_type} by {self.user.username} on {self.story.title}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    karma = models.IntegerField(default=0)
    
    def __str__(self):
        return f'Profile for {self.user.username}'
    
    def calculate_karma(self):
        # Calculate karma based on stories and comments
        story_karma = self.user.stories.aggregate(models.Sum('score'))['score__sum'] or 0
        comment_karma = self.user.comments.count() * 1  # Each comment is worth 1 karma
        self.karma = story_karma + comment_karma
        self.save()
        return self.karma