from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DataSource, ShiftList, Department, Doctor, Shift
import datetime
import json


class ShiftListForm(forms.ModelForm):
    """Nöbet listesi oluşturma ve düzenleme formu"""
    class Meta:
        model = ShiftList
        fields = ['title', 'department', 'start_date', 'end_date', 'description', 'is_published']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'GG.AA.YYYY'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'GG.AA.YYYY'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['department'].widget.attrs.update({'class': 'form-control select2'})
        self.fields['is_published'].widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _('Bitiş tarihi başlangıç tarihinden önce olamaz.'))

        return cleaned_data


class DataSourceForm(forms.ModelForm):
    """Veri kaynağı ekleme/düzenleme formu"""
    class Meta:
        model = DataSource
        fields = ['name', 'department', 'source_type', 'url', 'column_mapping', 
                 'fetch_interval', 'last_fetch', 'active', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'column_mapping': forms.Textarea(attrs={'class': 'json-editor', 'rows': 10}),
            'last_fetch': forms.DateTimeInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['department'].widget.attrs.update({'class': 'form-control select2'})
        self.fields['source_type'].widget.attrs.update({'class': 'form-control select2'})
        self.fields['active'].widget.attrs.update({'class': 'form-check-input'})
        
        # Son çekme zamanı salt okunur
        self.fields['last_fetch'].widget.attrs['disabled'] = 'disabled'
        self.fields['last_fetch'].required = False
    
    def clean_column_mapping(self):
        """JSON formatındaki kolon eşleştirmelerini doğrular"""
        column_mapping = self.cleaned_data.get('column_mapping')
        
        # JSON formatı kontrolü
        try:
            if isinstance(column_mapping, str):
                mapping = json.loads(column_mapping)
            else:
                mapping = column_mapping
            
            # Gerekli alanların kontrolü
            required_fields = ['doctor', 'date']
            for field in required_fields:
                if field not in mapping:
                    raise forms.ValidationError(_('Kolon eşleştirmesinde "{}" alanı eksik.').format(field))
            
            # Tekrar JSON formatına dönüştür (düzgün formatlama için)
            if isinstance(column_mapping, str):
                return json.dumps(mapping, indent=2)
            return column_mapping
        except ValueError:
            raise forms.ValidationError(_('Geçerli bir JSON formatı değil.'))
        except Exception as e:
            raise forms.ValidationError(_('Kolon eşleştirmesi hatalı: {}').format(str(e)))


class FileUploadForm(forms.Form):
    """Manuel dosya yükleme formu"""
    title = forms.CharField(
        label=_('Başlık'),
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        label=_('Bölüm'),
        queryset=Department.objects.filter(active=True),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    file = forms.FileField(
        label=_('Dosya'),
        widget=forms.FileInput(attrs={'class': 'form-control-file', 'accept': '.csv,.xls,.xlsx,.pdf'})
    )
    start_date = forms.DateField(
        label=_('Başlangıç Tarihi'),
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'GG.AA.YYYY'})
    )
    end_date = forms.DateField(
        label=_('Bitiş Tarihi'),
        widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'GG.AA.YYYY'})
    )
    column_mapping = forms.CharField(
        label=_('Kolon Eşleştirmesi'),
        widget=forms.Textarea(attrs={'class': 'json-editor', 'rows': 10}),
        help_text=_('JSON formatında kolon eşleştirmesi. Örnek: {"doctor": "Doktor Adı", "date": "Tarih"}')
    )
    is_published = forms.BooleanField(
        label=_('Yayınla'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Dosya uzantısı kontrolü
            ext = file.name.split('.')[-1].lower()
            if ext not in ['csv', 'xls', 'xlsx', 'pdf']:
                raise forms.ValidationError(_('Desteklenmeyen dosya formatı. Lütfen CSV, Excel veya PDF dosyası yükleyin.'))
            
            # Dosya boyutu kontrolü (maksimum 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_('Dosya boyutu çok büyük. Maksimum 10MB dosya yükleyebilirsiniz.'))
        return file

    def clean_column_mapping(self):
        column_mapping = self.cleaned_data.get('column_mapping')
        
        # JSON formatı kontrolü
        try:
            mapping = json.loads(column_mapping)
            
            # Gerekli alanların kontrolü
            required_fields = ['doctor', 'date']
            for field in required_fields:
                if field not in mapping:
                    raise forms.ValidationError(_('Kolon eşleştirmesinde "{}" alanı eksik.').format(field))
            
            # Tekrar JSON formatına dönüştür (düzgün formatlama için)
            return json.dumps(mapping, indent=2)
        except ValueError:
            raise forms.ValidationError(_('Geçerli bir JSON formatı değil.'))
        except Exception as e:
            raise forms.ValidationError(_('Kolon eşleştirmesi hatalı: {}').format(str(e)))
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _('Bitiş tarihi başlangıç tarihinden önce olamaz.'))
        
        return cleaned_data


class FilterForm(forms.Form):
    """Nöbet listesi filtreleme formu"""
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(active=True),
        label=_('Bölüm'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    date_range = forms.CharField(
        label=_('Tarih Aralığı'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control daterangepicker-input'})
    )
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(active=True),
        label=_('Doktor'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    status = forms.ChoiceField(
        label=_('Durum'),
        choices=[
            ('', _('Tümü')),
            ('active', _('Aktif')),
            ('past', _('Geçmiş')),
            ('upcoming', _('Gelecek')),
            ('published', _('Yayında')),
            ('draft', _('Taslak'))
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_date_range(self):
        """Tarih aralığını başlangıç ve bitiş tarihi olarak ayırır"""
        date_range = self.cleaned_data.get('date_range')
        if not date_range:
            return None
        
        try:
            start_str, end_str = date_range.split(' - ')
            start_date = datetime.datetime.strptime(start_str, '%d.%m.%Y').date()
            end_date = datetime.datetime.strptime(end_str, '%d.%m.%Y').date()
            return (start_date, end_date)
        except (ValueError, IndexError):
            return None


class ShiftForm(forms.ModelForm):
    """Nöbet ekleme/düzenleme formu"""
    class Meta:
        model = Shift
        fields = ['doctor', 'date', 'start_time', 'end_time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control datepicker', 'placeholder': 'GG.AA.YYYY'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        shift_list = kwargs.pop('shift_list', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Eğer bir nöbet listesi belirtilmişse, doktor seçimini o bölüme göre filtrele
        if shift_list and shift_list.department:
            self.fields['doctor'].queryset = Doctor.objects.filter(
                department=shift_list.department, active=True
            ).order_by('surname', 'name')
        
        self.fields['doctor'].widget.attrs.update({'class': 'form-control select2'})

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')

        if start_time and end_time and start_time > end_time:
            self.add_error('end_time', _('Bitiş saati başlangıç saatinden önce olamaz.'))
        
        # Aynı doktor ve tarihte çakışan nöbet kontrolü
        if doctor and date:
            overlapping_shifts = Shift.objects.filter(
                doctor=doctor, 
                date=date
            )
            
            if self.instance and self.instance.pk:
                overlapping_shifts = overlapping_shifts.exclude(pk=self.instance.pk)
            
            for shift in overlapping_shifts:
                # Zaman aralıkları çakışıyor mu kontrolü
                if (start_time <= shift.end_time and end_time >= shift.start_time):
                    self.add_error('date', _('Bu doktor için aynı tarih ve saatte başka bir nöbet kaydı mevcut.'))
                    break

        return cleaned_data


class BulkShiftForm(forms.Form):
    """Toplu nöbet kaydı oluşturma formu"""
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(active=True),
        label=_('Doktor'),
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    date_range = forms.CharField(
        label=_('Tarih Aralığı'),
        widget=forms.TextInput(attrs={'class': 'form-control daterangepicker-input'})
    )
    days_of_week = forms.MultipleChoiceField(
        choices=[
            (0, _('Pazartesi')),
            (1, _('Salı')),
            (2, _('Çarşamba')),
            (3, _('Perşembe')),
            (4, _('Cuma')),
            (5, _('Cumartesi')),
            (6, _('Pazar')),
        ],
        label=_('Haftanın Günleri'),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    start_time = forms.TimeField(
        label=_('Başlangıç Saati'),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    end_time = forms.TimeField(
        label=_('Bitiş Saati'),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    notes = forms.CharField(
        label=_('Notlar'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        shift_list = kwargs.pop('shift_list', None)
        super().__init__(*args, **kwargs)
        
        # Eğer bir nöbet listesi belirtilmişse, doktor seçimini o bölüme göre filtrele
        if shift_list and shift_list.department:
            self.fields['doctor'].queryset = Doctor.objects.filter(
                department=shift_list.department, active=True
            ).order_by('surname', 'name')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time > end_time:
            self.add_error('end_time', _('Bitiş saati başlangıç saatinden önce olamaz.'))

        return cleaned_data


class DoctorForm(forms.ModelForm):
    """Doktor ekleme/düzenleme formu"""
    class Meta:
        model = Doctor
        fields = ['name', 'surname', 'title', 'department', 'phone', 'email', 'notes', 'active', 'external_id']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['department'].widget.attrs.update({'class': 'form-control select2'})
        self.fields['active'].widget.attrs.update({'class': 'form-check-input'})
        
        # Telefon numarası için placeholder
        self.fields['phone'].widget.attrs.update({
            'placeholder': '5XX XXX XX XX',
            'class': 'form-control phone-input'
        })

    def clean_phone(self):
        """Telefon numarasını normalize eder"""
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        
        # Sadece rakamları al
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # Türkiye formatı için düzenleme
        if len(digits_only) == 10 and digits_only.startswith('5'):
            # 5XX XXX XX XX formatı
            return f'+90{digits_only}'
        elif len(digits_only) == 11 and digits_only.startswith('05'):
            # 05XX XXX XX XX formatı
            return f'+9{digits_only}'
        elif len(digits_only) == 12 and digits_only.startswith('905'):
            # 905XX XXX XX XX formatı
            return f'+{digits_only}'
        elif len(digits_only) == 13 and digits_only.startswith('+905'):
            # +905XX XXX XX XX formatı
            return digits_only
        else:
            raise forms.ValidationError(_('Geçerli bir Türkiye telefon numarası giriniz (5XX XXX XX XX).'))
        
        return phone


class DepartmentForm(forms.ModelForm):
    """Bölüm ekleme/düzenleme formu"""
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['active'].widget.attrs.update({'class': 'form-check-input'})
        
        # Kod alanı için placeholder
        self.fields['code'].widget.attrs.update({
            'placeholder': _('Otomatik oluşturulacak (opsiyonel)')
        })

    def clean_code(self):
        code = self.cleaned_data.get('code')
        name = self.cleaned_data.get('name')
        
        # Eğer kod belirtilmemişse, isimden otomatik oluştur
        if not code and name:
            # Türkçe karakterleri değiştir
            turkish_chars = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 
                           'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'}
            
            code = name.lower()
            for char, replacement in turkish_chars.items():
                code = code.replace(char, replacement)
            
            # Alfanumerik olmayan karakterleri kaldır ve boşlukları alt çizgi ile değiştir
            code = ''.join(c if c.isalnum() or c.isspace() else '' for c in code)
            code = code.replace(' ', '_')
            
            # Maksimum 10 karakter
            code = code[:10].upper()
        
        # Eğer bu kod zaten varsa ve bu kayıt değilse (güncelleme durumu)
        if code:
            existing = Department.objects.filter(code=code)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(_('Bu kod zaten kullanılıyor. Lütfen başka bir kod seçin.'))
        
        return code


class ExportForm(forms.Form):
    """Dışa aktarma formu"""
    format = forms.ChoiceField(
        label=_('Format'),
        choices=[
            ('excel', _('Excel (.xlsx)')),
            ('csv', _('CSV (.csv)')),
            ('pdf', _('PDF (.pdf)')),
        ],
        initial='excel',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shift_list = forms.ModelChoiceField(
        queryset=ShiftList.objects.filter(is_published=True),
        label=_('Nöbet Listesi'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(active=True),
        label=_('Bölüm'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    date_range = forms.CharField(
        label=_('Tarih Aralığı'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control daterangepicker-input'})
    )
    doctors = forms.ModelMultipleChoiceField(
        queryset=Doctor.objects.filter(active=True),
        label=_('Doktorlar'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2', 'multiple': 'multiple'})
    )
    include_contact_info = forms.BooleanField(
        label=_('İletişim Bilgilerini Dahil Et'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    mask_contact_info = forms.BooleanField(
        label=_('İletişim Bilgilerini Maskele'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_header = forms.BooleanField(
        label=_('Başlık Ekle'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_footer = forms.BooleanField(
        label=_('Altbilgi Ekle'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    # PDF için ek seçenekler
    page_size = forms.ChoiceField(
        label=_('Sayfa Boyutu'),
        choices=[
            ('a4', 'A4'),
            ('a3', 'A3'),
            ('letter', 'Letter'),
            ('legal', 'Legal'),
        ],
        initial='a4',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    orientation = forms.ChoiceField(
        label=_('Sayfa Yönü'),
        choices=[
            ('portrait', _('Dikey')),
            ('landscape', _('Yatay')),
        ],
        initial='portrait',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Bölüm seçildiğinde doktor listesini filtrelemek için
        department_id = kwargs.get('data', {}).get('department')
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
                self.fields['doctors'].queryset = Doctor.objects.filter(
                    department=department, active=True
                ).order_by('surname', 'name')
            except (Department.DoesNotExist, ValueError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        shift_list = cleaned_data.get('shift_list')
        department = cleaned_data.get('department')
        date_range = cleaned_data.get('date_range')
        
        # En az bir filtreleme kriteri gerekli
        if not shift_list and not department and not date_range:
            raise forms.ValidationError(_('Lütfen en az bir filtreleme kriteri seçin: Nöbet Listesi, Bölüm veya Tarih Aralığı.'))
        
        # İletişim bilgileri çelişkisi kontrolü
        include_contact = cleaned_data.get('include_contact_info')
        mask_contact = cleaned_data.get('mask_contact_info')
        
        if include_contact and mask_contact:
            self.add_error('mask_contact_info', _('Hem iletişim bilgilerini dahil etme hem de maskeleme seçeneği aynı anda seçilemez.'))
        
        return cleaned_data