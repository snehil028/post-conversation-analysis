from django.contrib import admin
from .models import Conversation, Messages, ConversationAnalysis

# Register your models here.


class MessageInline(admin.TabularInline):
    model = Messages
    extra = 0


@admin.register(Conversation)  # registers the model
class ConversationAdmin(admin.ModelAdmin):  # customizing how it appears
    list_display = ("id", "title", "created_at")
    inlines = [MessageInline]  # to see all related messages in a conversation


@admin.register(ConversationAnalysis)
class ConversationAnalysisAdmin (admin.ModelAdmin):
    list_display = ("conversation", "overall_score", "created_at")
