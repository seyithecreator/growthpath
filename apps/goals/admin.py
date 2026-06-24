from django.contrib import admin
from .models import Goal, Milestone


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0
    fields = ('title', 'order', 'target_date', 'is_completed', 'completed_at')
    readonly_fields = ('completed_at',)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'status',
                    'progress_display', 'target_date', 'days_remaining_display')
    list_filter = ('category', 'priority', 'status')
    search_fields = ('title', 'user__username', 'description', 'success_metric')
    ordering = ('-created_at',)
    date_hierarchy = 'target_date'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [MilestoneInline]
    fieldsets = (
        (None, {'fields': ('user', 'title', 'description', 'category', 'priority', 'status')}),
        ('Metrics', {'fields': ('success_metric', 'target_value', 'current_value')}),
        ('Dates', {'fields': ('start_date', 'target_date', 'completed_at')}),
        ('AI Metadata', {'fields': ('tags', 'notes'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Progress')
    def progress_display(self, obj):
        return f'{obj.progress_percentage}%'

    @admin.display(description='Days Left')
    def days_remaining_display(self, obj):
        d = obj.days_remaining
        if d < 0:
            return f'Overdue ({abs(d)}d)'
        return f'{d}d'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal', 'order', 'target_date', 'is_completed', 'completed_at')
    list_filter = ('is_completed',)
    search_fields = ('title', 'goal__title', 'goal__user__username')
    ordering = ('goal', 'order')
    readonly_fields = ('completed_at',)
