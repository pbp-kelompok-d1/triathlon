# activities/forms.py
from datetime import timedelta
from django import forms
from .models import ExerciseActivity
from place.models import Place

class ExerciseActivityForm(forms.ModelForm):

    duration = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "HH:MM"}),
        required=True,
        label="Duration (HH:MM)"
    )

    place_id = forms.IntegerField(required=False, min_value=1, label="Place ID")

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
        
    def clean_place_id(self):
        pid = self.cleaned_data.get('place_id')
        if pid in (None, ''):
            return None
        try:
            return Place.objects.get(pk=pid)
        except Place.DoesNotExist:
            raise forms.ValidationError("No Place found with that ID.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        place = self.cleaned_data.get('place_id')
        if place is not None:      # place is either a Place instance or None
            instance.place = place
        if commit:
            instance.save()
        return instance