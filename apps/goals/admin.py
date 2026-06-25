from django.contrib import admin
from django.utils.html import format_html
from .models import Goal, Milestone
from apps.activities.models import ActivityLog


PRIORITY_COLOURS = {'critical': '#EF4444', 'high': '#F97316', 'medium': '#EAB308', 'low': '#6B7280'}
STATUS_COLOURS   = {'active': '#22C55E', 'completed': '#A855F7', 'paused': '#EAB308', 'abandoned': '#EF4444'}


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0
    fields = ('title', 'order', 'target_date', 'is_completed', 'completed_at')
    readonly_fields = ('completed_at',)


class ActivityLogInline(admin.TabularInline):
    model = ActivityLog
    extra = 0
    fields = ('milestone', 'productivity_score', 'outcome_notes', 'started_at')
    readonly_fields = ('started_at',)
    ordering = ('-started_at',)
    show_change_link = True
    verbose_name = 'Session'
    verbose_name_plural = 'Daily Activity Log'
    can_delete = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'milestone':
            goal_id = request.resolver_match.kwargs.get('object_id')
            if goal_id:
                from .models import Milestone
                kwargs['queryset'] = Milestone.objects.filter(goal_id=goal_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        # Relabel productivity_score → confidence level via the form
        return fields


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category_badge', 'priority_badge', 'status_badge',
                    'progress_bar', 'target_date', 'days_remaining_display')
    list_filter = ('category', 'priority', 'status')
    search_fields = ('title', 'user__username', 'description', 'success_metric')
    ordering = ('-created_at',)
    date_hierarchy = 'target_date'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    list_select_related = ('user',)
    list_per_page = 25
    inlines = [MilestoneInline, ActivityLogInline]
    fieldsets = (
        (None, {'fields': ('user', 'title', 'description', 'category', 'priority', 'status')}),
        ('Metrics', {'fields': ('success_metric', 'target_value', 'current_value')}),
        ('Dates', {'fields': ('start_date', 'target_date', 'completed_at')}),
        ('AI Metadata', {'fields': ('tags', 'notes'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Category')
    def category_badge(self, obj):
        return format_html(
            '<span style="background:#7C3AED22;color:#A855F7;padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{}</span>',
            obj.get_category_display()
        )

    @admin.display(description='Priority')
    def priority_badge(self, obj):
        colour = PRIORITY_COLOURS.get(obj.priority, '#6B7280')
        return format_html(
            '<span style="background:{0}22;color:{0};padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{1}</span>',
            colour, obj.priority.capitalize()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colour = STATUS_COLOURS.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{0}22;color:{0};padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{1}</span>',
            colour, obj.status.capitalize()
        )

    @admin.display(description='Progress')
    def progress_bar(self, obj):
        pct = int(obj.progress_percentage)
        colour = '#22C55E' if pct >= 75 else '#EAB308' if pct >= 40 else '#EF4444'
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;min-width:110px">'
            '<div style="flex:1;background:#2A2A3D;border-radius:99px;height:7px;overflow:hidden">'
            '<div style="width:{0}%;background:{1};height:100%;border-radius:99px"></div></div>'
            '<span style="font-size:12px;color:{1};font-weight:600;min-width:30px">{0}%</span>'
            '</div>',
            pct, colour
        )

    @admin.display(description='Days Left')
    def days_remaining_display(self, obj):
        d = obj.days_remaining
        if d < 0:
            return format_html('<span style="color:#EF4444;font-weight:600">Overdue {}d</span>', abs(d))
        if d <= 7:
            return format_html('<span style="color:#F97316;font-weight:600">{}d</span>', d)
        return format_html('<span style="color:#6B7280">{}d</span>', d)


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal', 'order', 'target_date', 'completed_badge')
    list_filter = ('is_completed',)
    search_fields = ('title', 'goal__title', 'goal__user__username')
    ordering = ('goal', 'order')
    readonly_fields = ('completed_at',)
    list_select_related = ('goal', 'goal__user')

    @admin.display(description='Completed')
    def completed_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color:#22C55E;font-weight:600">✓ Done</span>')
        return format_html('<span style="color:#6B7280">Pending</span>')
