from django import forms
from django.utils import timezone
from .models import CertificateType, Certificate, CertificateRenewal, CertificateNotification

class DateInput(forms.DateInput):
    input_type = 'date'

class CertificateTypeForm(forms.ModelForm):
    class Meta:
        model = CertificateType
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = [
            'name', 'certificate_type', 'domain_name', 'issuer',
            'serial_number', 'issue_date', 'expiry_date', 'status',
            'key_algorithm', 'key_size', 'signature_algorithm',
            'subject_alternative_names', 'certificate_file',
            'private_key_file', 'notes'
        ]
        widgets = {
            'issue_date': DateInput(),
            'expiry_date': DateInput(),
            'subject_alternative_names': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if issue_date and expiry_date and issue_date > expiry_date:
            raise forms.ValidationError("Verilme tarihi, geçerlilik sonu tarihinden sonra olamaz.")
        
        return cleaned_data

class CertificateRenewalForm(forms.ModelForm):
    class Meta:
        model = CertificateRenewal
        fields = ['certificate', 'new_expiry_date', 'renewal_date', 'status', 'notes']
        widgets = {
            'renewal_date': DateInput(),
            'new_expiry_date': DateInput(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sadece aktif veya süresi dolmuş sertifikaları göster
        self.fields['certificate'].queryset = Certificate.objects.filter(
            status__in=['active', 'expired']
        )
        
        # Eğer bir sertifika seçilmişse, eski son geçerlilik tarihini otomatik doldur
        if 'instance' in kwargs and kwargs['instance']:
            self.initial['old_expiry_date'] = kwargs['instance'].certificate.expiry_date
    
    def clean(self):
        cleaned_data = super().clean()
        renewal_date = cleaned_data.get('renewal_date')
        new_expiry_date = cleaned_data.get('new_expiry_date')
        certificate = cleaned_data.get('certificate')
        
        if certificate and new_expiry_date:
            if new_expiry_date <= certificate.expiry_date:
                raise forms.ValidationError("Yeni geçerlilik sonu tarihi, mevcut geçerlilik sonu tarihinden sonra olmalıdır.")
        
        if renewal_date and new_expiry_date and renewal_date > new_expiry_date:
            raise forms.ValidationError("Yenileme tarihi, yeni geçerlilik sonu tarihinden sonra olamaz.")
        
        return cleaned_data

class CertificateNotificationForm(forms.ModelForm):
    class Meta:
        model = CertificateNotification
        fields = ['certificate', 'notification_type', 'sent_to', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'sent_to': forms.SelectMultiple(attrs={'size': 5}),
        }

class CertificateFilterForm(forms.Form):
    """Sertifika listesini filtrelemek için form"""
    name = forms.CharField(required=False, label="Sertifika Adı")
    domain_name = forms.CharField(required=False, label="Alan Adı")
    certificate_type = forms.ModelChoiceField(
        queryset=CertificateType.objects.all(),
        required=False,
        label="Sertifika Türü"
    )
    status = forms.ChoiceField(
        choices=[(None, '----')] + list(Certificate.STATUS_CHOICES),
        required=False,
        label="Durum"
    )
    issuer = forms.CharField(required=False, label="Sertifika Sağlayıcı")
    expiring_in_days = forms.IntegerField(
        required=False,
        min_value=1,
        label="Süresi Dolmasına Kalan Gün"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [(None, '----')] + list(Certificate.STATUS_CHOICES)

class CertificateRenewalFilterForm(forms.Form):
    """Sertifika yenileme işlemlerini filtrelemek için form"""
    certificate_name = forms.CharField(required=False, label="Sertifika Adı")
    status = forms.ChoiceField(
        choices=[(None, '----')] + list(CertificateRenewal.STATUS_CHOICES),
        required=False,
        label="Durum"
    )
    renewal_date_from = forms.DateField(
        required=False,
        widget=DateInput(),
        label="Yenileme Tarihi (Başlangıç)"
    )
    renewal_date_to = forms.DateField(
        required=False,
        widget=DateInput(),
        label="Yenileme Tarihi (Bitiş)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [(None, '----')] + list(CertificateRenewal.STATUS_CHOICES)
    
    def clean(self):
        cleaned_data = super().clean()
        renewal_date_from = cleaned_data.get('renewal_date_from')
        renewal_date_to = cleaned_data.get('renewal_date_to')
        
        if renewal_date_from and renewal_date_to and renewal_date_from > renewal_date_to:
            raise forms.ValidationError("Başlangıç tarihi, bitiş tarihinden sonra olamaz.")
        
        return cleaned_data