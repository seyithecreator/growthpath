from django.contrib import admin
from django.utils.html import format_html
from .models import ActivityLog, ProductivitySnapshot


TYPE_COLOURS = {
    'study':    '#3B82F6',
    'practice': '#A855F7',
    'reading':  '#22C55E',
    'project':  '#F97316',
    'revision': '#EAB308',
    'other':    '#6B7280',
}


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type_badge', 'duration_display',
                    'productivity_stars', 'focus_stars', 'started_at')
    list_filter = ('activity_type', 'productivity_score', 'focus_level')
    search_fields = ('title', 'user__username', 'description', 'outcome_notes')
    ordering = ('-started_at',)
    date_hierarchy = 'started_at'
    readonly_fields = ('logged_at', 'duration_minutes')
    list_select_related = ('user',)
    list_per_page = 30
    fieldsets = (
        (None, {'fields': ('user', 'title', 'description', 'activity_type')}),
        ('Time', {'fields': ('started_at', 'ended_at', 'duration_minutes')}),
        ('Productivity', {'fields': ('productivity_score', 'focus_level', 'outcome_notes')}),
        ('Linked Objects', {'fields': ('goal', 'skill')}),
        ('Progress Deltas', {'fields': ('goal_progress_delta', 'skill_score_delta')}),
        ('Metadata', {'fields': ('tags', 'logged_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Type')
    def type_badge(self, obj):
        colour = TYPE_COLOURS.get(obj.activity_type, '#6B7280')
        return format_html(
            '<span style="background:{0}22;color:{0};padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{1}</span>',
            colour, obj.activity_type.capitalize()
        )

    @admin.display(description='Duration')
    def duration_display(self, obj):
        if not obj.duration_minutes:
            return '—'
        h, m = divmod(obj.duration_minutes, 60)
        if h:
            return format_html('<span style="font-weight:600">{}h {}m</span>', h, m)
        return format_html('<span style="font-weight:600">{}m</span>', m)

    @admin.display(description='Productivity')
    def productivity_stars(self, obj):
        score = obj.productivity_score or 0
        stars = '★' * score + '☆' * (5 - score)
        colour = '#22C55E' if score >= 4 else '#EAB308' if score >= 3 else '#EF4444'
        return format_html('<span style="color:{};letter-spacing:1px">{}</span>', colour, stars)

    @admin.display(description='Focus')
    def focus_stars(self, obj):
        score = obj.focus_level or 0
        stars = '★' * score + '☆' * (5 - score)
        colour = '#3B82F6' if score >= 4 else '#EAB308' if score >= 3 else '#6B7280'
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
