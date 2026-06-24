from django.contrib import admin
from django.utils.html import format_html
from .models import SkillDomain, UserSkill, SkillScoreHistory


PROFICIENCY_COLOURS = {
    'Beginner':     '#EF4444',
    'Elementary':   '#F97316',
    'Intermediate': '#EAB308',
    'Advanced':     '#3B82F6',
    'Expert':       '#22C55E',
}


@admin.register(SkillDomain)
class SkillDomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'type_badge', 'icon', 'colour_swatch', 'is_global')
    list_filter = ('domain_type', 'is_global')
    search_fields = ('name', 'description')
    ordering = ('domain_type', 'name')

    @admin.display(description='Type')
    def type_badge(self, obj):
        return format_html(
            '<span style="background:#7C3AED22;color:#A855F7;padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{}</span>',
            obj.domain_type.capitalize()
        )

    @admin.display(description='Colour')
    def colour_swatch(self, obj):
        if obj.color_hex:
            return format_html(
                '<span style="display:inline-block;width:18px;height:18px;border-radius:4px;'
                'background:{};vertical-align:middle"></span> {}',
                obj.color_hex, obj.color_hex
            )
        return '—'


class SkillScoreHistoryInline(admin.TabularInline):
    model = SkillScoreHistory
    extra = 0
    fields = ('score', 'delta', 'recorded_at', 'notes')
    readonly_fields = ('recorded_at',)
    ordering = ('-recorded_at',)
    max_num = 20


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'domain', 'score_bar', 'proficiency_badge', 'gap_display', 'last_assessed', 'is_active')
    list_filter = ('domain', 'is_active')
    search_fields = ('user__username', 'domain__name', 'notes')
    ordering = ('-current_score',)
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'domain')
    inlines = [SkillScoreHistoryInline]

    @admin.display(description='Score')
    def score_bar(self, obj):
        pct = int(obj.current_score)
        target = int(obj.target_score)
        colour = '#22C55E' if pct >= target * 0.8 else '#EAB308' if pct >= target * 0.5 else '#EF4444'
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;min-width:120px">'
            '<div style="flex:1;background:#2A2A3D;border-radius:99px;height:7px;overflow:hidden">'
            '<div style="width:{0}%;background:{2};height:100%;border-radius:99px"></div></div>'
            '<span style="font-size:12px;color:{2};font-weight:600">{1}/{3}</span>'
            '</div>',
            pct, int(obj.current_score), colour, target
        )

    @admin.display(description='Proficiency')
    def proficiency_badge(self, obj):
        label = obj.proficiency_label
        colour = PROFICIENCY_COLOURS.get(label, '#6B7280')
        return format_html(
            '<span style="background:{0}22;color:{0};padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{1}</span>',
            colour, label
        )

    @admin.display(description='Gap')
    def gap_display(self, obj):
        gap = obj.gap
        colour = '#EF4444' if gap > 30 else '#EAB308' if gap > 15 else '#22C55E'
        return format_html('<span style="color:{};font-weight:600">{:.0f} pts</span>', colour, gap)


@admin.register(SkillScoreHistory)
class SkillScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ('skill', 'score', 'delta_badge', 'recorded_at', 'notes')
    list_filter = ('recorded_at',)
    search_fields = ('skill__user__username', 'skill__domain__name', 'notes')
    ordering = ('-recorded_at',)
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)

    @admin.display(description='Delta')
    def delta_badge(self, obj):
        if obj.delta is None:
            return '—'
        colour = '#22C55E' if obj.delta > 0 else '#EF4444' if obj.delta < 0 else '#6B7280'
        sign = '+' if obj.delta > 0 else ''
        return format_html('<span style="color:{};font-weight:600">{}{}</span>', colour, sign, obj.delta)
