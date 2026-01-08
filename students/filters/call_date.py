# students/filters/call_date.py
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


# *****************
# 架電日のフィルター
# ・指定した日付が 1〜3 コール目のいずれかに該当するレコードを抽出
# *****************
class CallDateFilter(admin.SimpleListFilter):
    title = _('架電日')
    parameter_name = 'call_date'

    def lookups(self, request, model_admin):
        # フィルタの選択肢は動的に生成しない（空リスト返却）
        return []

    def queryset(self, request, queryset):
        # クエリパラメータがなければ絞り込まず全件返却
        val = self.value()
        if not val:
            return queryset
        # first_call_date, second_call_date, third_call_date のいずれかが選択日と一致するものを OR 条件で抽出
        return queryset.filter(
            Q(first_call_date=val) |
            Q(second_call_date=val) |
            Q(third_call_date=val)
        )
