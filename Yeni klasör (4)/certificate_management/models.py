from django.db import models
from django.utils import timezone
from django.conf import settings

class CertificateType(models.Model):
    """Sertifika türlerini tanımlar (SSL, TLS, vb.)"""
    name = models.CharField(max_length=100, verbose_name="Sertifika Türü")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Sertifika Türü"
        verbose_name_plural = "Sertifika Türleri"

class Certificate(models.Model):
    """Sertifika bilgilerini tutar"""
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('expired', 'Süresi Dolmuş'),
        ('revoked', 'İptal Edilmiş'),
        ('pending', 'Beklemede'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Sertifika Adı")
    certificate_type = models.ForeignKey(CertificateType, on_delete=models.CASCADE, related_name="certificates", verbose_name="Sertifika Türü")
    domain_name = models.CharField(max_length=255, verbose_name="Alan Adı")
    issuer = models.CharField(max_length=255, verbose_name="Sertifika Sağlayıcı")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Seri Numarası")
    issue_date = models.DateField(verbose_name="Verilme Tarihi")
    expiry_date = models.DateField(verbose_name="Geçerlilik Sonu")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Durum")
    key_algorithm = models.CharField(max_length=50, blank=True, null=True, verbose_name="Anahtar Algoritması")
    key_size = models.IntegerField(blank=True, null=True, verbose_name="Anahtar Boyutu")
    signature_algorithm = models.CharField(max_length=100, blank=True, null=True, verbose_name="İmza Algoritması")
    subject_alternative_names = models.TextField(blank=True, null=True, verbose_name="Alternatif Alan Adları")
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True, verbose_name="Sertifika Dosyası")
    private_key_file = models.FileField(upload_to='certificates/private_keys/', blank=True, null=True, verbose_name="Özel Anahtar Dosyası")
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_certificates", verbose_name="Oluşturan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        return f"{self.name} ({self.domain_name})"
    
    def days_until_expiry(self):
        """Sertifikanın süresinin dolmasına kaç gün kaldığını hesaplar"""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None
    
    def is_expiring_soon(self, days=30):
        """Sertifikanın yakında süresi dolacak mı kontrol eder"""
        days_left = self.days_until_expiry()
        if days_left is not None:
            return 0 < days_left <= days
        return False
    
    def update_status(self):
        """Sertifika durumunu geçerlilik tarihine göre günceller"""
        today = timezone.now().date()
        if self.status != 'revoked':  # İptal edilmiş sertifikaların durumu değişmez
            if self.expiry_date < today:
                self.status = 'expired'
            else:
                self.status = 'active'
            self.save(update_fields=['status'])
    
    class Meta:
        verbose_name = "Sertifika"
        verbose_name_plural = "Sertifikalar"
        ordering = ['-expiry_date']

class CertificateRenewal(models.Model):
    """Sertifika yenileme işlemlerini takip eder"""
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('in_progress', 'İşlemde'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name="renewals", verbose_name="Sertifika")
    old_expiry_date = models.DateField(verbose_name="Eski Geçerlilik Sonu")
    new_expiry_date = models.DateField(blank=True, null=True, verbose_name="Yeni Geçerlilik Sonu")
    renewal_date = models.DateField(default=timezone.now, verbose_name="Yenileme Tarihi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    notes = models.TextField(blank=True, null=True, verbose_name="Notlar")
    renewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="certificate_renewals", verbose_name="Yenileyen")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    def __str__(self):
        return f"{self.certificate.name} - {self.renewal_date}"
    
    class Meta:
        verbose_name = "Sertifika Yenileme"
        verbose_name_plural = "Sertifika Yenilemeleri"
        ordering = ['-renewal_date']

class CertificateNotification(models.Model):
    """Sertifika sona erme bildirimleri"""
    NOTIFICATION_TYPE_CHOICES = [
        ('expiry_warning', 'Sona Erme Uyarısı'),
        ('expired', 'Süresi Doldu'),
        ('renewal_reminder', 'Yenileme Hatırlatıcısı'),
    ]
    
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name="notifications", verbose_name="Sertifika")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, verbose_name="Bildirim Türü")
    sent_date = models.DateTimeField(default=timezone.now, verbose_name="Gönderilme Tarihi")
    sent_to = models.ManyToManyField(User, related_name="certificate_notifications", verbose_name="Alıcılar")
    message = models.TextField(verbose_name="Mesaj")
    acknowledged = models.BooleanField(default=False, verbose_name="Onaylandı")
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_notifications", verbose_name="Onaylayan")
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name="Onaylanma Tarihi")
    
    def __str__(self):
        return f"{self.certificate.name} - {self.get_notification_type_display()} - {self.sent_date}"
    
    def acknowledge(self, user):
        """Bildirimi onaylar"""
        self.acknowledged = True
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Sertifika Bildirimi"
        verbose_name_plural = "Sertifika Bildirimleri"
        ordering = ['-sent_date']
