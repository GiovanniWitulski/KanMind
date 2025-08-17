from rest_framework import viewsets, permissions, status 
from rest_framework.response import Response
from django.db.models import Q
from ..models import Board, Task
from .serializers import TaskSerializer, BoardSerializer, BoardUpdateSerializer, BoardDetailSerializer
from .permissions import IsOwnerOrMember, IsOwner, IsTaskOnAccessibleBoard

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
        return Task.objects.filter(board__in=accessible_boards)
    
