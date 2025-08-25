from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Board, Task, Comment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class UserDetailSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']
    
    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserDetailSerializer(read_only=True)
    reviewer = UserDetailSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    board_id = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
        source='board',
        write_only=True
    )

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='assignee', 
        write_only=True,
        required=False,
        allow_null=True   
    )

    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='reviewer', 
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority', 
            'due_date', 'assignee', 'reviewer', 'comments_count', 
            'assignee_id', 'reviewer_id', 'board_id'
        ]
        read_only_fields = ['board']


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee = UserDetailSerializer(read_only=True)
    reviewer = UserDetailSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
    

class BoardSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id')

    class Meta:
        model = Board
        fields = [
            'id', 
            'title', 
            'member_count', 
            'ticket_count', 
            'tasks_to_do_count', 
            'tasks_high_prio_count', 
            'owner_id'
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status=Task.Status.TODO).count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority=Task.Priority.HIGH).count()


class BoardUpdateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False 
    )
    title = serializers.CharField(required=False)

    class Meta:
        model = Board
        fields = ['title', 'members']


class BoardDetailSerializer(serializers.ModelSerializer):
    owner_data = UserDetailSerializer(source='owner', read_only=True)
    members_data = UserDetailSerializer(source='members', many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'tasks',
            'owner_data',
            'members_data',
        ]


class CommentAuthorSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['author']

    def get_author(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
    
    def get_author(self, obj):
        if obj.author.first_name and obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}"
        return obj.author.username
    

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']