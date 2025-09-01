from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import UserProfile
# Register your models here.

class CustomerAdmin(admin.ModelAdmin):
    admin.site.register(UserProfile)

admin.site.unregister(User)
admin.site.unregister(Group)