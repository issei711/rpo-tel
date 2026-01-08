from django.contrib import admin
from django.urls import path
from students.views import (
    portal_index,
    redirect_to_company_students,
    upload_csv,
    download_csv_template,
    exchange_csv,
)

urlpatterns = [
    # ✅ 企業別ポータルページ（admin外）
    path("portal/companies/", portal_index, name="company_portal_index"),

    # ✅ 学生一覧画面にリダイレクト（company=ID を付与）
    path("portal/students/<int:company_id>/", redirect_to_company_students, name="company_student_redirect"),

    # ✅ CSVアップロード画面
    path("portal/upload/<int:company_id>/", upload_csv, name="student_upload_csv"),

    # ✅️ CSVテンプレートダウンロード
    path("portal/upload/<int:company_id>/template/", download_csv_template, name="student_csv_template"),

    # ✅ 汎用ファイル変換画面
    path("portal/exchange-csv/", exchange_csv, name="exchange_csv"),

    # ✅ Djangoの標準管理画面
    path("admin/", admin.site.urls),
]
