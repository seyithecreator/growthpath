from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import ActivityLog, ProductivitySnapshot


TYPE_COLOURS = {
    'study':      '#3B82F6',
    'exercise':   '#A855F7',
    'reading':    '#22C55E',
    'project':    '#F97316',
    'assessment': '#EAB308',
    'networking': '#06B6D4',
    'reflection': '#EC4899',
    'workshop':   '#8B5CF6',
    'other':      '#6B7280',
}


class ActivityLogAdminForm(forms.ModelForm):
    class Meta:
        model = ActivityLog
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['goal'].required = True
        self.fields['goal'].empty_label = '— Select a goal (required) —'
        self.fields['skill'].required = False

    def clean_goal(self):
        goal = self.cleaned_data.get('goal')
        if not goal:
            raise forms.ValidationError('Every activity must be linked to a goal.')
        return goal


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    form = ActivityLogAdminForm
    list_display = ('milestone_link', 'user', 'goal_link', 'type_badge', 'duration_display',
                    'progress_delta_display', 'productivity_stars', 'started_at')
    list_filter = ('goal', 'milestone', 'activity_type', 'productivity_score', 'focus_level')
    search_fields = ('title', 'user__username', 'description', 'outcome_notes', 'goal__title', 'milestone__title')
    ordering = ('-started_at',)
    date_hierarchy = 'started_at'
    readonly_fields = ('logged_at', 'duration_minutes')
    list_select_related = ('user', 'goal')
    list_per_page = 30
    fieldsets = (
        ('Goal (required)', {'fields': ('goal', 'milestone')}),
        ('Activity', {'fields': ('user', 'title', 'description', 'activity_type')}),
        ('Time', {'fields': ('started_at', 'ended_at', 'duration_minutes')}),
        ('Progress', {'fields': ('goal_progress_delta', 'skill_score_delta')}),
        ('Productivity', {'fields': ('productivity_score', 'focus_level', 'outcome_notes')}),
        ('Other', {'fields': ('skill', 'tags', 'logged_at'), 'classes': ('collapse',)}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'milestone':
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    from .models import ActivityLog
                    activity = ActivityLog.objects.get(pk=obj_id)
                    if activity.goal:
                        from apps.goals.models import Milestone
                        kwargs['queryset'] = Milestone.objects.filter(goal=activity.goal)
                except ActivityLog.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Milestone', ordering='milestone__title')
    def milestone_link(self, obj):
        if not obj.milestone:
            return format_html('<span style="color:var(--gp-text-muted,#888)">—</span>')
        status = '✓ ' if obj.milestone.is_completed else ''
        return format_html(
            '<span style="font-weight:600">{}{}</span>',
            status, obj.milestone.title[:45]
        )

    @admin.display(description='Goal', ordering='goal__title')
    def goal_link(self, obj):
        if not obj.goal:
            return format_html('<span style="color:#EF4444;font-weight:600">⚠ No goal</span>')
        return format_html(
            '<a href="/admin/goals/goal/{}/change/" style="color:var(--gp-purple,#A855F7);font-weight:600">{}</a>',
            obj.goal.pk, obj.goal.title[:40]
        )

    @admin.display(description='Type')
    def type_badge(self, obj):
        colour = TYPE_COLOURS.get(obj.activity_type, '#6B7280')
        return format_html(
            '<span style="background:{0}22;color:{0};padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{1}</span>',
            colour, obj.get_activity_type_display()
        )

    @admin.display(description='Duration')
    def duration_display(self, obj):
        if not obj.duration_minutes:
            return '—'
        h, m = divmod(obj.duration_minutes, 60)
        if h:
            return format_html('<span style="font-weight:600">{}h {}m</span>', h, m)
        return format_html('<span style="font-weight:600">{}m</span>', m)

    @admin.display(description='+Progress')
    def progress_delta_display(self, obj):
        if not obj.goal_progress_delta:
            return '—'
        return format_html(
            '<span style="color:#22C55E;font-weight:600">+{}</span>',
            obj.goal_progress_delta
        )

    @admin.display(description='Productivity')
    def productivity_stars(self, obj):
        score = obj.productivity_score or 0
        stars = '★' * score + '☆' * (5 - score)
        colour = '#22C55E' if score >= 4 else '#EAB308' if score >= 3 else '#EF4444'
        return format_html('<span style="color:{};letter-spacing:1px">{}</span>', colour, stars)


@admin.register(ProductivitySnapshot)
class ProductivitySnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_sessions', 'duration_display',
                    'productivity_bar', 'goals_advanced', 'skills_practised')
    list_filter = ('date',)
    search_fields = ('user__username',)
    ordering = ('-date',)
    date_hierarchy = 'date'
    readonly_fields = ('date',)
    list_select_related = ('user',)

    @admin.display(description='Time')
    def duration_display(self, obj):
        h, m = divmod(obj.total_minutes or 0, 60)
        return format_html('{}h {}m', h, m)

    @admin.display(description='Avg Productivity')
    def productivity_bar(self, obj):
        pct = int((obj.avg_productivity or 0) * 20)
        colour = '#22C55E' if pct >= 75 else '#EAB308' if pct >= 50 else '#EF4444'
        return format_html(
            '<div style="display:flex;align-items:center;gap:5px">'
            '<div style="width:70px;background:#2A2A3D;border-radius:99px;height:6px;overflow:hidden">'
            '<div style="width:{0}%;background:{1};height:100%;border-radius:99px"></div></div>'
            '<span style="font-size:11px;color:{1}">{2:.1f}/5</span>'
            '</div>',
            pct, colour, obj.avg_productivity or 0
        )
