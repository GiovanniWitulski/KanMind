from rest_framework import permissions

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