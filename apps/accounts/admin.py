from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Achievement


YEAR_LABELS = {1: '100L', 2: '200L', 3: '300L', 4: '400L', 5: '500L', 6: 'PG'}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name_display', 'university', 'year_badge',
                    'streak_display', 'points_display', 'active_badge')
    list_filter = ('year_of_study', 'daily_reminder', 'ai_personalisation', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'university', 'matric_number')
    ordering = ('-date_joined',)
    list_select_related = ()
    list_per_page = 25
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('bio', 'avatar', 'university', 'department', 'year_of_study', 'matric_number')}),
        ('Preferences', {'fields': ('daily_reminder', 'weekly_report', 'ai_personalisation',
                                    'peak_hour_start', 'peak_hour_end')}),
        ('Gamification', {'fields': ('streak_days', 'last_active_date', 'total_points')}),
    )

    @admin.display(description='Name')
    def full_name_display(self, obj):
        name = obj.get_full_name()
        if name:
            return format_html('<span style="font-weight:600">{}</span>', name)
        return format_html('<span style="color:#6B7280">—</span>')

    @admin.display(description='Level')
    def year_badge(self, obj):
        if not obj.year_of_study:
            return format_html('<span style="color:#6B7280">—</span>')
        label = YEAR_LABELS.get(obj.year_of_study, str(obj.year_of_study))
        return format_html(
            '<span style="background:#7C3AED22;color:#A855F7;padding:2px 8px;'
            'border-radius:99px;font-size:11px;font-weight:600">{}</span>',
            label
        )

    @admin.display(description='Streak')
    def streak_display(self, obj):
        days = obj.streak_days
        if days >= 30:
            colour = '#22C55E'
        elif days >= 7:
            colour = '#EAB308'
        else:
            colour = '#6B7280'
        return format_html('<span style="color:{};font-weight:600">🔥 {}d</span>', colour, days)

    @admin.display(description='Points')
    def points_display(self, obj):
        pts = obj.total_points
        colour = '#A855F7' if pts >= 500 else '#3B82F6' if pts >= 100 else '#6B7280'
        return format_html('<span style="color:{};font-weight:600">⭐ {}</span>', colour, pts)

    @admin.display(description='Active')
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#22C55E;font-weight:600">✓ Active</span>')
        return format_html('<span style="color:#EF4444">✗ Inactive</span>')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'category_badge', 'icon', 'unlocked_at')
    list_filter = ('category',)
    search_fields = ('user__username', 'title')
    ordering = ('-unlocked_at',)
    date_hierarchy = 'unlocked_at'
    list_select_related = ('user',)

    @admin.display(description='Category')
    def category_badge(self, obj):
        return format_html(
            '<span style="background:#F9731622;color:#F97316;padding:2px 9px;'
            'border-radius:99px;font-size:11px;font-weight:600">{}</span>',
            obj.category.capitalize()
        )
