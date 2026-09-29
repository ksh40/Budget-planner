from django import forms
from .models import Event, EventUpdate
from django import forms
from .models import Event, EventEvidence


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'location', 'date', 'time', 'banner', 'permit_number', 'issuing_authority']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_date(self):
        from datetime import date
        d = self.cleaned_data.get('date')
        if d and d < date.today():
            raise forms.ValidationError('Event date cannot be in the past.')
        return d


class EventUpdateForm(forms.ModelForm):
    class Meta:
        model = EventUpdate
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = EventEvidence
        fields = ['evidence_type', 'document', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }