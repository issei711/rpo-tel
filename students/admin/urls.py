from django.urls import path
from .unlock_view import unlock_view

app_name = 'students_admin'
urlpatterns = [
    # 詳細画面離脱時に呼ぶエンドポイント
    path(
        '<int:object_id>/unlock/',
        unlock_view,
        name='students_student_unlock'
    ),
]
