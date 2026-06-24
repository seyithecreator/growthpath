from django.contrib import admin
from .models import SkillDomain, UserSkill, SkillScoreHistory


@admin.register(SkillDomain)
class SkillDomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain_type', 'icon', 'color_hex', 'is_global')
    list_filter = ('domain_type', 'is_global')
    search_fields = ('name', 'description')
    ordering = ('domain_type', 'name')


class SkillScoreHistoryInline(admin.TabularInline):
    model = SkillScoreHistory
    extra = 0
    fields = ('score', 'delta', 'recorded_at', 'notes')
    readonly_fields = ('recorded_at',)
    ordering = ('-recorded_at',)
    max_num = 20


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'domain', 'current_score', 'target_score',
                    'proficiency_label_display', 'gap_display', 'last_assessed', 'is_active')
    list_filter = ('domain', 'is_active')
    search_fields = ('user__username', 'domain__name', 'notes')
    ordering = ('-current_score',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SkillScoreHistoryInline]

    @admin.display(description='Proficiency')
    def proficiency_label_display(self, obj):
        return obj.proficiency_label

    @admin.display(description='Gap')
    def gap_display(self, obj):
        return f'{obj.gap:.1f}pts'


@admin.register(SkillScoreHistory)
class SkillScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ('skill', 'score', 'delta', 'recorded_at', 'notes')
    list_filter = ('recorded_at',)
    search_fields = ('skill__user__username', 'skill__domain__name', 'notes')
    ordering = ('-recorded_at',)
    date_hierarchy = 'recorded_at'
    readonly_fields = ('recorded_at',)
