from django.contrib import admin
from ..models import Student


# *****************
# 小分類を大分類ごとにフィルタリングするクラス
# このフィルタは、特定の企業と大分類に紐づく学生の小分類を選択できるようにする
# 企業と大分類が選択されている場合、その組み合わせに紐づく学生の小分類を取得し、選択肢として表示する
# *****************
class MinorClassByMajorFilter(admin.SimpleListFilter):
    title = '小分類'
    parameter_name = 'minor_class'

    def lookups(self, request, model_admin):
        # 1) クエリパラメータから「企業ID」「大分類」を取得
        company_id  = request.GET.get('company')
        major_class = request.GET.get('major_class')
        if not company_id or not major_class:
            return []

        # 2) 「当該企業・大分類・小分類」ごとに、TEL終了（done_tel=True）ではないレコードが 1 件以上ある小分類だけを取得
        #    -> 具体的には、まずすべての小分類を distinct で一覧化し、
        #       さらにそのうち「done_tel が False のレコードを含む」ものだけを残す

        qs = Student.objects.filter(
            company_id=company_id,
            major_class=major_class,
            done_tel=False
        )

        # 3) 上記クエリセットから distinct な minor_class 値を取り出す
        choices = qs.values_list('minor_class', 'minor_class').distinct()

        # 4) タプル (value, display) のリスト形式で返却
        return [(mc, mc) for mc, _ in choices]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(minor_class=self.value())
        return queryset
