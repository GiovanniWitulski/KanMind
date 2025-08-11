# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Board, Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'


class BoardSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='member_count', read_only=True)
    ticket_count = serializers.IntegerField(source='ticket_count', read_only=True)
    tasks_to_do_count = serializers.IntegerField(source='tasks_to_do_count', read_only=True)
    tasks_high_prio_count = serializers.IntegerField(source='tasks_high_prio_count', read_only=True)
    
    owner_id = serializers.PrimaryKeyRelatedField(source='owner', read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 
            'title', 
            'owner_id',
            'member_count', 
            'ticket_count', 
            'tasks_to_do_count', 
            'tasks_high_prio_count'
        ]