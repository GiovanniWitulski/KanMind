from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from . import views

# A simple router for nesting comment URLs under tasks.
comment_router = SimpleRouter()
comment_router.register(r'', views.CommentViewSet, basename='task-comments')

urlpatterns = [
    # URLs for Boards
    path('boards/', views.BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:pk>/', views.BoardDetailView.as_view(), name='board-detail'),

    # URLs for Tasks
    path('tasks/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),

    # URLs for specialized task lists
    path('tasks/assigned-to-me/', views.AssignedToMeTasksView.as_view(), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', views.ReviewingTasksView.as_view(), name='tasks-reviewing'),

    # Nested URL for comments related to a specific task
    path('tasks/<int:task_pk>/comments/', include(comment_router.urls)),
]