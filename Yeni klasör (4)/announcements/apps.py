from django.apps import AppConfig


class AnnouncementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'announcements'
    verbose_name = 'Duyurular ve Planlı Çalışmalar'

    def ready(self):
        # Sinyalleri yükle
        import announcements.signals