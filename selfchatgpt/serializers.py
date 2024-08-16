# selfchatgpt/serializers.py
from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=200)
    session_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
