from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count 
from ..models import Board, Task, Comment 
from .serializers import TaskSerializer, BoardSerializer, BoardUpdateSerializer, BoardDetailSerializer, TaskDetailSerializer, CommentSerializer, CommentCreateSerializer 
from .permissions import IsOwnerOrMember, IsOwner, IsTaskOnAccessibleBoard, IsAuthorOrReadOnly 

class BoardViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrMember]
            
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer
        
        if self.action in ['create', 'update', 'partial_update']:
            return BoardUpdateSerializer
            
        return BoardSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = BoardDetailSerializer(instance, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOnAccessibleBoard]

    def get_queryset(self):
        user = self.request.user
        accessible_boards = Board.objects.filter(Q(owner=user) | Q(members=user))
        return Task.objects.filter(board__in=accessible_boards).annotate(
            comments_count=Count('comments')
        )
    
    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        user = self.request.user
        tasks = Task.objects.filter(assignee=user)
        serializer = TaskDetailSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)
    
        
    @action(detail=False, methods=['get'])
    def reviews_for_me(self, request):
        user = self.request.user
        tasks = Task.objects.filter(reviewer=user)
        serializer = TaskDetailSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)
    


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