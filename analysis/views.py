from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Conversation, ConversationAnalysis
from .serializers import ConversationSerializer, ConversationAnalysisSerializer
from .engine import analyze_conversation

# Create your views here.


class ConversationUploadView(APIView):
    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conv = serializer.save()
        return Response({"conversation_id": conv.id}, status=status.HTTP_201_CREATED)


class TriggerAnalysisView(APIView):
    def post(self, request):
        conv_id = request.data.get("conversation_id")
        if not conv_id:
            return Response({"detail": "conversation_id required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            conv = Conversation.objects.get(pk=conv_id)
        except Conversation.DoesNotExist:
            return Response({"detail": "conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        metrics = analyze_conversation(conv)

        # create or update ConversationAnalysis
        ca, _ = ConversationAnalysis.objects.update_or_create(
            conversation=conv,
            defaults={
                "clarity_score": metrics.get("clarity_score"),
                "relevance_score": metrics.get("relevance_score"),
                "empathy_score": metrics.get("empathy_score"),
                "fallback_count": metrics.get("fallback_count"),
                "sentiment": metrics.get("sentiment"),
                "resolution": metrics.get("resolution"),
                "overall_score": metrics.get("overall_score"),
            }
        )
        ser = ConversationAnalysisSerializer(ca)
        return Response(ser.data)


class AnalysesListView(APIView):
    def get(self, request):
        qs = ConversationAnalysis.objects.select_related(
            "conversation").all().order_by("-created_at")
        ser = ConversationAnalysisSerializer(qs, many=True)
        return Response(ser.data)
