# core/admin.py (ya jis app me models hain)

from django.contrib import admin
from .models import User, App, UserApp, AILog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email', 'is_investor', 'is_staff', 'is_active')
    search_fields = ('username', 'full_name', 'email', 'phone')
    list_filter = ('is_investor', 'is_staff', 'is_active')

@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')

@admin.register(UserApp)
class UserAppAdmin(admin.ModelAdmin):
    list_display = ('user', 'app', 'access_granted')
    list_filter = ('access_granted',)
    search_fields = ('user__username', 'app__name')

@admin.register(AILog)
class AILogAdmin(admin.ModelAdmin):
    list_display = ('user', 'app', 'prompt', 'response', 'timestamp')
    search_fields = ('user__username', 'app__name', 'prompt')
    list_filter = ('timestamp',)
    readonly_fields = ('timestamp',)
