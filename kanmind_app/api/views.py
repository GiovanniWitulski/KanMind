from rest_framework import viewsets, permissions, generics, mixins
from rest_framework.exceptions import PermissionDenied, status
from rest_framework.response import Response
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from ..models import Board, Task, Comment 
from .serializers import BoardSerializer, BoardDetailSerializer, BoardUpdateSerializer, TaskSerializer, CommentSerializer
from .permissions import IsOwnerOrMember, IsOwner, IsTaskOnAccessibleBoard, IsAuthorOrReadOnly, CanDeleteTask, CanAccessTaskComments

class BoardListCreateView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        board_instance = serializer.save(owner=self.request.user)
        board_instance.members.add(self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class BoardDetailView(generics.GenericAPIView,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin):
    
    def get_queryset(self):
        tasks_with_comment_count = Task.objects.annotate(
            comments_count=Count('comments')
        )
        prefetch_tasks = Prefetch('tasks', queryset=tasks_with_comment_count)
        return Board.objects.prefetch_related(prefetch_tasks) 

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated(), IsOwnerOrMember()]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)    


class TaskListCreateView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOnAccessibleBoard]

    def get_queryset(self):
        user = self.request.user
        accessible_boards = Board.objects.filter(Q(owner=user) | Q(members=user))
        return Task.objects.filter(board__in=accessible_boards).annotate(
            comments_count=Count('comments')
        )

    def perform_create(self, serializer):
        board = serializer.validated_data['board']
        is_owner = board.owner == self.request.user
        is_member = self.request.user in board.members.all()

        if not (is_owner or is_member):
            raise PermissionDenied("You don't have permission to create a task on this board.")
        
        serializer.save(created_by=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        board_id = request.data.get('board')
        if not board_id:
            return Response({"board": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        board = get_object_or_404(Board, pk=board_id)

        user = request.user
        if not (board.owner == user or user in board.members.all()):
             raise PermissionDenied("You don't have permission to create a task on this board.")
        return self.create(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        instance = serializer.instance
        refreshed_instance = self.get_queryset().get(pk=instance.pk)
        response_serializer = self.get_serializer(refreshed_instance)
        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TaskDetailView(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):

    serializer_class = TaskSerializer
    def get_queryset(self):
        return Task.objects.annotate(
            comments_count=Count('comments')
        )

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), CanDeleteTask()]
        return [permissions.IsAuthenticated(), IsTaskOnAccessibleBoard()]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class AssignedToMeTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).annotate(
            comments_count=Count('comments')
        )

class ReviewingTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user).annotate(
            comments_count=Count('comments')
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessTaskComments, IsAuthorOrReadOnly]

    def get_task(self):
        task_pk = self.kwargs['task_pk']
        task = get_object_or_404(Task, pk=task_pk)
        return task

    def get_queryset(self):
        task = self.get_task()
        return Comment.objects.filter(task=task)

    def perform_create(self, serializer):
        task = self.get_task()
        serializer.save(author=self.request.user, task=task)