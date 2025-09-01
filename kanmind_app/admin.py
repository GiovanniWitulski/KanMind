from django.contrib import admin
from .models import Board, Task, Comment
# Register your models here.

class CustomerAdmin(admin.ModelAdmin):
    admin.site.register(Board)
    admin.site.register(Task)
    admin.site.register(Comment)