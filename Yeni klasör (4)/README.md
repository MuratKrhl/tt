# IT Varlık Yönetim Sistemi

Bu proje, bir şirketin IT varlıklarını (envanter, sertifikalar, sunucular) yönetmek için geliştirilmiş bir Django web uygulamasıdır.

## Özellikler

- **Envanter Yönetimi**: Donanım ve yazılım envanterinin takibi, kategorilendirme, tedarikçi bilgileri, bakım kayıtları
- **Sertifika Yönetimi**: SSL, lisans ve diğer sertifikaların takibi, yenileme bildirimleri
- **Sunucu Yönetimi**: Fiziksel ve sanal sunucuların takibi, bakım kayıtları, izleme günlükleri
- **Kullanıcı Yönetimi**: Rol tabanlı erişim kontrolü, departman yönetimi, kullanıcı aktivite takibi

## Kurulum

1. Projeyi klonlayın:
   ```
   git clone <repo-url>
   cd it-asset-management
   ```

2. Sanal ortam oluşturun ve etkinleştirin:
   ```
   python -m venv venv
   # Windows için
   venv\Scripts\activate
   # Linux/Mac için
   source venv/bin/activate
   ```

3. Bağımlılıkları yükleyin:
   ```
   pip install -r requirements.txt
   ```

4. Veritabanı migrasyonlarını uygulayın:
   ```
   python manage.py migrate
   ```

5. Bir süper kullanıcı oluşturun:
   ```
   python manage.py createsuperuser
   ```

6. Sunucuyu başlatın:
   ```
   python manage.py runserver
   ```

## Modüller

### Envanter Yönetimi
- Kategoriler, tedarikçiler ve envanter öğelerinin yönetimi
- Envanter hareketleri ve bakım kayıtları
- Filtreleme ve arama özellikleri

### Sertifika Yönetimi
- Sertifika türleri ve sertifikaların yönetimi
- Yenileme kayıtları ve bildirimleri
- Sona erme tarihi takibi ve uyarılar

### Sunucu Yönetimi
- Sunucu türleri ve sunucuların yönetimi
- Bakım kayıtları ve izleme günlükleri
- Sunucu belgeleri ve garanti takibi

### Kullanıcı Yönetimi
- Özel kullanıcı modeli ve departman yönetimi
- Kullanıcı aktivite takibi ve bildirimler
- İzin istekleri ve yönetimi

## Teknolojiler

- Django 4.2
- Bootstrap 5
- SQLite (geliştirme) / PostgreSQL (üretim)
- Crispy Forms
- ReportLab / xhtml2pdf (raporlama için)