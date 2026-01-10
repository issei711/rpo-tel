from django.contrib import admin


# *****************
# 架電ステータスフィルター
# *****************
class CallProgressFilter(admin.SimpleListFilter):
    title = '架電ステータス'
    parameter_name = 'call_progress'

    def lookups(self, request, model_admin):
        return [
            ('first', '1コール目'),
            ('second', '2コール目'),
            ('third', '3コール目'),
            ('third_done_not_closed', '3コール完了・未TEL終了'),
            ('done', 'TEL終了/処理済'),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == 'first':
            return queryset.filter(
                first_call_date__isnull=True,
                done_tel=False
                )
        if v == 'second':
            return queryset.filter(
                first_call_date__isnull=False,
                second_call_date__isnull=True,
                done_tel=False
                )
        if v == 'third':
            return queryset.filter(
                first_call_date__isnull=False,
                second_call_date__isnull=False,
                third_call_date__isnull=True,
                done_tel=False
            )
        if v == 'third_done_not_closed':
            return queryset.filter(
                first_call_date__isnull=False,
                second_call_date__isnull=False,
                third_call_date__isnull=False,
                done_tel=False
            )
        if v == 'done':
            return queryset.filter(
                done_tel=True
                )
        return queryset
