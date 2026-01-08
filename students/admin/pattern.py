from django.contrib import admin
from ..models import Pattern, PatternItem


class PatternItemInline(admin.TabularInline):
    model = PatternItem
    extra = 1


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    inlines = [PatternItemInline]
    list_display = ('company', 'created_at')
    ordering = ('company',)
