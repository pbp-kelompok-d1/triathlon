# activities/forms.py
from datetime import timedelta
from django import forms
from .models import ExerciseActivity

class ExerciseActivityForm(forms.ModelForm):

    duration = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "HH:MM"}),
        required=True,
        label="Duration (HH:MM)"
    )

    class Meta:
        model = ExerciseActivity
        fields = ['title','duration','distance','notes','sport_category','done_at']
        widgets = {
            "notes" : forms.Textarea(attrs={"rows":6}),
            "done_at": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_duration(self):
        val = self.cleaned_data["duration"]
        if not isinstance(val, str):
            return val
        txt = val.strip()
        try:
            parts = [int(p) for p in txt.split(":")]
            if len(parts) == 2:
                h, m = parts
                s = 0
            elif len(parts) == 3:
                h, m, s = parts
            if not (0 <= m < 60):
                raise ValueError
            return timedelta(hours=h, minutes=m, seconds=s)
        
        except Exception:
            raise forms.ValidationError("Duration must be HH:MM or HH:MM:SS.")