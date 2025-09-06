from rest_framework import permissions

class IsOwnerOrMember(permissions.BasePermission):
    """
    Allows access only to the board's owner or its members.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.members.all()

class IsTaskOnAccessibleBoard(permissions.BasePermission):
    """
    Allows access if the user is the owner 
    or a member of the board that the task belongs to.
    """
    def has_object_permission(self, request, view, obj):
        board = obj.board
        return board.owner == request.user or request.user in board.members.all()
    
class IsOwner(permissions.BasePermission):
    """
    Allows access only to the owner of the object.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
    

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access for any request, 
    but write access only to the author of the object.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request (GET, HEAD, OPTIONS).
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the author of the object.
        return obj.author == request.user
    
class CanDeleteTask(permissions.BasePermission):
    """
    Allows deleting a task only if the user is the one who created it
    or if the user is the owner of the board the task is on.
    """
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or obj.board.owner == request.user
    
class CanAccessTaskComments(permissions.BasePermission):
    """
    Checks if a user can access the comments of a task.
    This is determined by checking if they have access to the parent board.
    """
    def has_permission(self, request, view):
        # This permission runs before an object is retrieved, so it gets the
        # parent task from the view's 'get_task' helper method.
        try:
            task = view.get_task()
        except AttributeError:
            # Fails safely if the view doesn't have the required method.
            return False

        user = request.user
        board = task.board
        return board.owner == user or user in board.members.all()