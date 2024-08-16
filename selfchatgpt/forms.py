# forms.py
from django import forms

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV 파일 업로드",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )