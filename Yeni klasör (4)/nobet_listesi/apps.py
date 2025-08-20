from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NobetListesiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nobet_listesi'
    verbose_name = _('Nöbet Listesi Çözümü')
    
    def ready(self):
        # Sinyalleri yükle
        import nobet_listesi.signals