from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Announcement
from .tasks import send_teams_notification

@receiver(post_save, sender=Announcement)
def announcement_post_save(sender, instance, created, **kwargs):
    """Duyuru kaydedildiğinde çalışacak sinyal işleyicisi"""
    # Yeni bir duyuru oluşturulduğunda ve yayında ise Teams bildirimi gönder
    if created and instance.status == 'published':
        send_teams_notification.delay(instance.id)
    
    # Var olan bir duyuru güncellendiğinde ve yayında ise Teams bildirimi gönder
    elif not created and instance.status == 'published' and instance.tracker.has_changed('status'):
        # Eğer durum taslaktan yayına değiştiyse bildirim gönder
        if instance.tracker.previous('status') == 'draft':
            send_teams_notification.delay(instance.id)