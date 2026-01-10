from django.contrib import admin, messages
from django.http import QueryDict
from django.contrib.admin.views.main import ChangeList
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Q
from django.db.models.functions import Collate

from ..models import Student, Company
from ..forms.student import StudentAdminForm
from ..filters.major_class import MajorClassByCompanyFilter
from ..filters.minor_class import MinorClassByMajorFilter
from ..filters.call_progress import CallProgressFilter
from ..filters.call_progress_detailed import DetailedCallProgressFilter
from ..filters.call_date import CallDateFilter

from .lock import LOCK_EXPIRE_MINUTES, is_locked, set_lock, clear_lock
from .urls import urlpatterns as custom_urls


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    ordering = ()

    # 複数選択→ CSV ダウンロードアクション
    actions = ['export_as_csv']
    actions_on_top = True
    actions_on_bottom = False

    # *****************
    # エントリー一覧への表示設定
    # シメイ、電話番号、大分類、1コール目結果、2コール目結果、3コール目結果、TEL終了/処理済
    # *****************
    form = StudentAdminForm
    list_display = (
        'name', 'phone_number', 'major_class',
        'first_call_notes', 'second_call_notes', 'third_call_notes', 'done_tel',
    )
    list_filter = (
        'grad_year',
        MajorClassByCompanyFilter,
        MinorClassByMajorFilter,
        CallProgressFilter,
        DetailedCallProgressFilter,
        CallDateFilter,
    )
    search_fields = ('name', 'phone_number')
    list_display_links = ('name',)

    class Media:
        css = {'all': ('students/css/admin_student.css',)}




    # *****************
    # 選択された学生を CSV 形式でダウンロードするアクション
    # *****************
    def export_as_csv(self, request, queryset):
        import io, csv
        meta = self.model._meta
        field_names = [
            'company',              'name',                'phone_number',     'process_destination',
            'data_id',              'grad_year',           'major_class',      'minor_class',
            'first_call_date',      'first_call_timezone', 'first_call_notes', 'second_call_date',
            'second_call_timezone', 'second_call_notes',   'third_call_date',  'third_call_timezone',
            'third_call_notes',     'need_process',        'done_draft',       'done_tel',
            'before_special_notes', 'after_special_notes', 'full_name',        'university',
            'faculty',              'department',          'first_entry_date'
        ]
        filename = f"{meta.verbose_name_plural}.csv"

        # 1） メモリ上に UTF-8 CSV を組み立て
        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー行：英語のフィールド名そのまま
        writer.writerow(field_names)

        # 各レコードをループ
        for obj in queryset:
            row = []
            for fn in field_names:
                val = getattr(obj, fn)
                if val is None:
                    row.append('')
                elif hasattr(val, '__str__') and not isinstance(val, (str, int, float)):
                    row.append(str(val))
                else:
                    row.append(val)
            writer.writerow(row)

        # 2） Shift_JIS (cp932) に変換して応答
        csv_data = output.getvalue().encode('cp932', errors='replace')
        response = HttpResponse(csv_data, content_type='text/csv; charset=cp932')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    export_as_csv.short_description = "選択された エントリー一覧 のダウンロード"






    def get_urls(self):
        from . import urls as custom_urls_module
        # カスタムURL を先頭に追加
        return custom_urls_module.urlpatterns + super().get_urls()




    # *****************
    # 学生の詳細画面からリスト前後への移動
    # *****************
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # URL パラメータから company を取得
        company_id = request.GET.get("company")
        if company_id:
            company = Company.objects.filter(id=company_id).first()
            if company:
                extra_context['current_company_name'] = company.name
                extra_context['current_company_id'] = company.id

        if request.method == "GET":
            try:
                cl = ChangeList(
                    request, self.model, self.list_display,
                    self.list_display_links, self.list_filter,
                    self.date_hierarchy, self.search_fields,
                    self.list_select_related, self.list_per_page,
                    self.list_max_show_all, self.list_editable, self
                )
                filtered_qs = cl.get_queryset(request)
                ordering = self.get_ordering(request)
                filtered_qs = filtered_qs.order_by(*ordering) if ordering else filtered_qs
                id_list = list(filtered_qs.values_list("id", flat=True))

                # 前後遷移に必要な情報をセッションへ保存
                request.session["filtered_student_ids"] = id_list
                request.session["_changelist_filters"] = request.GET.urlencode()
            except Exception:
                pass

        return super().changelist_view(request, extra_context)




    # *****************
    # 学生の詳細画面
    # *****************
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # URL が ChangeView (_change) / HistoryView (_history) のときは絞り込みをスキップ
        url_name = request.resolver_match.url_name
        if url_name.endswith('_change') or url_name.endswith('_history'):
            return qs

        # それ以外（＝一覧表示）のときだけ company= で絞る
        company_id = request.GET.get('company')
        if not company_id:
            # company パラメータがなければ一覧表示も何も出さない
            return qs.none()
        qs = qs.filter(company_id=company_id)

        # ここに call_date の OR 絞り込みを追加
        call_date = request.GET.get('call_date')
        if call_date:
            qs = qs.filter(
                Q(first_call_date=call_date) |
                Q(second_call_date=call_date) |
                Q(third_call_date=call_date)
            )

        return qs.order_by(Collate("name", "ja-x-icu"))




    # *****************
    # 詳細画面の読み取り専用フィールド
    # 会社名、フルネーム、シメイ、電話番号、卒業年、大学名、学部名、学科名、大分類、小分類、初回エントリー経路、学生ID
    # *****************
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                'company', 'full_name', 'name',
                'phone_number', 'grad_year', 'university',
                'faculty', 'department', 'major_class',
                'minor_class', 'process_destination', 'data_id',
            )
        return ()




    # *****************
    # カスタム変更ビュー
    # ①セッションにチェンジリストのフィルタ情報を保存
    # ②トークスクリプト URL を取得
    # ③編集ロックのチェックと設定
    # *****************
    def change_view(self, request, object_id, form_url='', extra_context=None):
        student = self.get_object(request, object_id)
        if not student:
            return super().change_view(request, object_id, form_url, extra_context)

        # ①毎回 _changelist_filters をセッションに保存（GET のときのみ）
        if request.method == "GET":
            filters = request.GET.get('_changelist_filters')
            if filters:
                request.session['_changelist_filters'] = filters
                request.session['student_back_url'] = f"{reverse('admin:students_student_changelist')}?{filters}"

        # ②filtersからQueryDictを再構成
        filters = request.GET.get('_changelist_filters', '')
        filter_qs = QueryDict(filters, mutable=False)

        # 自前フィルタの構築（必要な分だけ追加）
        qs = Student.objects.all()

        if 'company' in filter_qs:
            qs = qs.filter(company_id=filter_qs['company'])
        if 'grad_year' in filter_qs:
            qs = qs.filter(grad_year=filter_qs['grad_year'])
        if 'major_class' in filter_qs:
            qs = qs.filter(major_class=filter_qs['major_class'])

        # ②トークスクリプトURL（既存コード維持）
        talk_script_url = None
        if student.company and student.major_class:
            try:
                pattern = student.company.pattern_config
                item = pattern.items.filter(major_class=student.major_class).first()
                if item and item.talk_script:
                    talk_script_url = item.talk_script
            except Company.pattern_config.RelatedObjectDoesNotExist:
                pass

        # ③編集ロック判定
        if is_locked(student, request.user):
            messages.warning(
                request,
                f"学生「{student.name}」は「{student.locked_by}」さんが編集中です。しばらく待ってから再度開いてください。"
            )
            # 直前に保存されたチェンジリストのURLがあればそこへ、
            # なければ company パラメータだけのURLへフォールバック
            back_url = request.session.get('student_back_url')
            if back_url:
                return redirect(back_url)
            base = reverse('admin:students_student_changelist')
            return redirect(f"{base}?company={student.company_id}")

        set_lock(student, request.user)

        # extra_contextの構築
        extra_context = extra_context or {}

        extra_context.update({
            'unlock_url': reverse('admin:students_student_unlock', args=[object_id]),
            'lock_expire_minutes': LOCK_EXPIRE_MINUTES,
            'talk_script_url': talk_script_url,
        })

        return super().change_view(request, object_id, form_url, extra_context)




    # *****************
    # 保存後レスポンス
    # ・編集ロックを解除
    # ・「保存して前の画面に戻る」リクエストを処理
    # *****************
    def response_change(self, request, obj):
        clear_lock(obj)

        if "_save_back" in request.POST:
            back_url = request.session.pop("student_back_url", None)
            if back_url:
                return redirect(back_url)
        return super().response_change(request, obj)





    # *****************
    # 追加後レスポンス
    # ・編集ロックを解除して通常のレスポンスを返す
    # *****************
    def response_add(self, request, obj, post_url_continue=None):
        clear_lock(obj)
        return super().response_add(request, obj, post_url_continue)
