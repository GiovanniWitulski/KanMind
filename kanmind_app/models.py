from django.db import models
from django.conf import settings


class Task(models.Model):
    """
    Represents a single task or ticket within a project board.
    """
    # Extra 'Title Case' choices for task status and priority.
    class Status(models.TextChoices):
        TODO = 'to-do', 'To Do'
        IN_PROGRESS = 'in-progress', 'In Progress'
        REVIEW = 'review', 'Review'
        DONE = 'done', 'Done'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)

    # A task must belong to a board. If the board is deleted, the task is also deleted.
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='tasks')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Tracks who originally created the task.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep the task even if the creator's account is deleted.
        null=True,
        related_name='created_tasks'
    )

    # The user currently assigned to work on the task.
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )

    # The user responsible for reviewing the task.
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_tasks'
    )

    def __str__(self):
        return self.title
    

class Board(models.Model): 
    """
    Represents a project board that contains a collection of tasks.
    """
    title = models.CharField(max_length=255)

    # The user who owns and manages the board.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_boards'
    )

    # Users who are members of the board and can access its tasks.
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='member_of_boards',
        blank=True 
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

class Comment(models.Model):
    """
    Represents a comment made on a specific task.
    """
    # The task this comment is associated with.
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.task.title}'