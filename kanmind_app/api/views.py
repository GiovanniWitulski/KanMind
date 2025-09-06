from rest_framework import viewsets, permissions, generics, mixins
from rest_framework.exceptions import PermissionDenied, status
from rest_framework.response import Response
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from ..models import Board, Task, Comment 
from .serializers import BoardSerializer, BoardDetailSerializer, BoardUpdateSerializer, TaskSerializer, CommentSerializer
from .permissions import IsOwnerOrMember, IsOwner, IsTaskOnAccessibleBoard, IsAuthorOrReadOnly, CanDeleteTask, CanAccessTaskComments

class BoardListCreateView(generics.ListCreateAPIView):
    """Handles listing and creating boards for the logged-in user."""
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Returns boards where the user is either the owner or a member."""
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        """Sets the current user as the board owner and adds them as a member."""
        board_instance = serializer.save(owner=self.request.user)
        board_instance.members.add(self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Handles retrieving, updating, and deleting a single board."""

    def get_queryset(self):
        """
        Optimizes the query by prefetching related tasks and annotating
        them with a comment count to prevent N+1 query problems.
        """
        tasks_with_comment_count = Task.objects.annotate(
            comments_count=Count('comments')
        )
        prefetch_tasks = Prefetch('tasks', queryset=tasks_with_comment_count)
        return Board.objects.prefetch_related(prefetch_tasks) 

    def get_serializer_class(self):
        """Uses a different serializer for update actions versus retrieve actions."""
        if self.request.method in ['PUT', 'PATCH']:
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_permissions(self):
        """Sets stricter permissions for the DELETE action (owner only)."""
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated(), IsOwnerOrMember()]


class TaskListCreateView(generics.ListCreateAPIView):
    """Handles listing all accessible tasks and creating a new task on a board."""
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOnAccessibleBoard]

    def get_queryset(self):
        """Returns tasks from all boards the user has access to."""
        user = self.request.user
        accessible_boards = Board.objects.filter(Q(owner=user) | Q(members=user))
        return Task.objects.filter(board__in=accessible_boards).annotate(
            comments_count=Count('comments')
        )

    def perform_create(self, serializer):
        """Sets the current user as the creator of the task."""
        board = serializer.validated_data['board']
        is_owner = board.owner == self.request.user
        is_member = self.request.user in board.members.all()

        if not (is_owner or is_member):
            raise PermissionDenied("You don't have permission to create a task on this board.")
        
        serializer.save(created_by=self.request.user)

    def post(self, request, *args, **kwargs):
        """
        Overrides the default post to perform a manual permission check
        before attempting to create the task.
        """
        board_id = request.data.get('board')
        if not board_id:
            return Response({"board": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        board = get_object_or_404(Board, pk=board_id)

        # Check if the user is a member of the board before proceeding.
        user = request.user
        if not (board.owner == user or user in board.members.all()):
             raise PermissionDenied("You don't have permission to create a task on this board.")
        return self.create(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """
        Overrides the default create to ensure the response data includes
        the annotated 'comments_count' field after creation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Re-fetch the instance from the annotated queryset to get all fields.
        instance = serializer.instance
        refreshed_instance = self.get_queryset().get(pk=instance.pk)
        response_serializer = self.get_serializer(refreshed_instance)

        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Handles retrieving, updating, and deleting a single task."""
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Returns all tasks, annotated with their comment count."""
        return Task.objects.annotate(comments_count=Count('comments'))

    def get_permissions(self):
        """Sets stricter permissions for deleting a task."""
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), CanDeleteTask()]
        return [permissions.IsAuthenticated(), IsTaskOnAccessibleBoard()]


class AssignedToMeTasksView(generics.ListAPIView):
    """Provides a list of tasks assigned to the current user."""
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filters tasks where the assignee is the logged-in user."""
        return Task.objects.filter(assignee=self.request.user).annotate(
            comments_count=Count('comments')
        )

class ReviewingTasksView(generics.ListAPIView):
    """Provides a list of tasks the current user is responsible for reviewing."""
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filters tasks where the reviewer is the logged-in user."""
        return Task.objects.filter(reviewer=self.request.user).annotate(
            comments_count=Count('comments')
        )


class CommentViewSet(viewsets.ModelViewSet):
    """Handles all CRUD operations for comments on a specific task."""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessTaskComments, IsAuthorOrReadOnly]

    def get_task(self):
        """Helper method to retrieve the parent task from the URL."""
        task_pk = self.kwargs['task_pk']
        task = get_object_or_404(Task, pk=task_pk)
        return task

    def get_queryset(self):
        """Filters comments to only show those belonging to the parent task."""
        task = self.get_task()
        return Comment.objects.filter(task=task)

    def perform_create(self, serializer):
        """Automatically sets the comment's author and parent task upon creation."""
        task = self.get_task()
        serializer.save(author=self.request.user, task=task)