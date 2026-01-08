from django.contrib import admin
from ..models import Student


# *****************
# 大分類を企業ごとにフィルタリングするクラス
# このフィルタは、特定の企業に紐づく学生の大分類を選択できるようにする
# 企業が選択されている場合、その企業に紐づく学生の大分類を取得し、選択肢として表示する
# *****************
class MajorClassByCompanyFilter(admin.SimpleListFilter):
    title = '大分類'
    parameter_name = 'major_class'

    def lookups(self, request, model_admin):
        # 「company」パラメータを取得
        company_id = request.GET.get('company')
        if not company_id:
            return []

        # その企業かつ done_tel=False のレコードから distinct な major_class を取得
        qs = Student.objects.filter(
            company_id=company_id,
            done_tel=False
        )
        choices = qs.values_list('major_class', 'major_class').distinct()
        return [(mc, mc) for mc, _ in choices]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(major_class=self.value())
        return queryset
