from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import ShiftList, Shift, Doctor, Department, FetchLog, AuditLog


@receiver(post_save, sender=ShiftList)
def update_shift_list_dates(sender, instance, created, **kwargs):
    """
    Nöbet listesi kaydedildiğinde, içindeki nöbetlerin tarih aralığına göre
    başlangıç ve bitiş tarihlerini günceller.
    """
    if not created:  # Sadece güncelleme durumunda çalış
        shifts = instance.shifts.all()
        if shifts.exists():
            min_date = shifts.order_by('date').first().date
            max_date = shifts.order_by('-date').first().date
            
            # Tarih aralığı değiştiyse güncelle
            if instance.start_date != min_date or instance.end_date != max_date:
                instance.start_date = min_date
                instance.end_date = max_date
                # Sonsuz döngüyü önlemek için signal'ı geçici olarak devre dışı bırak
                post_save.disconnect(update_shift_list_dates, sender=ShiftList)
                instance.save()
                post_save.connect(update_shift_list_dates, sender=ShiftList)


@receiver(post_save, sender=Shift)
def update_shift_list_on_shift_change(sender, instance, created, **kwargs):
    """
    Nöbet eklendiğinde veya güncellendiğinde, bağlı olduğu nöbet listesinin
    tarih aralığını günceller.
    """
    shift_list = instance.shift_list
    shifts = shift_list.shifts.all()
    
    if shifts.exists():
        min_date = shifts.order_by('date').first().date
        max_date = shifts.order_by('-date').first().date
        
        # Tarih aralığı değiştiyse güncelle
        if shift_list.start_date != min_date or shift_list.end_date != max_date:
            shift_list.start_date = min_date
            shift_list.end_date = max_date
            # Sonsuz döngüyü önlemek için signal'ı geçici olarak devre dışı bırak
            post_save.disconnect(update_shift_list_dates, sender=ShiftList)
            shift_list.save()
            post_save.connect(update_shift_list_dates, sender=ShiftList)


@receiver(post_delete, sender=Shift)
def update_shift_list_on_shift_delete(sender, instance, **kwargs):
    """
    Nöbet silindiğinde, bağlı olduğu nöbet listesinin tarih aralığını günceller.
    """
    try:
        shift_list = instance.shift_list
        shifts = shift_list.shifts.all()
        
        if shifts.exists():
            min_date = shifts.order_by('date').first().date
            max_date = shifts.order_by('-date').first().date
            
            # Tarih aralığı değiştiyse güncelle
            if shift_list.start_date != min_date or shift_list.end_date != max_date:
                shift_list.start_date = min_date
                shift_list.end_date = max_date
                # Sonsuz döngüyü önlemek için signal'ı geçici olarak devre dışı bırak
                post_save.disconnect(update_shift_list_dates, sender=ShiftList)
                shift_list.save()
                post_save.connect(update_shift_list_dates, sender=ShiftList)
    except ShiftList.DoesNotExist:
        # Nöbet listesi silinmiş olabilir
        pass


@receiver(post_save, sender=FetchLog)
def notify_on_fetch_completion(sender, instance, created, **kwargs):
    """
    Veri çekme işlemi tamamlandığında bildirim gönderir.
    """
    # Sadece durum değişikliklerinde çalış
    if not created and instance.status in ['success', 'failed'] and instance.completed_at:
        # Burada bildirim gönderme işlemleri yapılabilir
        # Örneğin: Email, Slack, Teams vb.
        pass


@receiver(post_save, sender=Doctor)
def normalize_doctor_phone(sender, instance, created, **kwargs):
    """
    Doktor kaydedildiğinde telefon numarasını normalize eder.
    """
    from .tasks import normalize_phone_number
    
    if instance.phone and not instance.phone.startswith('+'):
        normalized_phone = normalize_phone_number(instance.phone)
        if normalized_phone != instance.phone:
            # Sonsuz döngüyü önlemek için signal'ı geçici olarak devre dışı bırak
            post_save.disconnect(normalize_doctor_phone, sender=Doctor)
            instance.phone = normalized_phone
            instance.save()
            post_save.connect(normalize_doctor_phone, sender=Doctor)