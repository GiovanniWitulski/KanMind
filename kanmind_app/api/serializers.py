from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Board, Task, Comment


class UserSerializer(serializers.ModelSerializer):
    """Basic serializer for the User model, showing public info."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer that includes a calculated 'fullname' field."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']
    
    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for the Task model, handles both read and write operations."""
    # Read-only fields to display nested user data.
    assignee = UserDetailSerializer(read_only=True)
    reviewer = UserDetailSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    # Field to select the board when creating/updating a task.
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
    )

    # Write-only fields to accept user IDs for assigning tasks.
    # 'source' points to the actual model field to populate.
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
            # Include the write-only fields in the Meta class.
            'assignee_id', 'reviewer_id'
        ]
    

class BoardSerializer(serializers.ModelSerializer):
    """Serializer for Board list views, includes calculated summary fields."""
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

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
        """Calculates the total number of members on the board."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Calculates the total number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Calculates the number of tasks with 'To Do' status."""
        return obj.tasks.filter(status=Task.Status.TODO).count()

    def get_tasks_high_prio_count(self, obj):
        """Calculates the number of tasks with 'High' priority."""
        return obj.tasks.filter(priority=Task.Priority.HIGH).count()


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a Board, specifically for changing title and members."""
    # Read-only fields to show current state in the response.
    owner_data = UserDetailSerializer(source='owner', read_only=True)
    members_data = UserDetailSerializer(source='members', many=True, read_only=True)
    title = serializers.CharField(required=False)

    # Write-only field to accept a list of user IDs to set as members.
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True, 
        required=False
    )

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_data', 'members_data', 'members']


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer for the detailed view of a Board, including all members and tasks."""
    members = UserDetailSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'owner_id',
            'members',
            'tasks',
        ]


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments, with a custom author representation."""
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
    
    def get_author(self, obj):
        """Returns the author's full name if available, otherwise their username."""
        if obj.author.first_name and obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}"
        return obj.author.username