from rest_framework import serializers
from .models import Conversation, Messages, ConversationAnalysis


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Messages
        fields = ("sender", "text", "timestamp")  # fields in API input/output


class ConversationSerializer(serializers.ModelSerializer):
    # nesting MessageSerializer inside this
    messages = MessageSerializer(many=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "messages")

    def create(self, validated_data):
        messages = validated_data.pop("messages", [])
        conv = Conversation.objects.create(**validated_data)
        for m in messages:
            Messages.objects.create(conversation=conv, **m)
        return conv


class ConversationAnalysisSerializer(serializers.ModelSerializer):
    conversation = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ConversationAnalysis
        fields = "__all__"
