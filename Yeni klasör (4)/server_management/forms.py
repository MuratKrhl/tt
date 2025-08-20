from django import forms
from django.utils import timezone
from .models import ServerType, Server, ServerMaintenanceRecord, ServerMonitoringLog, ServerDocument

class DateInput(forms.DateInput):
    input_type = 'date'

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class ServerTypeForm(forms.ModelForm):
    class Meta:
        model = ServerType
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = [
            'name', 'hostname', 'ip_address', 'server_type',
            'operating_system', 'os_version', 'cpu', 'ram',
            'storage', 'location', 'status', 'purchase_date',
            'warranty_expiry', 'notes'
        ]
        widgets = {
            'purchase_date': DateInput(),
            'warranty_expiry': DateInput(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class ServerMaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = ServerMaintenanceRecord
        fields = [
            'server', 'title', 'description', 'maintenance_type',
            'scheduled_date', 'status', 'performed_by', 'notes'
        ]
        widgets = {
            'scheduled_date': DateTimeInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class ServerMonitoringLogForm(forms.ModelForm):
    class Meta:
        model = ServerMonitoringLog
        fields = [
            'server', 'timestamp', 'log_level', 'metric_name',
            'metric_value', 'threshold', 'message', 'resolved'
        ]
        widgets = {
            'timestamp': DateTimeInput(),
            'message': forms.Textarea(attrs={'rows': 3}),
        }

class ServerDocumentForm(forms.ModelForm):
    class Meta:
        model = ServerDocument
        fields = ['server', 'title', 'document_type', 'file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ServerFilterForm(forms.Form):
    """Sunucu listesini filtrelemek için form"""
    name = forms.CharField(required=False, label="Sunucu Adı")
    hostname = forms.CharField(required=False, label="Hostname")
    ip_address = forms.CharField(required=False, label="IP Adresi")
    server_type = forms.ModelChoiceField(
        queryset=ServerType.objects.all(),
        required=False,
        label="Sunucu Türü"
    )
    operating_system = forms.ChoiceField(
        choices=[(None, '----')] + list(Server.OS_CHOICES),
        required=False,
        label="İşletim Sistemi"
    )
    status = forms.ChoiceField(
        choices=[(None, '----')] + list(Server.STATUS_CHOICES),
        required=False,
        label="Durum"
    )
    location = forms.CharField(required=False, label="Konum")
    warranty_expiring_in_days = forms.IntegerField(
        required=False,
        min_value=1,
        label="Garantisi Dolmasına Kalan Gün"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['operating_system'].choices = [(None, '----')] + list(Server.OS_CHOICES)
        self.fields['status'].choices = [(None, '----')] + list(Server.STATUS_CHOICES)

class ServerMaintenanceFilterForm(forms.Form):
    """Sunucu bakım kayıtlarını filtrelemek için form"""
    server = forms.ModelChoiceField(
        queryset=Server.objects.all(),
        required=False,
        label="Sunucu"
    )
    maintenance_type = forms.CharField(required=False, label="Bakım Türü")
    status = forms.ChoiceField(
        choices=[(None, '----')] + list(ServerMaintenanceRecord.STATUS_CHOICES),
        required=False,
        label="Durum"
    )
    scheduled_from = forms.DateField(
        required=False,
        widget=DateInput(),
        label="Planlanan Tarih (Başlangıç)"
    )
    scheduled_to = forms.DateField(
        required=False,
        widget=DateInput(),
        label="Planlanan Tarih (Bitiş)"
    )
    performed_by = forms.ModelChoiceField(
        queryset=None,  # Bu alanı __init__ içinde dolduracağız
        required=False,
        label="Gerçekleştiren"
    )
    
    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [(None, '----')] + list(ServerMaintenanceRecord.STATUS_CHOICES)
        self.fields['performed_by'].queryset = User.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        scheduled_from = cleaned_data.get('scheduled_from')
        scheduled_to = cleaned_data.get('scheduled_to')
        
        if scheduled_from and scheduled_to and scheduled_from > scheduled_to:
            raise forms.ValidationError("Başlangıç tarihi, bitiş tarihinden sonra olamaz.")
        
        return cleaned_data

class ServerMonitoringLogFilterForm(forms.Form):
    """Sunucu izleme günlüklerini filtrelemek için form"""
    server = forms.ModelChoiceField(
        queryset=Server.objects.all(),
        required=False,
        label="Sunucu"
    )
    log_level = forms.ChoiceField(
        choices=[(None, '----')] + list(ServerMonitoringLog.LOG_LEVEL_CHOICES),
        required=False,
        label="Log Seviyesi"
    )
    metric_name = forms.CharField(required=False, label="Metrik Adı")
    timestamp_from = forms.DateTimeField(
        required=False,
        widget=DateTimeInput(),
        label="Zaman (Başlangıç)"
    )
    timestamp_to = forms.DateTimeField(
        required=False,
        widget=DateTimeInput(),
        label="Zaman (Bitiş)"
    )
    resolved = forms.ChoiceField(
        choices=[(None, '----'), (True, 'Evet'), (False, 'Hayır')],
        required=False,
        label="Çözüldü"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['log_level'].choices = [(None, '----')] + list(ServerMonitoringLog.LOG_LEVEL_CHOICES)
    
    def clean(self):
        cleaned_data = super().clean()
        timestamp_from = cleaned_data.get('timestamp_from')
        timestamp_to = cleaned_data.get('timestamp_to')
        
        if timestamp_from and timestamp_to and timestamp_from > timestamp_to:
            raise forms.ValidationError("Başlangıç zamanı, bitiş zamanından sonra olamaz.")
        
        return cleaned_data