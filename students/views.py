from django.shortcuts import render, redirect
from django.contrib import messages
import csv
import io
import pandas as pd
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
from .models import Company, Student, Pattern
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404


# -------------------------
# 1コール目、2コール目の時間帯から3コール目の時間帯を決定する
# -------------------------
def determine_third_call_timezone(first, second):
    timezones = ['morning', 'noon', 'evening']
    used = {first, second}
    if len(used) == 2:
        remaining = list(set(timezones) - used)
        return remaining[0] if remaining else None
    try:
        idx = timezones.index(second)
        return timezones[(idx + 1) % 3]
    except ValueError:
        return None



# -------------------------
# 編集ロックのメソッド
# -------------------------
@require_POST
def lock_keepalive(request, pk):
    student = get_object_or_404(Student, pk=pk)
    # ロックが空いていたら取得、既に自分が持っていたら時刻更新
    if not student.is_locked(request.user) or student.locked_by == request.user:
        student.acquire_lock(request.user)
        return JsonResponse({'status':'locked'})
    return JsonResponse({'status':'busy'}, status=423)




# -------------------------
# ポータル：企業一覧
# -------------------------
def portal_index(request):
    today = timezone.localdate()

    # GET パラメータから日付を取得（ISO フォーマット 'YYYY-MM-DD'）
    call_date_str = request.GET.get('call_date')
    try:
        sel_date = datetime.fromisoformat(call_date_str).date() if call_date_str else today
    except (ValueError, TypeError):
        sel_date = today

    companies_data = []

    for company in Company.objects.all():
        # ① 日付集計（OR で合算）
        count_on_date = Student.objects.filter(
            company=company,
            done_tel=False
        ).filter(
            Q(first_call_date=sel_date) |
            Q(second_call_date=sel_date) |
            Q(third_call_date=sel_date)
        ).count()

        # ② 処理必要：need_process=True & done_draft=False & done_tel=False
        count_need_process = Student.objects.filter(
            company=company,
            need_process=True,
            done_draft=False,
            done_tel=False,
        ).count()

        # ③ Wチェック必要：done_draft=True & done_tel=False
        count_wcheck = Student.objects.filter(
            company=company,
            done_draft=True,
            done_tel=False,
        ).count()

        count1 = Student.objects.filter(
            company=company,
            first_call_date__isnull=True,
            done_tel=False
        ).count()

        base2 = Student.objects.filter(
            company=company,
            first_call_date__isnull=False,
            second_call_date__isnull=True,
            first_call_date__lt=today,
            done_tel=False
        )

        count2 = {'morning': 0, 'noon': 0, 'evening': 0}
        for s in base2:
            if s.first_call_timezone == 'morning':
                count2['noon'] += 1
            elif s.first_call_timezone == 'noon':
                count2['evening'] += 1
            elif s.first_call_timezone == 'evening':
                count2['morning'] += 1

        base3 = Student.objects.filter(
            company=company,
            first_call_date__isnull=False,
            second_call_date__isnull=False,
            third_call_date__isnull=True,
            second_call_date__lt=today,
            done_tel=False
        )

        count3 = {'morning':0,'noon':0,'evening':0}
        for s in base3:
            tz3 = determine_third_call_timezone(s.first_call_timezone, s.second_call_timezone)
            if tz3 in count3:
                count3[tz3] += 1

        companies_data.append({
            'company': company,
            'date': sel_date.isoformat(),
            'count_on_date': count_on_date,
            'count_need_process': count_need_process,
            'count_wcheck': count_wcheck,
            'count1': count1,
            'count2': count2,
            'count3': count3,
        })

    return render(request, "portal/index.html", {
        "companies_data": companies_data,
        "selected_date": sel_date.isoformat(),
    })


def redirect_to_company_students(request, company_id):
    return redirect(f"/admin/students/student/?_facets=True&company={company_id}")




# -------------------------
# 学生一覧へリダイレクト（Django admin に facets, company パラメータを付ける）
# -------------------------
def redirect_to_company_students(request, company_id):
    return redirect(f"/admin/students/student/?_facets=True&company={company_id}")




# ***********************************************************************************************************************************

COLUMNS = [
    # key, label, options
    ("company", "企業名", {"required": True}),
    ("name", "シメイ", {"required": True}),
    ("phone_number", "電話番号", {"required": True}),
    ("process_destination", "初回エントリー経路", {}),
    ("data_id", "学生ID", {}),
    ("grad_year", "卒年度", {"required": True, "type": "int"}),
    ("major_class", "大分類", {"required": True}),
    ("minor_class", "小分類", {"required": True}),
    ("first_call_date", "1コール目", {"type": "date"}),
    ("first_call_timezone", "1コール目時間区分", {}),
    ("first_call_notes", "1コール目結果", {}),
    ("second_call_date", "2コール目", {"type": "date"}),
    ("second_call_timezone", "2コール目時間区分", {}),
    ("second_call_notes", "2コール目結果", {}),
    ("third_call_date", "3コール目", {"type": "date"}),
    ("third_call_timezone", "3コール目時間区分", {}),
    ("third_call_notes", "3コール目結果", {}),
    ("need_process", "処理必要", {}),
    ("done_draft", "Wチェ必要", {}),
    ("done_tel", "TEL終了/処理済", {}),
    ("before_special_notes", "TEL前特記事項", {}),
    ("after_special_notes", "TEL後特記事項", {}),
    ("full_name", "氏名", {"required": True}),
    ("university", "大学", {}),
    ("faculty", "学部", {}),
    ("department", "学科", {}),
    ("first_entry_date", "初回エントリー日", {"type": "date"}),
]

# ===== 派生定義（ここから下は触らない） =====
CSV_HEADERS = [(key, label) for key, label, _ in COLUMNS]
OUTPUT_COLUMNS = [key for key, _, _ in COLUMNS]
REQUIRED = [key for key, _, opt in COLUMNS if opt.get("required")]
INT_FIELDS = [key for key, _, opt in COLUMNS if opt.get("type") == "int"]
DATE_FIELDS = [key for key, _, opt in COLUMNS if opt.get("type") == "date"]


# -------------------------
# CSVアップロード
# -------------------------
def upload_csv(request, company_id):
    company = Company.objects.filter(id=company_id).first()
    if not company:
        messages.error(request, "指定された企業が見つかりません。")
        return redirect("students:portal_index")

    if request.method == "POST" and request.FILES.get("csv_file"):
        file = request.FILES["csv_file"]
        raw = file.read()

        for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                text = None

        if text is None:
            messages.error(
                request,
                "CSVの文字コードが不正です。UTF-8 または Shift_JIS（CP932）で保存してください。"
            )
            return redirect(request.path)

        reader = csv.DictReader(text.splitlines())

        # ① 全行チェック
        pattern = Pattern.objects.filter(company=company).first()
        pattern_major_classes = set()
        if pattern:
            pattern_major_classes = set(pattern.items.values_list("major_class", flat=True))

        for row_no, row in enumerate(reader, start=2):
            # 企業名チェック
            if row.get("company") != company.name:
                messages.error(request, f"{row_no}行目: company が一致しません。")
                return redirect(request.path)

            # major_class が PatternItem にあるかチェック
            major_class = row.get("major_class")
            if major_class not in pattern_major_classes:
                messages.error(request, f"{row_no}行目: major_class '{major_class}' がパターン一覧にまだ登録されていません。")
                return redirect(request.path)

            # 必須フィールドチェック
            for key in REQUIRED:
                if not row.get(key):
                    messages.error(request, f"{row_no}行目: 「{key}」が空欄です。")
                    return redirect(request.path)

            # 整数フィールドチェック
            for key in INT_FIELDS:
                try:
                    int(row[key])
                except (TypeError, ValueError):
                    messages.error(request, f"{row_no}行目: 「{key}」が整数ではありません。")
                    return redirect(request.path)

            # 日付フィールドチェック (YYYY-MM-DD 形式を想定)
            for key in DATE_FIELDS:
                val = row.get(key)
                if val:
                    try:
                        datetime.strptime(val, "%Y-%m-%d")
                    except ValueError:
                        messages.error(
                            request,
                            f"{row_no}行目: 「{key}」を YYYY-MM-DD 形式で入力してください。"
                        )
                        return redirect(request.path)

        # ② 問題なければ再読み込みして登録
        file.seek(0)
        text = file.read().decode("shift_jis", errors="ignore")
        reader = csv.DictReader(text.splitlines())
        created = 0

        for row in reader:
            Student.objects.create(
                company=company,
                data_id=row.get("data_id"),                           grad_year=int(row["grad_year"]),                      major_class=row["major_class"],
                minor_class=row["minor_class"],                       name=row["name"],                                     phone_number=row["phone_number"],
                process_destination=row.get("process_destination"),   before_special_notes=row.get("before_special_notes"), first_call_date=row.get("first_call_date") or None,
                first_call_timezone=row.get("first_call_timezone"),   first_call_notes=row.get("first_call_notes"),         second_call_date=row.get("second_call_date") or None,
                second_call_timezone=row.get("second_call_timezone"), second_call_notes=row.get("second_call_notes"),       third_call_date=row.get("third_call_date") or None,
                third_call_timezone=row.get("third_call_timezone"),   third_call_notes=row.get("third_call_notes"),         need_process=(row.get("need_process") == "True"),
                done_draft=(row.get("done_draft") == "True"),         done_tel=(row.get("done_tel") == "True"),             after_special_notes=row.get("after_special_notes"),
                full_name=row["full_name"],                           university=row["university"],                         faculty=row["faculty"],
                department=row["department"],                         first_entry_date=row.get("first_entry_date") or None,
            )
            created += 1

        messages.success(request, f"新規登録完了: {created} 件")
        return redirect(request.path)

    return render(request, "portal/upload_csv.html", {
        "company": company,
        "csv_headers": CSV_HEADERS,
        "required_fields": REQUIRED,
    })




# -------------------------
# CSVテンプレートダウンロード
# -------------------------
def download_csv_template(request, company_id):
    company = Company.objects.filter(id=company_id).first()
    if not company:
        return HttpResponse("企業が見つかりませんでした。", status=404)

    output = io.StringIO()
    writer = csv.writer(output)

    # 英字ヘッダ（OUTPUT_COLUMNS から自動生成）
    writer.writerow(OUTPUT_COLUMNS)

    # サンプル1行目
    writer.writerow([company.name] + [""] * (len(OUTPUT_COLUMNS) - 1))

    csv_data = output.getvalue().encode("cp932", errors="replace")
    response = HttpResponse(csv_data, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{company.name}_template.csv"'
    return response


# -------------------------
# CSV変換
# -------------------------

# フォーマット選択肢
FORMAT_CHOICES = (
    ('Airワーク', 'Airワーク'),
    ('riksak', 'riksak'),
    ('マイナビ', 'マイナビ'),
    ('i-web', 'i-web'),
    ('採マネ', '採マネ'),
    ('かんりくん', 'かんりくん'),
)

# 各フォーマットごとの「元ヘッダー名 → 標準ヘッダー名」マッピング
FORMAT_MAPPINGS = {
    'Airワーク': {
        'ふりがな': 'name',
        '電話番号': 'phone_number',
        '応募ID': 'data_id',
        '応募者名': 'full_name',
        '学校名': 'university',
        '学部・学科・専攻': 'faculty',
        '応募日時': 'first_entry_date',
    },
    'riksak': {
        'カナ氏名': 'name',
        '電話番号': 'phone_number',
        '応募者コード': 'data_id',
        '氏名': 'full_name',
        '学校名': 'university',
        '学部名': 'faculty',
        '学科名': 'department',
        '登録日時': 'first_entry_date',
    },
    'マイナビ': {
        '電話番号（携帯）': 'phone_number',
        '応募者管理ID': 'data_id',
        '学校名': 'university',
        '学部名': 'faculty',
        '学科名': 'department',
        '初回エントリー日時': 'first_entry_date',
        # 結合用（実際に出力には直接使わない）
        "姓": "__last_name",
        "名": "__first_name",
        "姓カナ": "__last_name_kana",
        "名カナ": "__first_name_kana",
    },
    'i-web': {
        'カナ氏名': 'name',
        '携帯電話番号': 'phone_number',
        '応募者コード': 'data_id',
        '漢字氏名': 'full_name',
        '大学名称': 'university',
        '学部名称': 'faculty',
        '学科名称': 'department',
        '初回登録日': 'first_entry_date',
    },
    '採マネ': {
        'フリガナ': 'name',
        '電話番号': 'phone_number',
        'ID': 'data_id',
        '本名': 'full_name',
        '学校名': 'university',
        '学部・学科': 'faculty',
    },
    'かんりくん': {
        'ID': 'data_id',
        '携帯電話番号': 'phone_number',
        '学校名': 'university',
        '学部名': 'faculty',
        '学科名': 'department',
        'エントリー日': 'first_entry_date',
        # 結合用（実際に出力には直接使わない）
        "姓": "__last_name",
        "名": "__first_name",
        "セイ": "__last_name_kana",
        "メイ": "__first_name_kana",
    },
}

def exchange_csv(request, company_id=None):
    context = {"company_id": company_id, "formats": FORMAT_MAPPINGS.keys()}

    if request.method == "POST":
        file = request.FILES.get("file")
        format_choice = request.POST.get("format_choice")

        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            context["error"] = "CSVまたはExcelファイルをアップロードしてください"
            return render(request, "portal/exchange_csv.html", context)

        mapping = FORMAT_MAPPINGS.get(format_choice, {})
        converted_df = pd.DataFrame(columns=OUTPUT_COLUMNS)

        # 基本のマッピング処理
        for src_col, target_col in mapping.items():
            if src_col in df.columns and not target_col.startswith("__"):
                converted_df[target_col] = df[src_col]

        # マイナビ・かんりくん用の特殊処理
        if format_choice == "マイナビ":
            if "姓" in df.columns and "名" in df.columns:
                converted_df["full_name"] = df["姓"].astype(str) + " " + df["名"].astype(str)
            if "姓カナ" in df.columns and "名カナ" in df.columns:
                converted_df["name"] = df["姓カナ"].astype(str) + " " + df["名カナ"].astype(str)
        elif format_choice == "かんりくん":
            if "姓" in df.columns and "名" in df.columns:
                converted_df["full_name"] = df["姓"].astype(str) + " " + df["名"].astype(str)
            if "セイ" in df.columns and "メイ" in df.columns:
                converted_df["name"] = df["セイ"].astype(str) + " " + df["メイ"].astype(str)

        # ===== 採マネ用の特殊処理 =====
        if format_choice == "採マネ" and "大学名" in df.columns:
            # 大学名列をアンダーバーで分割
            split_cols = df["大学名"].astype(str).str.split("_", expand=True)

            # 分割結果を標準カラムに格納
            converted_df["university"] = split_cols[0].fillna("").str.strip()
            if split_cols.shape[1] > 1:
                converted_df["faculty"] = split_cols[1].fillna("").str.strip()
            if split_cols.shape[1] > 2:
                converted_df["department"] = split_cols[2].fillna("").str.strip()

        # 存在しない列は空白
        for col in OUTPUT_COLUMNS:
            if col not in converted_df.columns:
                converted_df[col] = ""

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = f'attachment; filename="converted_{format_choice}_{company_id}.csv"'
        converted_df.to_csv(response, index=False)
        return response

    return render(request, "portal/exchange_csv.html", context)
