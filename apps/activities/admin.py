from django.contrib import admin
from .models import ActivityLog, ProductivitySnapshot


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'activity_type', 'duration_minutes',
                    'productivity_score', 'focus_level', 'started_at')
    list_filter = ('activity_type', 'productivity_score', 'focus_level')
    search_fields = ('title', 'user__username', 'description', 'outcome_notes')
    ordering = ('-started_at',)
    date_hierarchy = 'started_at'
    readonly_fields = ('logged_at', 'duration_minutes')
    fieldsets = (
        (None, {'fields': ('user', 'title', 'description', 'activity_type')}),
        ('Time', {'fields': ('started_at', 'ended_at', 'duration_minutes')}),
        ('Productivity', {'fields': ('productivity_score', 'focus_level', 'outcome_notes')}),
        ('Linked Objects', {'fields': ('goal', 'skill')}),
        ('Progress Deltas', {'fields': ('goal_progress_delta', 'skill_score_delta')}),
        ('Metadata', {'fields': ('tags', 'logged_at'), 'classes': ('collapse',)}),
    )


@admin.register(ProductivitySnapshot)
class ProductivitySnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_sessions', 'total_minutes',
                    'avg_productivity', 'avg_focus', 'goals_advanced', 'skills_practised')
    list_filter = ('date',)
    search_fields = ('user__username',)
    ordering = ('-date',)
    date_hierarchy = 'date'
    readonly_fields = ('date',)
