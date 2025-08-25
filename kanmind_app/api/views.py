from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Count 
from ..models import Board, Task, Comment 
from .serializers import TaskSerializer, BoardSerializer, BoardUpdateSerializer, BoardDetailSerializer, TaskDetailSerializer, CommentSerializer, CommentCreateSerializer 
from .permissions import IsOwnerOrMember, IsOwner, IsTaskOnAccessibleBoard, IsAuthorOrReadOnly, CanDeleteTask 

class BoardViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        elif self.action in ['update', 'partial_update']:
             permission_classes = [permissions.IsAuthenticated, IsOwnerOrMember]
        else:
            permission_classes = [permissions.IsAuthenticated]
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
        board_instance = serializer.save(owner=self.request.user)
        board_instance.members.add(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = BoardSerializer(serializer.instance, context=self.get_serializer_context())
        
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not (instance.owner == request.user or request.user in instance.members.all()):
             raise PermissionDenied("You must be the owner or a member to edit this board.")

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_serializer = BoardDetailSerializer(instance, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_permissions(self):

        if self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, CanDeleteTask]
        else:
            permission_classes = [permissions.IsAuthenticated, IsTaskOnAccessibleBoard]
        return [permission() for permission in permission_classes]

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
            raise PermissionDenied("You do not have permission to create a task on this board.")
        
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        user = self.request.user
        tasks = self.get_queryset().filter(assignee=user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviews_for_me(self, request):
        user = self.request.user
        tasks = self.get_queryset().filter(reviewer=user) 
        serializer = self.get_serializer(tasks, many=True)
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