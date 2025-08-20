from django import forms
from .models import Server, ServerType, Application, ApplicationType, MaintenanceRecord, ApplicationDocument

class ServerForm(forms.ModelForm):
    """Sunucu formu"""
    class Meta:
        model = Server
        fields = ['name', 'hostname', 'ip_address', 'operating_system', 'server_type', 'status', 'description']

class ServerTypeForm(forms.ModelForm):
    """Sunucu tipi formu"""
    class Meta:
        model = ServerType
        fields = ['name', 'description']

class ApplicationForm(forms.ModelForm):
    """Uygulama formu"""
    class Meta:
        model = Application
        fields = ['name', 'application_type', 'server', 'port', 'install_path', 'version', 'status', 'description']

class ApplicationTypeForm(forms.ModelForm):
    """Uygulama tipi formu"""
    class Meta:
        model = ApplicationType
        fields = ['name', 'description']

class MaintenanceRecordForm(forms.ModelForm):
    """Bakım kaydı formu"""
    class Meta:
        model = MaintenanceRecord
        fields = ['title', 'description', 'scheduled_start', 'scheduled_end', 'actual_start', 'actual_end', 'status']
        widgets = {
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ApplicationDocumentForm(forms.ModelForm):
    """Uygulama dokümanı formu"""
    class Meta:
        model = ApplicationDocument
        fields = ['title', 'document_type', 'file', 'description']

class ApplicationFilterForm(forms.Form):
    """Uygulama filtreleme formu"""
    application_type = forms.ModelChoiceField(queryset=ApplicationType.objects.all(), required=False)
    server = forms.ModelChoiceField(queryset=Server.objects.all(), required=False)
    status = forms.ChoiceField(choices=[('', '---')] + list(Application.STATUS_CHOICES), required=False)

class ServerFilterForm(forms.Form):
    """Sunucu filtreleme formu"""
    server_type = forms.ModelChoiceField(queryset=ServerType.objects.all(), required=False)
    operating_system = forms.ChoiceField(choices=[('', '---')] + list(Server.OPERATING_SYSTEM_CHOICES), required=False)
    status = forms.ChoiceField(choices=[('', '---')] + list(Server.STATUS_CHOICES), required=False)