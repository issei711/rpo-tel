from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta


# *****************
# 企業のモデル
# *****************
class Company(models.Model):
    name = models.CharField('企業名', max_length=100, unique=True)

    class Meta:
        verbose_name = '企業'
        verbose_name_plural = '企業一覧'

    def __str__(self):
        return self.name




# *****************
# 架電結果のモデル
# 管理画面で自由に登録→その後学生のコール結果に利用
# *****************
class CallResult(models.Model):
    name = models.CharField('分類キー', max_length=50, unique=True)
    results = models.TextField('コール結果リスト（カンマ区切り）')

    def get_result_list(self):
        return [x.strip() for x in self.results.split(',') if x.strip()]

    class Meta:
        verbose_name = 'コール結果'
        verbose_name_plural = 'コール結果一覧'

    def __str__(self):
        return self.name




# *****************
# 企業名に紐づく大分類、分類（直確TEL、即TELなど）、トークスクリプトの設定
# *****************
class Pattern(models.Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="pattern_config", verbose_name='企業名')
    created_at = models.DateTimeField('登録日時', auto_now_add=True)

    class Meta:
        verbose_name = 'パターン'
        verbose_name_plural = 'パターン一覧'

    def __str__(self):
        return f"{self.company.name}のパターン"




# *****************
# パターンの中身
# *****************
class PatternItem(models.Model):
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="items")
    major_class = models.CharField("大分類", max_length=100)
    classification = models.ForeignKey(CallResult, on_delete=models.SET_NULL, null=True, verbose_name='分類')
    talk_script = models.URLField("トークスクリプトURL", blank=True, null=True)

    def __str__(self):
        return ""




# *****************
# 学生のモデル
# *****************
class Student(models.Model):
    CALL_TIMEZONE_CHOICES = [
        ('morning', '朝（9:00〜12:00）'),
        ('noon', '昼（12:00〜15:00）'),
        ('evening', '夕（15:00〜18:00）'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='students', null=True, verbose_name='企業名')

    grad_year = models.IntegerField('卒年度', blank=True, null=True)
    major_class = models.CharField('大分類', max_length=100, blank=True, null=True)
    minor_class = models.CharField('小分類', max_length=100, blank=True, null=True)
    before_special_notes = models.TextField('TEL前特記事項', blank=True, null=True)
    process_destination = models.CharField('初回エントリー経路', max_length=100, blank=True, null=True)
    data_id = models.CharField('学生ID', max_length=20, blank=True, null=True)
    name = models.CharField('シメイ', max_length=100, blank=True, null=True)
    phone_number = models.CharField('電話番号', max_length=20, blank=True, null=True)

    first_call_date = models.DateField('1コール目', blank=True, null=True)
    first_call_timezone = models.CharField('1コール目時間区分', max_length=50, blank=True, null=True, choices=CALL_TIMEZONE_CHOICES)
    first_call_notes = models.CharField('1コール目結果', max_length=100, blank=True, null=True)
    second_call_date = models.DateField('2コール目', blank=True, null=True)
    second_call_timezone = models.CharField('2コール目時間区分', max_length=50, blank=True, null=True, choices=CALL_TIMEZONE_CHOICES)
    second_call_notes = models.CharField('2コール目結果', max_length=100, blank=True, null=True)
    third_call_date = models.DateField('3コール目', blank=True, null=True)
    third_call_timezone = models.CharField('3コール目時間区分', max_length=50, blank=True, null=True, choices=CALL_TIMEZONE_CHOICES)
    third_call_notes = models.CharField('3コール目結果', max_length=100, blank=True, null=True)

    need_process = models.BooleanField('処理必要', default=False, blank=True, null=True)
    done_draft = models.BooleanField('Wチェ必要', default=False, blank=True, null=True)
    done_tel = models.BooleanField('TEL終了/処理済', default=False, blank=True, null=True)
    after_special_notes = models.TextField('TEL後特記事項', blank=True, null=True)

    full_name = models.CharField('氏名', max_length=100, blank=True, null=True)
    university = models.CharField('大学', max_length=100, blank=True, null=True)
    faculty = models.CharField('学部', max_length=100, blank=True, null=True)
    department = models.CharField('学科', max_length=100, blank=True, null=True)
    first_entry_date = models.DateField('初回エントリー日', blank=True, null=True)

    created_at = models.DateTimeField('登録日時', auto_now_add=True)

    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="編集中ユーザー")
    locked_at = models.DateTimeField(null=True, blank=True, verbose_name="ロック時刻")

    def is_locked(self, user, expire_minutes=1):
        """
        他ユーザーによってロック中かどうか。
        ロック有効期間はデフォルト 1 分。
        locked_at は「最後にブラウザが生存確認した時刻」を示すように更新します。
        """
        if not self.locked_by or not self.locked_at:
            return False
        # 自分がロック中なら常に編集可能
        if self.locked_by == user:
            return False
        # expire_minutes より古ければロック切れ
        return (timezone.now() - self.locked_at) < timedelta(minutes=expire_minutes)

    def acquire_lock(self, user):
        """
        編集開始／生存確認用。呼び出し側で
        ・画面を開いたとき（初回）と
        ・定期的（例:30秒ごと）に
        これを呼ぶようにします。
        """
        self.locked_by = user
        self.locked_at = timezone.now()
        self.save(update_fields=('locked_by', 'locked_at'))

    def release_lock(self):
        """
        明示的にロック解除したいときに呼び出す。
        """
        self.locked_by = None
        self.locked_at = None
        self.save(update_fields=('locked_by', 'locked_at'))

    class Meta:
        verbose_name = 'エントリー'
        verbose_name_plural = 'エントリー一覧'

    def __str__(self):
        return self.name
