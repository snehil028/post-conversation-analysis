from django.db import models

# Create your models here.


class Conversation(models.Model):  # represents one entire chat
    # title is optional field to enter chat name
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Messages(models.Model):  # stores all messages in a coversation
    SENDER_CHOICES = [
        ('user', "User"),
        ('ai', 'AI')
    ]
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,  related_name="messages")
    sender = models.CharField(
        max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()  # message content
    timestamp = models.DateTimeField(
        null=True, blank=True)  # to provide time of message


class ConversationAnalysis(models.Model):
    conversation = models.OneToOneField(
        Conversation, on_delete=models.CASCADE, related_name='analysis')
    clarity_score = models.FloatField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    empathy_score = models.FloatField(null=True, blank=True)
    fallback_count = models.IntegerField(default=0)
    sentiment = models.CharField(max_length=20, null=True, blank=True)
    resolution = models.BooleanField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
