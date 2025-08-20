from django import forms
from django.utils import timezone
from ckeditor.widgets import CKEditorWidget
from .models import Announcement, Tag

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class AnnouncementForm(forms.ModelForm):
    """Duyuru oluşturma ve düzenleme formu"""
    content = forms.CharField(widget=CKEditorWidget(), label='İçerik')
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Etiketler'
    )
    
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'announcement_type', 'priority',
            'product', 'start_date', 'end_date', 'pinned', 'status', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'announcement_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': DateTimeInput(attrs={'class': 'form-control'}),
            'end_date': DateTimeInput(attrs={'class': 'form-control'}),
            'pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Varsayılan değerler
        if not self.instance.pk:  # Yeni kayıt oluşturuluyorsa
            self.fields['start_date'].initial = timezone.now()
            self.fields['end_date'].initial = timezone.now() + timezone.timedelta(days=30)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('Bitiş tarihi başlangıç tarihinden önce olamaz.')
        
        return cleaned_data


class AnnouncementFilterForm(forms.Form):
    """Duyuruları filtreleme formu"""
    FILTER_TYPE_CHOICES = (
        ('', 'Tüm Türler'),
    ) + Announcement.TYPE_CHOICES
    
    FILTER_PRIORITY_CHOICES = (
        ('', 'Tüm Öncelikler'),
    ) + Announcement.PRIORITY_CHOICES
    
    FILTER_STATUS_CHOICES = (
        ('', 'Tüm Durumlar'),
    ) + Announcement.STATUS_CHOICES
    
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Başlık ara...'}),
        label='Başlık'
    )
    announcement_type = forms.ChoiceField(
        choices=FILTER_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tür'
    )
    priority = forms.ChoiceField(
        choices=FILTER_PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Öncelik'
    )
    product = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün ara...'}),
        label='Ürün'
    )
    status = forms.ChoiceField(
        choices=FILTER_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Durum'
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Etiketler'
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Başlangıç Tarihi'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Bitiş Tarihi'
    )


class TagForm(forms.ModelForm):
    """Etiket oluşturma ve düzenleme formu"""
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AnnouncementFileForm(forms.Form):
    """Duyuruya dosya ekleme formu"""
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'multiple': True}),
        label='Dosya'
    )