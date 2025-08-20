from celery import shared_task
from django.utils import timezone
from .models import Announcement
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def archive_expired_announcements():
    """Süresi dolmuş duyuruları arşivler"""
    now = timezone.now()
    expired_announcements = Announcement.objects.filter(
        status='published',
        end_date__lt=now
    )
    
    count = 0
    for announcement in expired_announcements:
        try:
            announcement.archive()
            count += 1
        except Exception as e:
            logger.error(f"Duyuru arşivlenirken hata oluştu (ID: {announcement.id}): {str(e)}")
    
    logger.info(f"{count} adet duyuru otomatik olarak arşivlendi.")
    return count

@shared_task
def send_teams_notification(announcement_id):
    """Yeni duyuru için Teams webhook bildirimi gönderir"""
    try:
        # Duyuru bilgilerini al
        announcement = Announcement.objects.get(id=announcement_id)
        
        # Teams webhook URL'si ayarlardan alınır
        webhook_url = getattr(settings, 'TEAMS_WEBHOOK_URL', None)
        
        if not webhook_url:
            logger.warning("Teams webhook URL'si tanımlanmamış. Bildirim gönderilemiyor.")
            return False
        
        # Duyuru türüne göre renk belirleme
        color_map = {
            'low': '808080',  # Gri
            'medium': '0078D7',  # Mavi
            'high': 'FFA500',  # Turuncu
            'critical': 'FF0000'  # Kırmızı
        }
        
        # Duyuru türüne göre başlık belirleme
        type_titles = {
            'announcement': 'Duyuru',
            'planned_work': 'Planlı Çalışma',
            'information': 'Bilgilendirme'
        }
        
        # Teams kart mesajı oluştur
        card_data = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color_map.get(announcement.priority, '0078D7'),
            "summary": f"Yeni {type_titles.get(announcement.announcement_type, 'Duyuru')}: {announcement.title}",
            "sections": [
                {
                    "activityTitle": f"Yeni {type_titles.get(announcement.announcement_type, 'Duyuru')}",
                    "activitySubtitle": announcement.title,
                    "activityImage": "https://adaptivecards.io/content/adaptive-card-50.png",
                    "facts": [
                        {
                            "name": "Öncelik:",
                            "value": announcement.get_priority_display()
                        },
                        {
                            "name": "Ürün:",
                            "value": announcement.product
                        },
                        {
                            "name": "Yayın Tarihi:",
                            "value": announcement.start_date.strftime('%d.%m.%Y %H:%M')
                        },
                        {
                            "name": "Yazar:",
                            "value": announcement.author.get_full_name() or announcement.author.username
                        }
                    ],
                    "text": announcement.content[:500] + ("..." if len(announcement.content) > 500 else "")
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Detayları Görüntüle",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"{settings.SITE_URL}{announcement.get_absolute_url()}"
                        }
                    ]
                }
            ]
        }
        
        # Webhook'a POST isteği gönder
        response = requests.post(
            webhook_url,
            json=card_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code >= 400:
            logger.error(f"Teams bildirimi gönderilirken hata oluştu: {response.status_code} - {response.text}")
            return False
        
        logger.info(f"Teams bildirimi başarıyla gönderildi: {announcement.title}")
        return True
        
    except Announcement.DoesNotExist:
        logger.error(f"Bildirim gönderilecek duyuru bulunamadı (ID: {announcement_id})")
        return False
    except Exception as e:
        logger.error(f"Teams bildirimi gönderilirken beklenmeyen hata: {str(e)}")
        return False