from django.contrib import admin
from ..models import CallResult


@admin.register(CallResult)
class CallResultAdmin(admin.ModelAdmin):
    list_display = ('name', 'results')
    search_fields = ('name',)
