from rest_framework import viewsets, permissions, generics, mixins
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Count 
from ..models import Board, Task, Comment 
from .serializers import BoardSerializer, BoardDetailSerializer, BoardUpdateSerializer, TaskSerializer, CommentSerializer 
from .permissions import IsOwnerOrMember, IsOwner, IsTaskOnAccessibleBoard, IsAuthorOrReadOnly, CanDeleteTask 

class BoardListCreateView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]

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
    
    queryset = Board.objects.all() 

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
        return self.create(request, *args, **kwargs)
    

class TaskDetailView(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):

    serializer_class = TaskSerializer
    queryset = Task.objects.all() 

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
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        task_pk = self.kwargs['task_pk']
        return Comment.objects.filter(task_id=task_pk)

    def perform_create(self, serializer):
        task_pk = self.kwargs['task_pk']
        task = Task.objects.get(pk=task_pk)
        serializer.save(author=self.request.user, task=task)