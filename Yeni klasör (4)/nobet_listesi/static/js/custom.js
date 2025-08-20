/* Nöbet Listesi Çözümü - Özel JavaScript Fonksiyonları */

// Sayfa yüklendiğinde çalışacak fonksiyonlar
$(document).ready(function() {
    // Tooltip'leri etkinleştir
    $('[data-toggle="tooltip"]').tooltip();
    
    // Popover'ları etkinleştir
    $('[data-toggle="popover"]').popover();
    
    // Select2 için varsayılan ayarlar
    initializeSelect2();
    
    // Telefon numarası formatlaması
    initializePhoneInputs();
    
    // Tarih seçicileri için varsayılan ayarlar
    initializeDatepickers();
    
    // Dosya yükleme alanı için sürükle-bırak desteği
    initializeDropzone();
    
    // Bildirim kapatma düğmesi
    $('.alert').alert();
    
    // Otomatik kaybolan bildirimler
    setTimeout(function() {
        $('.alert-auto-dismiss').alert('close');
    }, 5000);
});

// Select2 başlatma fonksiyonu
function initializeSelect2() {
    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap4',
            width: '100%',
            placeholder: function() {
                return $(this).data('placeholder') || 'Seçiniz';
            },
            allowClear: true,
            language: {
                inputTooShort: function() {
                    return "Lütfen en az 2 karakter girin...";
                },
                noResults: function() {
                    return "Sonuç bulunamadı";
                },
                searching: function() {
                    return "Aranıyor...";
                }
            }
        });
    }
}

// Telefon numarası formatlaması
function initializePhoneInputs() {
    $('.phone-input').on('input', function() {
        let value = $(this).val().replace(/\D/g, '');
        
        // Türkiye telefon numarası formatı: +90 (5XX) XXX XX XX
        if (value.length > 0) {
            if (value.length <= 3) {
                value = value;
            } else if (value.length <= 6) {
                value = value.substring(0, 3) + ' ' + value.substring(3);
            } else if (value.length <= 8) {
                value = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6);
            } else if (value.length <= 10) {
                value = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6, 8) + ' ' + value.substring(8);
            } else {
                value = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6, 8) + ' ' + value.substring(8, 10) + ' ' + value.substring(10, Math.min(value.length, 12));
            }
        }
        
        $(this).val(value);
    });
}

// Tarih seçicileri için varsayılan ayarlar
function initializeDatepickers() {
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'dd.mm.yyyy',
            autoclose: true,
            todayHighlight: true,
            language: 'tr',
            weekStart: 1
        });
    }
    
    if ($.fn.daterangepicker) {
        $('.daterangepicker-input').daterangepicker({
            locale: {
                format: 'DD.MM.YYYY',
                applyLabel: 'Uygula',
                cancelLabel: 'İptal',
                fromLabel: 'Başlangıç',
                toLabel: 'Bitiş',
                customRangeLabel: 'Özel Aralık',
                daysOfWeek: ['Pz', 'Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct'],
                monthNames: ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'],
                firstDay: 1
            },
            opens: 'right'
        });
    }
}

// Dosya yükleme alanı için sürükle-bırak desteği
function initializeDropzone() {
    const dropzoneArea = document.querySelector('.dropzone');
    
    if (dropzoneArea) {
        const fileInput = dropzoneArea.querySelector('input[type="file"]');
        const previewArea = dropzoneArea.querySelector('.file-preview') || document.createElement('div');
        
        if (!dropzoneArea.querySelector('.file-preview')) {
            previewArea.classList.add('file-preview', 'mt-3');
            dropzoneArea.appendChild(previewArea);
        }
        
        // Dosya seçildiğinde önizleme göster
        fileInput.addEventListener('change', function(e) {
            showFilePreview(this.files);
        });
        
        // Sürükle-bırak olayları
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzoneArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzoneArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropzoneArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropzoneArea.classList.add('dragover');
        }
        
        function unhighlight() {
            dropzoneArea.classList.remove('dragover');
        }
        
        // Dosya bırakıldığında
        dropzoneArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            fileInput.files = files;
            showFilePreview(files);
            
            // Change olayını tetikle
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
        
        // Dosya önizleme fonksiyonu
        function showFilePreview(files) {
            previewArea.innerHTML = '';
            
            if (files.length > 0) {
                const file = files[0];
                const fileSize = formatFileSize(file.size);
                const fileType = getFileTypeIcon(file.type);
                
                const fileInfo = document.createElement('div');
                fileInfo.className = 'alert alert-info d-flex align-items-center';
                fileInfo.innerHTML = `
                    <i class="fas ${fileType} fa-2x mr-3"></i>
                    <div>
                        <strong>${file.name}</strong><br>
                        <small>${fileSize} - ${file.type || 'Bilinmeyen tür'}</small>
                    </div>
                    <button type="button" class="close ml-auto" aria-label="Kapat">
                        <span aria-hidden="true">&times;</span>
                    </button>
                `;
                
                previewArea.appendChild(fileInfo);
                
                // Dosyayı kaldırma düğmesi
                const closeButton = fileInfo.querySelector('.close');
                closeButton.addEventListener('click', function() {
                    fileInput.value = '';
                    previewArea.innerHTML = '';
                    
                    // Change olayını tetikle
                    const event = new Event('change');
                    fileInput.dispatchEvent(event);
                });
            }
        }
        
        // Dosya boyutu formatla
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // Dosya türüne göre ikon belirle
        function getFileTypeIcon(mimeType) {
            if (mimeType.includes('excel') || mimeType.includes('spreadsheet') || mimeType.includes('csv')) {
                return 'fa-file-excel';
            } else if (mimeType.includes('pdf')) {
                return 'fa-file-pdf';
            } else if (mimeType.includes('word') || mimeType.includes('document')) {
                return 'fa-file-word';
            } else if (mimeType.includes('image')) {
                return 'fa-file-image';
            } else if (mimeType.includes('text')) {
                return 'fa-file-alt';
            } else if (mimeType.includes('zip') || mimeType.includes('compressed')) {
                return 'fa-file-archive';
            } else {
                return 'fa-file';
            }
        }
    }
}

// Yükleniyor göstergesi
function showLoading() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="spinner-border text-primary loading-spinner" role="status">
            <span class="sr-only">Yükleniyor...</span>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// Form doğrulama
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            
            // Hata mesajı ekle
            let errorDiv = field.nextElementSibling;
            if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            }
            errorDiv.textContent = 'Bu alan zorunludur.';
        } else {
            field.classList.remove('is-invalid');
            
            // Hata mesajını kaldır
            const errorDiv = field.nextElementSibling;
            if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                errorDiv.textContent = '';
            }
        }
    });
    
    return isValid;
}

// AJAX form gönderimi
function submitFormAjax(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    if (!validateForm(formId)) return;
    
    const formData = new FormData(form);
    const url = form.getAttribute('action') || window.location.href;
    const method = form.getAttribute('method') || 'POST';
    
    showLoading();
    
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            if (successCallback && typeof successCallback === 'function') {
                successCallback(data);
            } else {
                // Varsayılan başarı işlemi
                Swal.fire({
                    title: 'Başarılı!',
                    text: data.message || 'İşlem başarıyla tamamlandı.',
                    icon: 'success',
                    confirmButtonText: 'Tamam'
                }).then(() => {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                });
            }
        } else {
            if (errorCallback && typeof errorCallback === 'function') {
                errorCallback(data);
            } else {
                // Varsayılan hata işlemi
                Swal.fire({
                    title: 'Hata!',
                    text: data.error || 'İşlem sırasında bir hata oluştu.',
                    icon: 'error',
                    confirmButtonText: 'Tamam'
                });
            }
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        
        if (errorCallback && typeof errorCallback === 'function') {
            errorCallback({ error: 'Bir ağ hatası oluştu.' });
        } else {
            // Varsayılan hata işlemi
            Swal.fire({
                title: 'Hata!',
                text: 'Bir ağ hatası oluştu. Lütfen daha sonra tekrar deneyin.',
                icon: 'error',
                confirmButtonText: 'Tamam'
            });
        }
    });
}

// Silme onayı
function confirmDelete(url, itemName, successCallback) {
    Swal.fire({
        title: 'Emin misiniz?',
        text: `"${itemName}" öğesini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74a3b',
        cancelButtonColor: '#858796',
        confirmButtonText: 'Evet, sil!',
        cancelButtonText: 'İptal'
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading();
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    Swal.fire(
                        'Silindi!',
                        data.message || 'Öğe başarıyla silindi.',
                        'success'
                    ).then(() => {
                        if (successCallback && typeof successCallback === 'function') {
                            successCallback(data);
                        } else if (data.redirect) {
                            window.location.href = data.redirect;
                        } else {
                            window.location.reload();
                        }
                    });
                } else {
                    Swal.fire(
                        'Hata!',
                        data.error || 'Silme işlemi sırasında bir hata oluştu.',
                        'error'
                    );
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Error:', error);
                Swal.fire(
                    'Hata!',
                    'Bir ağ hatası oluştu. Lütfen daha sonra tekrar deneyin.',
                    'error'
                );
            });
        }
    });
}

// Kod üretme fonksiyonu
function generateCode(text, prefix = '') {
    if (!text) return '';
    
    // Türkçe karakterleri değiştir
    const turkishChars = { 'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U' };
    
    let code = text.toString()
        .trim()
        .toLowerCase()
        .replace(/[çğıöşü]/g, match => turkishChars[match])
        .replace(/\s+/g, '_')        // Boşlukları alt çizgi yap
        .replace(/[^a-z0-9_]/g, '')  // Alfanumerik olmayan karakterleri kaldır
        .substring(0, 20);            // Maksimum 20 karakter
    
    if (prefix) {
        code = prefix + '_' + code;
    }
    
    return code.toUpperCase();
}

// Tarih formatı dönüştürme
function formatDate(dateString, format = 'DD.MM.YYYY') {
    if (!dateString) return '';
    
    if (window.moment) {
        return moment(dateString).format(format);
    } else {
        // Basit tarih formatlaması
        const date = new Date(dateString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        if (format === 'DD.MM.YYYY') {
            return `${day}.${month}.${year}`;
        } else if (format === 'YYYY-MM-DD') {
            return `${year}-${month}-${day}`;
        } else {
            return `${day}.${month}.${year}`;
        }
    }
}

// Telefon numarası formatı
function formatPhoneNumber(phoneNumber) {
    if (!phoneNumber) return '';
    
    // Sadece rakamları al
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    // Türkiye telefon numarası formatı: +90 (5XX) XXX XX XX
    if (cleaned.length === 10) {
        return `+90 (${cleaned.substring(0, 3)}) ${cleaned.substring(3, 6)} ${cleaned.substring(6, 8)} ${cleaned.substring(8)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('0')) {
        return `+90 (${cleaned.substring(1, 4)}) ${cleaned.substring(4, 7)} ${cleaned.substring(7, 9)} ${cleaned.substring(9)}`;
    } else {
        return phoneNumber; // Orijinal formatı koru
    }
}

// Telefon numarası maskeleme
function maskPhoneNumber(phoneNumber) {
    if (!phoneNumber) return '';
    
    // Sadece rakamları al
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    if (cleaned.length >= 10) {
        // Son 4 haneyi göster, diğerlerini maskele
        const lastFour = cleaned.slice(-4);
        const maskedPart = cleaned.slice(0, -4).replace(/\d/g, '*');
        
        // Türkiye telefon numarası formatı: +90 (5**) *** ** XX
        if (cleaned.length === 10) {
            return `+90 (${maskedPart.substring(0, 3)}) ${maskedPart.substring(3, 6)} ${lastFour.substring(0, 2)} ${lastFour.substring(2)}`;
        } else {
            return maskedPart + lastFour;
        }
    } else {
        return phoneNumber.replace(/\d/g, '*');
    }
}

// E-posta maskeleme
function maskEmail(email) {
    if (!email) return '';
    
    const parts = email.split('@');
    if (parts.length !== 2) return email;
    
    const name = parts[0];
    const domain = parts[1];
    
    // İlk 2 ve son 1 karakteri göster, aradakileri maskele
    let maskedName;
    if (name.length <= 3) {
        maskedName = name.charAt(0) + '*'.repeat(name.length - 1);
    } else {
        maskedName = name.substring(0, 2) + '*'.repeat(name.length - 3) + name.charAt(name.length - 1);
    }
    
    return `${maskedName}@${domain}`;
}