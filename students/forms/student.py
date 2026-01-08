from django import forms
from ..models import Student, PatternItem


# *****************
# フィールドの動的選択肢設定
# ・company_id と major_class の組み合わせから PatternItem を取得
# ・該当する分類(classification)があれば、その結果リストを
#   1〜3 コール目の「通話結果」フィールドの選択肢として設定
# *****************
class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        company_id = (
            getattr(self.instance, 'company_id', None)
            or self.initial.get("company")
            or self.data.get("company")
        )
        major_class = (
            getattr(self.instance, 'major_class', None)
            or self.initial.get("major_class")
            or self.data.get("major_class")
        )

        if company_id and major_class:
            pattern_item = (
                PatternItem.objects
                .filter(pattern__company_id=company_id, major_class=major_class)
                .select_related("classification")
                .first()
            )

            if pattern_item and pattern_item.classification:
                results = pattern_item.classification.get_result_list()
                select_widget = forms.Select(
                    choices=[("", "---------")] + [(r, r) for r in results]
                )
                for field in ["first_call_notes", "second_call_notes", "third_call_notes"]:
                    self.fields[field].widget = select_widget
