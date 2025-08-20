from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ServerType(models.Model):
    """Sunucu türlerini tanımlar (Fiziksel, Sanal, Bulut, vb.)"""
    name = models.CharField(max_length=100, verbose_name="Sunucu Türü")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Sunucu Türü"
        verbose_name_plural = "Sunucu Türleri"

class Server(models.Model):
    """Sunucu bilgilerini tutar"""
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'İnaktif'),
        ('maintenance', 'Bakımda'),
        ('retired', 'Emekli'),
    ]
    
    OS_CHOICES = [
        ('windows', 'Windows'),
        ('linux', 'Linux'),
        ('unix', 'Unix'),
        ('macos', 'MacOS'),
        ('other', 'Diğer'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Sunucu Adı")
    hostname = models.CharField(max_length=255, verbose_name="Hostname")
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi")
    server_type = models.ForeignKey(ServerType, on_delete=models.CASCADE, related_name="servers", verbose_name="Sunucu Türü")
    operating_system = models.CharField(max_length=50, choices=OS_CHOICES, verbose_name="İşletim Sistemi")
    os_version = models.CharField(max_length=50, verbose_name="İşletim Sistemi Versiyonu")
    cpu = models.CharField(max_length=100, verbose_name="CPU")
    ram = models.CharField(max_length=50, verbose_name="RAM")
    storage = models.CharField(max_length=100, verbose_name="Depolama")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Konum")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Durum")
    purchase_date = models.DateField(blank=True, null=True, verbose_name="Satın Alma Tarihi")
    warranty_expiry = models.DateField(blank=True, null=True, verbose_name="Garanti Bitiş Tarihi")
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_servers", verbose_name="Oluşturan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    def days_until_warranty_expiry(self):
        """Garantinin dolmasına kaç gün kaldığını hesaplar"""
        if self.warranty_expiry:
            delta = self.warranty_expiry - timezone.now().date()
            return delta.days
        return None
    
    def is_warranty_expiring_soon(self, days=30):
        """Garantinin yakında süresi dolacak mı kontrol eder"""
        days_left = self.days_until_warranty_expiry()
        if days_left is not None:
            return 0 < days_left <= days
        return False
    
    class Meta:
        verbose_name = "Sunucu"
        verbose_name_plural = "Sunucular"
        ordering = ['name']

class ServerMaintenanceRecord(models.Model):
    """Sunucu bakım kayıtlarını tutar"""
    STATUS_CHOICES = [
        ('scheduled', 'Planlandı'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="maintenance_records", verbose_name="Sunucu")
    title = models.CharField(max_length=255, verbose_name="Başlık")
    description = models.TextField(verbose_name="Açıklama")
    maintenance_type = models.CharField(max_length=100, verbose_name="Bakım Türü")
    scheduled_date = models.DateTimeField(verbose_name="Planlanan Tarih")
    completed_date = models.DateTimeField(blank=True, null=True, verbose_name="Tamamlanma Tarihi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Durum")
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_server_maintenance", verbose_name="Gerçekleştiren")
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_server_maintenance", verbose_name="Oluşturan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        return f"{self.server.name} - {self.title} ({self.scheduled_date})"
    
    def save(self, *args, **kwargs):
        # Bakım tamamlandıysa, tamamlanma tarihini ayarla
        if self.status == 'completed' and not self.completed_date:
            self.completed_date = timezone.now()
        super().save(*args, **kwargs)
        
        # Sunucu durumunu güncelle
        server = self.server
        if self.status in ['scheduled', 'in_progress']:
            server.status = 'maintenance'
        elif self.status == 'completed':
            server.status = 'active'
        server.save()
    
    class Meta:
        verbose_name = "Sunucu Bakım Kaydı"
        verbose_name_plural = "Sunucu Bakım Kayıtları"
        ordering = ['-scheduled_date']

class ServerMonitoringLog(models.Model):
    """Sunucu izleme günlüklerini tutar"""
    LOG_LEVEL_CHOICES = [
        ('info', 'Bilgi'),
        ('warning', 'Uyarı'),
        ('error', 'Hata'),
        ('critical', 'Kritik'),
    ]
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="monitoring_logs", verbose_name="Sunucu")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zaman")
    log_level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, verbose_name="Log Seviyesi")
    metric_name = models.CharField(max_length=100, verbose_name="Metrik Adı")
    metric_value = models.FloatField(verbose_name="Metrik Değeri")
    threshold = models.FloatField(blank=True, null=True, verbose_name="Eşik Değeri")
    message = models.TextField(verbose_name="Mesaj")
    resolved = models.BooleanField(default=False, verbose_name="Çözüldü")
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_server_logs", verbose_name="Çözen")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="Çözülme Zamanı")
    
    def __str__(self):
        return f"{self.server.name} - {self.metric_name} - {self.timestamp}"
    
    def resolve(self, user):
        """Log kaydını çözüldü olarak işaretle"""
        self.resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Sunucu İzleme Logu"
        verbose_name_plural = "Sunucu İzleme Logları"
        ordering = ['-timestamp']

class ServerDocument(models.Model):
    """Sunucu ile ilgili belgeleri tutar"""
    DOCUMENT_TYPE_CHOICES = [
        ('manual', 'Kullanım Kılavuzu'),
        ('warranty', 'Garanti Belgesi'),
        ('invoice', 'Fatura'),
        ('license', 'Lisans'),
        ('config', 'Yapılandırma Dosyası'),
        ('other', 'Diğer'),
    ]
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="documents", verbose_name="Sunucu")
    title = models.CharField(max_length=255, verbose_name="Başlık")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, verbose_name="Belge Türü")
    file = models.FileField(upload_to='server_documents/', verbose_name="Dosya")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploaded_server_documents", verbose_name="Yükleyen")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Yüklenme Tarihi")
    
    def __str__(self):
        return f"{self.server.name} - {self.title}"
    
    class Meta:
        verbose_name = "Sunucu Belgesi"
        verbose_name_plural = "Sunucu Belgeleri"
        ordering = ['-uploaded_at']