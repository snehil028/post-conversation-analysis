
from celery import shared_task
from .models import Conversation, ConversationAnalysis
from .engine import analyze_conversation  # ✅ correct import


@shared_task
def analyze_new_conversations_task():

    qs = Conversation.objects.filter(analysis__isnull=True)
    for conv in qs:
        metrics = analyze_conversation(conv)
        ConversationAnalysis.objects.create(
            conversation=conv,
            clarity_score=metrics.get("clarity_score"),
            relevance_score=metrics.get("relevance_score"),
            empathy_score=metrics.get("empathy_score"),
            fallback_count=metrics.get("fallback_count"),
            sentiment=metrics.get("sentiment"),
            resolution=metrics.get("resolution"),
            overall_score=metrics.get("overall_score"),
        )
    print(f" Analyzed {qs.count()} new conversations.")
