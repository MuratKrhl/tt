from django.db import models
from django.contrib.auth.models import User

class ServerType(models.Model):
    """Sunucu tipi modeli"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Server(models.Model):
    """Sunucu modeli"""
    OPERATING_SYSTEM_CHOICES = [
        ('linux', 'Linux'),
        ('aix', 'AIX'),
        ('windows', 'Windows'),
        ('other', 'Diğer'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('maintenance', 'Bakımda'),
        ('inactive', 'Pasif'),
        ('error', 'Hata'),
    ]
    
    name = models.CharField(max_length=100)
    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    operating_system = models.CharField(max_length=20, choices=OPERATING_SYSTEM_CHOICES)
    server_type = models.ForeignKey(ServerType, on_delete=models.SET_NULL, null=True, related_name='servers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_servers')
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"

class ApplicationType(models.Model):
    """Uygulama tipi modeli"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Application(models.Model):
    """Uygulama modeli"""
    STATUS_CHOICES = [
        ('running', 'Çalışıyor'),
        ('stopped', 'Durduruldu'),
        ('error', 'Hata'),
        ('unknown', 'Bilinmiyor'),
    ]
    
    name = models.CharField(max_length=100)
    application_type = models.ForeignKey(ApplicationType, on_delete=models.SET_NULL, null=True, related_name='applications')
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='applications')
    port = models.IntegerField(blank=True, null=True)
    install_path = models.CharField(max_length=255, blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_applications')
    
    def __str__(self):
        return f"{self.name} ({self.application_type})"

class ApplicationLog(models.Model):
    """Uygulama log modeli"""
    LOG_TYPE_CHOICES = [
        ('info', 'Bilgi'),
        ('warning', 'Uyarı'),
        ('error', 'Hata'),
        ('critical', 'Kritik'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='application_logs')
    
    def __str__(self):
        return f"{self.application.name} - {self.log_type} - {self.timestamp}"

class MaintenanceRecord(models.Model):
    """Bakım kaydı modeli"""
    STATUS_CHOICES = [
        ('scheduled', 'Planlandı'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='maintenance_records')
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_maintenance_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.application.name} - {self.title}"

class ApplicationDocument(models.Model):
    """Uygulama dokümanı modeli"""
    DOCUMENT_TYPE_CHOICES = [
        ('installation', 'Kurulum Kılavuzu'),
        ('configuration', 'Yapılandırma Kılavuzu'),
        ('user_manual', 'Kullanım Kılavuzu'),
        ('troubleshooting', 'Sorun Giderme Kılavuzu'),
        ('other', 'Diğer'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='application_documents/')
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.application.name} - {self.title}"