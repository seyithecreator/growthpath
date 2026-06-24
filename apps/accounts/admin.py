from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Achievement


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'university', 'department', 'year_of_study',
                    'streak_days', 'total_points', 'is_active')
    list_filter = ('year_of_study', 'daily_reminder', 'ai_personalisation', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'university', 'matric_number')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('bio', 'avatar', 'university', 'department', 'year_of_study', 'matric_number')}),
        ('Preferences', {'fields': ('daily_reminder', 'weekly_report', 'ai_personalisation',
                                     'peak_hour_start', 'peak_hour_end')}),
        ('Gamification', {'fields': ('streak_days', 'last_active_date', 'total_points')}),
    )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'category', 'icon', 'unlocked_at')
    list_filter = ('category',)
    search_fields = ('user__username', 'title')
    ordering = ('-unlocked_at',)
    date_hierarchy = 'unlocked_at'
