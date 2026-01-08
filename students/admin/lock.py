from datetime import timedelta
from django.utils import timezone

# ロックの最長有効時間（分）
LOCK_EXPIRE_MINUTES = 1


def is_locked(student, user):
    """
    他ユーザーによってロック中かを判定。
    同一ユーザーならロック継続（タイムスタンプ更新）。
    他ユーザーは1分以内ならロック中、それ以降は解除扱い。
    """
    # ① ロックされていない or clear_lock が走っていれば編集可
    if not student.locked_by:
        return False

    # ② 同じユーザーならリフレッシュ＆編集可
    if student.locked_by == user:
        set_lock(student, user)
        return False

    # ③ 明示的に clear_lock() が呼ばれていない限りロック中
    # 　→ フォールバックでタイムアウトを使う
    expired = (timezone.now() - student.locked_at) >= timedelta(minutes=LOCK_EXPIRE_MINUTES)
    return not expired


def set_lock(student, user):
    """
    student を user でロック。locked_at を今に更新。
    同一ユーザーが再度アクセスしたときにも呼ぶことで
    タイムアウト延長を実現。
    """
    student.locked_by = user
    student.locked_at = timezone.now()
    student.save(update_fields=('locked_by', 'locked_at'))


def clear_lock(student):
    """ロックを明示解除する"""
    student.locked_by = None
    student.locked_at = None
    student.save(update_fields=('locked_by', 'locked_at'))
