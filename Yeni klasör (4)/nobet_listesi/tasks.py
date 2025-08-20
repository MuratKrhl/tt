import os
import pandas as pd
import numpy as np
import requests
import json
import logging
import datetime
import tabula
import re
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import urlparse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from .models import DataSource, ShiftList, Department, Doctor, Shift, FetchLog, AuditLog

# Logger yapılandırması
logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_data_from_source(self, source_id, user_id=None):
    """
    Veri kaynağından nöbet listesi verilerini çeker ve işler
    
    Args:
        source_id (int): Veri kaynağı ID'si
        user_id (int, optional): İşlemi başlatan kullanıcı ID'si
    """
    source = None
    fetch_log = None
    
    try:
        # Veri kaynağını al
        source = DataSource.objects.get(id=source_id)
        user = User.objects.get(id=user_id) if user_id else None
        
        # Fetch log oluştur
        fetch_log = FetchLog.objects.create(
            source=source,
            status='processing',
            started_at=timezone.now(),
            initiated_by=user
        )
        
        # URL'nin geçerli olup olmadığını kontrol et
        parsed_url = urlparse(source.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Geçersiz URL: {source.url}")
        
        # Veri kaynağı tipine göre işlem yap
        if source.source_type == 'csv':
            df = fetch_csv_data(source.url)
        elif source.source_type == 'excel':
            df = fetch_excel_data(source.url)
        elif source.source_type == 'html':
            df = fetch_html_table_data(source.url)
        elif source.source_type == 'pdf':
            df = fetch_pdf_table_data(source.url)
        else:
            raise ValueError(f"Desteklenmeyen kaynak tipi: {source.source_type}")
        
        # Kolon eşleştirmesi yap
        df = map_columns(df, source.column_mapping)
        
        # Verileri işle ve kaydet
        with transaction.atomic():
            process_shift_data(df, source, user)
        
        # Başarılı log kaydı
        fetch_log.status = 'success'
        fetch_log.completed_at = timezone.now()
        fetch_log.save()
        
        # Denetim logu
        if user:
            AuditLog.objects.create(
                user=user,
                action='fetch',
                model_name='DataSource',
                object_id=source.id,
                object_repr=str(source),
                details=f"Veri kaynağından başarıyla veri çekildi. Log ID: {fetch_log.id}"
            )
        
        return {
            'status': 'success',
            'message': f"Veri kaynağından başarıyla veri çekildi. Log ID: {fetch_log.id}"
        }
    
    except DataSource.DoesNotExist:
        error_msg = f"Veri kaynağı bulunamadı: {source_id}"
        logger.error(error_msg)
        if fetch_log:
            fetch_log.status = 'failed'
            fetch_log.error_message = error_msg
            fetch_log.completed_at = timezone.now()
            fetch_log.save()
        return {'status': 'error', 'message': error_msg}
    
    except User.DoesNotExist:
        error_msg = f"Kullanıcı bulunamadı: {user_id}"
        logger.error(error_msg)
        if fetch_log:
            fetch_log.status = 'failed'
            fetch_log.error_message = error_msg
            fetch_log.completed_at = timezone.now()
            fetch_log.save()
        return {'status': 'error', 'message': error_msg}
    
    except requests.exceptions.RequestException as e:
        error_msg = f"HTTP isteği başarısız: {str(e)}"
        logger.error(error_msg)
        if fetch_log:
            fetch_log.status = 'failed'
            fetch_log.error_message = error_msg
            fetch_log.completed_at = timezone.now()
            fetch_log.save()
        
        # Yeniden deneme
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {'status': 'error', 'message': f"Maksimum yeniden deneme sayısına ulaşıldı: {error_msg}"}
    
    except Exception as e:
        error_msg = f"Veri çekme işlemi başarısız: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if fetch_log:
            fetch_log.status = 'failed'
            fetch_log.error_message = error_msg
            fetch_log.completed_at = timezone.now()
            fetch_log.save()
        return {'status': 'error', 'message': error_msg}


@shared_task(bind=True, max_retries=2)
def process_uploaded_file(self, file_path, file_type, department_id, start_date, end_date, title, column_mapping, user_id=None):
    """
    Yüklenen dosyayı işler ve nöbet listesi oluşturur
    
    Args:
        file_path (str): Dosya yolu
        file_type (str): Dosya tipi (csv, excel, pdf, html)
        department_id (int): Bölüm ID'si
        start_date (str): Başlangıç tarihi (ISO format)
        end_date (str): Bitiş tarihi (ISO format)
        title (str): Nöbet listesi başlığı
        column_mapping (dict): Kolon eşleştirme bilgileri
        user_id (int, optional): İşlemi başlatan kullanıcı ID'si
    """
    try:
        # Kullanıcı ve bölüm bilgilerini al
        user = User.objects.get(id=user_id) if user_id else None
        department = Department.objects.get(id=department_id)
        
        # Tarihleri parse et
        start_date = datetime.date.fromisoformat(start_date)
        end_date = datetime.date.fromisoformat(end_date)
        
        # Dosya tipine göre veriyi oku
        if file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_type == 'excel':
            df = pd.read_excel(file_path)
        elif file_type == 'pdf':
            df = tabula.read_pdf(file_path, pages='all')
            if isinstance(df, list) and len(df) > 0:
                df = pd.concat(df, ignore_index=True)
            else:
                raise ValueError("PDF'den tablo okunamadı")
        elif file_type == 'html':
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            if not tables:
                raise ValueError("HTML dosyasında tablo bulunamadı")
            df = pd.read_html(str(tables[0]))[0]
        else:
            raise ValueError(f"Desteklenmeyen dosya tipi: {file_type}")
        
        # Kolon eşleştirmesi yap
        df = map_columns(df, column_mapping)
        
        # Nöbet listesi oluştur
        shift_list = ShiftList.objects.create(
            title=title,
            department=department,
            start_date=start_date,
            end_date=end_date,
            created_by=user,
            is_published=False,  # Taslak olarak oluştur
            source_type=file_type,
            source_file=os.path.basename(file_path)
        )
        
        # Verileri işle
        process_shift_data_from_df(df, shift_list, user)
        
        # Geçici dosyayı sil
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Denetim logu
        if user:
            AuditLog.objects.create(
                user=user,
                action='upload',
                model_name='ShiftList',
                object_id=shift_list.id,
                object_repr=str(shift_list),
                details=f"Dosyadan nöbet listesi oluşturuldu: {title}"
            )
        
        return {
            'status': 'success',
            'message': f"Dosya başarıyla işlendi ve nöbet listesi oluşturuldu: {title}",
            'shift_list_id': shift_list.id
        }
    
    except (Department.DoesNotExist, User.DoesNotExist) as e:
        error_msg = f"Veritabanı nesnesi bulunamadı: {str(e)}"
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}
    
    except Exception as e:
        error_msg = f"Dosya işleme hatası: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Geçici dosyayı silmeye çalış
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        
        # Yeniden deneme
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {'status': 'error', 'message': f"Maksimum yeniden deneme sayısına ulaşıldı: {error_msg}"}
        
        return {'status': 'error', 'message': error_msg}


# Yardımcı fonksiyonlar
def fetch_csv_data(url):
    """
    URL'den CSV verisi çeker
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_csv(BytesIO(response.content))


def fetch_excel_data(url):
    """
    URL'den Excel verisi çeker
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.read_excel(BytesIO(response.content))


def fetch_html_table_data(url):
    """
    URL'den HTML tablosu çeker
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        raise ValueError("HTML sayfasında tablo bulunamadı")
    return pd.read_html(str(tables[0]))[0]


def fetch_pdf_table_data(url):
    """
    URL'den PDF tablosu çeker
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    # Geçici dosya oluştur
    temp_file = f"/tmp/temp_pdf_{timezone.now().timestamp()}.pdf"
    with open(temp_file, 'wb') as f:
        f.write(response.content)
    
    # PDF'den tabloları oku
    try:
        df_list = tabula.read_pdf(temp_file, pages='all')
        if not df_list:
            raise ValueError("PDF'den tablo okunamadı")
        
        # Tüm tabloları birleştir
        df = pd.concat(df_list, ignore_index=True)
        
        # Geçici dosyayı sil
        os.remove(temp_file)
        
        return df
    except Exception as e:
        # Hata durumunda geçici dosyayı silmeye çalış
        try:
            os.remove(temp_file)
        except:
            pass
        raise e


def map_columns(df, column_mapping):
    """
    DataFrame kolonlarını eşleştirir
    
    Args:
        df (DataFrame): Orijinal veri çerçevesi
        column_mapping (dict): Kolon eşleştirme bilgileri
    
    Returns:
        DataFrame: Eşleştirilmiş kolonlarla veri çerçevesi
    """
    if not column_mapping:
        return df
    
    # JSON string ise parse et
    if isinstance(column_mapping, str):
        try:
            column_mapping = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise ValueError("Geçersiz kolon eşleştirme JSON formatı")
    
    # Kolon eşleştirmesi yap
    renamed_columns = {}
    for target_col, source_cols in column_mapping.items():
        # Birden fazla kaynak kolon olabilir, ilk bulunanı kullan
        if isinstance(source_cols, list):
            for source_col in source_cols:
                if source_col in df.columns:
                    renamed_columns[source_col] = target_col
                    break
        else:
            if source_cols in df.columns:
                renamed_columns[source_cols] = target_col
    
    # Kolonları yeniden adlandır
    if renamed_columns:
        df = df.rename(columns=renamed_columns)
    
    return df


def process_shift_data(df, source, user=None):
    """
    DataFrame'den nöbet verilerini işler ve kaydeder
    
    Args:
        df (DataFrame): İşlenecek veri çerçevesi
        source (DataSource): Veri kaynağı
        user (User, optional): İşlemi başlatan kullanıcı
    """
    # Nöbet listesi oluştur
    today = timezone.now().date()
    shift_list = ShiftList.objects.create(
        title=f"{source.name} - {today.strftime('%d.%m.%Y')}",
        department=source.department,
        start_date=today,
        end_date=today + datetime.timedelta(days=30),  # Varsayılan olarak 30 gün
        created_by=user,
        is_published=False,  # Taslak olarak oluştur
        source_type=source.source_type,
        source_url=source.url
    )
    
    # Verileri işle
    process_shift_data_from_df(df, shift_list, user)
    
    return shift_list


def process_shift_data_from_df(df, shift_list, user=None):
    """
    DataFrame'den nöbet verilerini işler ve kaydeder
    
    Args:
        df (DataFrame): İşlenecek veri çerçevesi
        shift_list (ShiftList): Nöbet listesi
        user (User, optional): İşlemi başlatan kullanıcı
    """
    required_columns = ['doctor_name', 'date']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Gerekli kolon bulunamadı: {col}")
    
    # Tarih kolonunu datetime formatına dönüştür
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # NaT değerleri filtrele
            df = df.dropna(subset=['date'])
        except Exception as e:
            raise ValueError(f"Tarih dönüşümü başarısız: {str(e)}")
    
    # Nöbet listesinin tarih aralığını güncelle
    if not df.empty:
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        shift_list.start_date = min_date
        shift_list.end_date = max_date
        shift_list.save()
    
    # Her satır için nöbet kaydı oluştur
    for _, row in df.iterrows():
        # Doktor adını parse et
        doctor_name = row['doctor_name']
        doctor_parts = parse_doctor_name(doctor_name)
        
        # Doktor kaydını bul veya oluştur
        doctor, _ = Doctor.objects.get_or_create(
            name=doctor_parts.get('name', ''),
            surname=doctor_parts.get('surname', ''),
            defaults={
                'title': doctor_parts.get('title', ''),
                'department': shift_list.department,
                'active': True
            }
        )
        
        # Telefon numarası varsa normalize et ve kaydet
        if 'phone' in row and pd.notna(row['phone']):
            phone = normalize_phone_number(str(row['phone']))
            if phone and doctor.phone != phone:
                doctor.phone = phone
                doctor.save()
        
        # E-posta varsa kaydet
        if 'email' in row and pd.notna(row['email']):
            email = str(row['email']).strip()
            if email and doctor.email != email:
                doctor.email = email
                doctor.save()
        
        # Nöbet tipi
        shift_type = 'normal'
        if 'shift_type' in row and pd.notna(row['shift_type']):
            shift_type_val = str(row['shift_type']).lower()
            if 'icap' in shift_type_val or 'on-call' in shift_type_val:
                shift_type = 'on_call'
            elif 'gece' in shift_type_val or 'night' in shift_type_val:
                shift_type = 'night'
        
        # Başlangıç ve bitiş saatleri
        start_time = None
        end_time = None
        
        if 'start_time' in row and pd.notna(row['start_time']):
            try:
                if isinstance(row['start_time'], str):
                    start_time = datetime.datetime.strptime(row['start_time'], '%H:%M').time()
                elif isinstance(row['start_time'], datetime.time):
                    start_time = row['start_time']
            except (ValueError, TypeError):
                pass
        
        if 'end_time' in row and pd.notna(row['end_time']):
            try:
                if isinstance(row['end_time'], str):
                    end_time = datetime.datetime.strptime(row['end_time'], '%H:%M').time()
                elif isinstance(row['end_time'], datetime.time):
                    end_time = row['end_time']
            except (ValueError, TypeError):
                pass
        
        # Notlar
        notes = None
        if 'notes' in row and pd.notna(row['notes']):
            notes = str(row['notes']).strip()
        
        # Nöbet kaydı oluştur
        Shift.objects.create(
            shift_list=shift_list,
            doctor=doctor,
            date=row['date'].date(),
            shift_type=shift_type,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )


def parse_doctor_name(full_name):
    """
    Doktor adını parçalara ayırır
    
    Args:
        full_name (str): Tam ad
    
    Returns:
        dict: Ad, soyad ve unvan bilgileri
    """
    if not full_name or not isinstance(full_name, str):
        return {'name': '', 'surname': '', 'title': ''}
    
    full_name = full_name.strip()
    
    # Unvan kontrolü
    title_patterns = [
        r'^(Prof\.|Prof\.Dr\.|Prof\. Dr\.|Doç\.|Doç\.Dr\.|Doç\. Dr\.|Dr\.|Uzm\.|Uzm\.Dr\.|Uzm\. Dr\.|Op\.|Op\.Dr\.|Op\. Dr\.)',
        r'^(Asst\.|Asst\.Prof\.|Assoc\.|Assoc\.Prof\.|MD|PhD)'
    ]
    
    title = ''
    name = ''
    surname = ''
    
    # Unvan varsa ayır
    for pattern in title_patterns:
        match = re.search(pattern, full_name, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            full_name = full_name[len(title):].strip()
            break
    
    # Ad ve soyadı ayır
    parts = full_name.split()
    if len(parts) >= 2:
        surname = parts[-1]
        name = ' '.join(parts[:-1])
    elif len(parts) == 1:
        surname = parts[0]
    
    return {
        'title': title,
        'name': name,
        'surname': surname
    }


def normalize_phone_number(phone):
    """
    Telefon numarasını normalize eder
    
    Args:
        phone (str): Telefon numarası
    
    Returns:
        str: Normalize edilmiş telefon numarası
    """
    if not phone:
        return None
    
    # Sadece rakamları al
    digits = re.sub(r'\D', '', phone)
    
    # Türkiye telefon numarası formatı
    if len(digits) == 10 and digits.startswith('5'):
        return f"+90{digits}"
    elif len(digits) == 11 and digits.startswith('05'):
        return f"+9{digits}"
    elif len(digits) == 11 and digits.startswith('90'):
        return f"+{digits}"
    elif len(digits) == 12 and digits.startswith('905'):
        return f"+{digits}"
    elif len(digits) == 13 and digits.startswith('+905'):
        return digits
    
    # Diğer durumlarda orijinal numarayı döndür
    return phone