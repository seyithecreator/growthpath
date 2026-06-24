from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'rec_type', 'rank', 'confidence',
                    'is_read', 'is_actioned', 'generated_at')
    list_filter = ('rec_type', 'is_read', 'is_actioned')
    search_fields = ('title', 'user__username', 'description')
    ordering = ('user', 'rank')
    date_hierarchy = 'generated_at'
    readonly_fields = ('generated_at', 'read_at')
    fieldsets = (
        (None, {'fields': ('user', 'rec_type', 'rank', 'title', 'description',
                           'action_label', 'icon', 'confidence', 'tags')}),
        ('Linked Objects', {'fields': ('goal', 'skill')}),
        ('Status', {'fields': ('is_read', 'is_actioned', 'generated_at', 'read_at')}),
    )
