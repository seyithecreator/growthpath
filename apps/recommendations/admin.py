from django.contrib import admin
from django.utils.html import format_html
from .models import Recommendation


TYPE_COLOURS = {
    'deadline':  '#EF4444',
    'skill_gap': '#A855F7',
    'habit':     '#22C55E',
    'schedule':  '#3B82F6',
    'peer':      '#F97316',
    'resource':  '#EAB308',
}


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type_badge', 'rank', 'confidence_bar',
                    'read_badge', 'actioned_badge', 'generated_at')
    list_filter = ('rec_type', 'is_read', 'is_actioned')
    search_fields = ('title', 'user__username', 'description')
    ordering = ('user', 'rank')
    date_hierarchy = 'generated_at'
    readonly_fields = ('generated_at', 'read_at')
    list_select_related = ('user',)
    list_per_page = 30
    fieldsets = (
        (None, {'fields': ('user', 'rec_type', 'rank', 'title', 'description',
                           'action_label', 'icon', 'confidence', 'tags')}),
        ('Linked Objects', {'fields': ('goal', 'skill')}),
        ('Status', {'fields': ('is_read', 'is_actioned', 'generated_at', 'read_at')}),
    )

    @admin.display(description='Type')
    def type_badge(self, obj):
        colour = TYPE_COLOURS.get(obj.rec_type, '#6B7280')
        return format_html(
            '<span style="background:{0}22;color:{0};padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{1}</span>',
            colour, obj.rec_type.replace('_', ' ').capitalize()
        )

    @admin.display(description='Confidence')
    def confidence_bar(self, obj):
        pct = int((obj.confidence or 0) * 100)
        colour = '#22C55E' if pct >= 80 else '#EAB308' if pct >= 60 else '#EF4444'
        return format_html(
            '<div style="display:flex;align-items:center;gap:5px">'
            '<div style="width:60px;background:#2A2A3D;border-radius:99px;height:6px;overflow:hidden">'
            '<div style="width:{0}%;background:{1};height:100%;border-radius:99px"></div></div>'
            '<span style="font-size:11px;color:{1}">{0}%</span>'
            '</div>',
            pct, colour
        )

    @admin.display(description='Read')
    def read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#22C55E">✓</span>')
        return format_html('<span style="color:#6B7280">—</span>')

    @admin.display(description='Actioned')
    def actioned_badge(self, obj):
        if obj.is_actioned:
            return format_html('<span style="color:#A855F7;font-weight:600">✓</span>')
        return format_html('<span style="color:#6B7280">—</span>')
