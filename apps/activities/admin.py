from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import ActivityLog, ProductivitySnapshot


CONFIDENCE_LABELS = {1: 'Not confident yet', 2: 'Struggling', 3: 'Getting there', 4: 'Confident', 5: 'Very confident'}
CONFIDENCE_COLOURS = {1: '#EF4444', 2: '#F97316', 3: '#EAB308', 4: '#3B82F6', 5: '#22C55E'}


class ActivityLogAdminForm(forms.ModelForm):
    confidence_level = forms.ChoiceField(
        choices=[(i, f'{i} — {CONFIDENCE_LABELS[i]}') for i in range(1, 6)],
        initial=3,
        label='Confidence level',
        widget=forms.Select(attrs={'style': 'max-width:300px'}),
    )

    class Meta:
        model = ActivityLog
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['goal'].required = True
        self.fields['goal'].empty_label = '— Select a goal (required) —'
        # Pre-fill confidence_level from productivity_score
        if self.instance and self.instance.pk:
            self.fields['confidence_level'].initial = self.instance.productivity_score

    def clean_goal(self):
        goal = self.cleaned_data.get('goal')
        if not goal:
            raise forms.ValidationError('Every activity must be linked to a goal.')
        return goal

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.productivity_score = int(self.cleaned_data.get('confidence_level', 3))
        if commit:
            instance.save()
        return instance


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    form = ActivityLogAdminForm
    list_display = ('milestone_link', 'user', 'goal_link', 'confidence_display', 'started_at')
    list_filter = ('goal', 'milestone', 'productivity_score')
    search_fields = ('title', 'user__username', 'outcome_notes', 'goal__title', 'milestone__title')
    ordering = ('-started_at',)
    date_hierarchy = 'started_at'
    readonly_fields = ('logged_at', 'started_at')
    list_select_related = ('user', 'goal', 'milestone')
    list_per_page = 30
    fieldsets = (
        ('Goal & Milestone (required)', {'fields': ('goal', 'milestone')}),
        ('Session', {'fields': ('user', 'confidence_level', 'outcome_notes')}),
        ('Metadata', {'fields': ('logged_at', 'started_at'), 'classes': ('collapse',)}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'milestone':
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
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
            return format_html('<span style="color:#888">—</span>')
        status = '✓ ' if obj.milestone.is_completed else ''
        return format_html('<span style="font-weight:600">{}{}</span>', status, obj.milestone.title[:50])

    @admin.display(description='Goal', ordering='goal__title')
    def goal_link(self, obj):
        if not obj.goal:
            return format_html('<span style="color:#EF4444;font-weight:600">⚠ No goal</span>')
        return format_html(
            '<a href="/admin/goals/goal/{}/change/" style="color:#A855F7;font-weight:600">{}</a>',
            obj.goal.pk, obj.goal.title[:40]
        )

    @admin.display(description='Confidence', ordering='productivity_score')
    def confidence_display(self, obj):
        score = obj.productivity_score or 0
        colour = CONFIDENCE_COLOURS.get(score, '#6B7280')
        label = CONFIDENCE_LABELS.get(score, '—')
        dots = '●' * score + '○' * (5 - score)
        return format_html(
            '<span style="color:{};font-weight:600;letter-spacing:2px">{}</span>'
            '<span style="color:{};font-size:11px;margin-left:6px">{}/5 {}</span>',
            colour, dots, colour, score, label
        )


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
