from django.contrib import admin
from django.utils import timezone
from ..models import Student


# *****************
# 1コール目の time zone から、「次に振り分ける」2コール目の time zone を返す。
# morning → noon, noon → evening, evening → morning
# *****************
def determine_second_call_timezone(first):
    timezones = ['morning', 'noon', 'evening']
    try:
        return timezones[(timezones.index(first) + 1) % 3]
    except ValueError:
        return None




# *****************
# 1,2コール目の time zone から、3コール目の time zone を返す。
# - 異なる 2 つなら、残りのひとつ
# - 同じなら、2コール目の次の time zone
# *****************
def determine_third_call_timezone(first, second):
    timezones = ['morning', 'noon', 'evening']
    used = {first, second}
    if len(used) == 2:
        remaining = list(set(timezones) - used)
        return remaining[0] if remaining else None
    else:
        try:
            idx = timezones.index(second)
            return timezones[(idx + 1) % 3]
        except ValueError:
            return None




# *****************
# 架電時間帯の詳細フィルター
# - 2コール目の時間帯（朝、昼、夕）
# - 3コール目の時間帯（朝、昼、夕）
# *****************
class DetailedCallProgressFilter(admin.SimpleListFilter):
    title = '架電時間帯'
    parameter_name = 'detailed_call'

    def lookups(self, request, model_admin):
        return [
            ('2_morning', '2コール目（朝）'),
            ('2_noon',    '2コール目（昼）'),
            ('2_evening','2コール目（夕）'),
            ('3_morning', '3コール目（朝）'),
            ('3_noon',    '3コール目（昼）'),
            ('3_evening','3コール目（夕）'),
        ]

    # *****************
    # クエリセットをフィルタリングする
    # - 2コール目の時間帯が指定された場合、1コール目の時間帯から次の時間帯を決定し、それに一致するレコードを抽出
    # - 3コール目の時間帯が指定された場合、1コール目と2コール目の時間帯から次の時間帯を決定し、それに一致するレコードを抽出
    # - それ以外は何もしない
    # *****************
    def queryset(self, request, queryset):
        v = self.value()
        today = timezone.localdate()

        # ベース queryset を作る
        if v and v.startswith('2_'):
            # ２コール目対象のみ抽出
            base2 = queryset.filter(
                done_tel=False,
                first_call_date__isnull=False,
                second_call_date__isnull=True,
                first_call_date__lt=today
            )
            # "次の時間帯" が一致するものだけ残す
            target_tz = v.split('_')[1]  # 'morning' etc.
            # pks を Python 側で決めてからINで絞り込む
            pks = [
                s.pk
                for s in base2
                if determine_second_call_timezone(s.first_call_timezone) == target_tz
            ]
            return queryset.filter(pk__in=pks)

        if v and v.startswith('3_'):
            # ３コール目対象のみ抽出
            base3 = queryset.filter(
                done_tel=False,
                first_call_date__isnull=False,
                second_call_date__isnull=False,
                third_call_date__isnull=True,
                second_call_date__lt=today
            )
            target_tz = v.split('_')[1]
            pks = [
                s.pk
                for s in base3
                if determine_third_call_timezone(
                    s.first_call_timezone,
                    s.second_call_timezone
                ) == target_tz
            ]
            return queryset.filter(pk__in=pks)

        # それ以外は何もしない
        return queryset
