from rest_framework import permissions
from ..models import Task

class IsOwnerOrMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.members.all()

class IsTaskOnAccessibleBoard(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        board = obj.board
        return board.owner == request.user or request.user in board.members.all()
    
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
    

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
    
class CanDeleteTask(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or obj.board.owner == request.user
    
class CanAccessTaskComments(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            task = Task.objects.get(pk=view.kwargs['task_pk'])
        except Task.DoesNotExist:
            return True

        user = request.user
        board = task.board
        return board.owner == user or user in board.members.all()