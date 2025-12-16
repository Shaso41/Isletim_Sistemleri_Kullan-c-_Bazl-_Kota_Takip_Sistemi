# backend/QuotaManager.py
import json
import os

DATA_FILE = "users.json"
DEFAULT_QUOTA_MB = 100  # Varsayılan kullanıcı kotası

class QuotaManager:
    """
    Kullanıcı bazlı kotaları, şifreleri ve veri kalıcılığını (JSON) yönetir.
    Admin kullanıcısını ve dosya sistemi tutarlılığını otomatik yönetir.
    """
    def __init__(self):
        self.user_quotas = {}
        self.passwords = {}
        self.MB = 1024 * 1024

    def load_data_from_disk(self):
        """Diskteki users.json dosyasından ham veriyi yükler."""
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
        
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                try:
                    data = json.load(f)
                    self.user_quotas = data.get('quotas', {})
                    self.passwords = data.get('passwords', {})
                except json.JSONDecodeError:
                    print("[HATA] Kullanıcı veri dosyası (users.json) bozuk.")

    def save_data(self):
        """Tüm kullanıcı verilerini users.json dosyasına kaydeder."""
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
        
        data = {
            'quotas': self.user_quotas,
            'passwords': self.passwords
        }
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=4)
        print("[Sistem] Kullanıcı verileri diske kaydedildi.")

    def load_and_sync_data(self, project_root):
        """
        Veriyi yükler, fiziksel klasör varlığını kontrol ederek senkronize eder.
        """
        self.load_data_from_disk()

        users_to_remove = []

        # Fiziksel Klasör Kontrolü (Senkronizasyon)
        for user_id in list(self.user_quotas.keys()):
            if user_id == "admin": continue # Admin için klasör kontrolü yapılmaz

            home_dir_name = user_id + "_home"
            physical_dir_path = os.path.join(project_root, home_dir_name) 

            if not os.path.isdir(physical_dir_path):
                print(f"[UYARI] Kullanıcı '{user_id}' için fiziksel dizin silinmiş. Verisi JSON'dan kaldırılıyor.")
                users_to_remove.append(user_id)

        # Silinmesi Gerekenleri Kaldır
        for user_id in users_to_remove:
            if user_id in self.user_quotas:
                del self.user_quotas[user_id]
            if user_id in self.passwords:
                del self.passwords[user_id]

        # JSON Dosyasını Güncelle
        if users_to_remove:
            self.save_data()
            print(f"[Sistem] {len(users_to_remove)} kullanıcı sistemden silindi ve veri güncellendi.")
        
        # ADMIN KULLANICISINI KONTROL ET VE EKLE
        ADMIN_ID = "admin"
        ADMIN_PASS = "admin"
        ADMIN_LIMIT = 100000 * self.MB # Sınırsız gibi davranan yüksek kota

        if ADMIN_ID not in self.user_quotas:
            self.user_quotas[ADMIN_ID] = {'limit': ADMIN_LIMIT, 'usage': 0}
            self.passwords[ADMIN_ID] = ADMIN_PASS
            self.save_data()
            print(f"[Sistem] Yönetici kullanıcısı '{ADMIN_ID}' sisteme eklendi.")
        
        print(f"[Sistem] {len(self.user_quotas)} kullanıcı verisi yüklendi ve senkronize edildi.")

    def add_user(self, user_id, password, quota_mb=None): 
        """
        Yeni kullanıcı ekler. 
        quota_mb verilirse onu kullanır, verilmezse varsayılanı (DEFAULT_QUOTA_MB) kullanır.
        """
        # Eğer kota girilmediyse veya boşsa varsayılanı al
        if quota_mb is None or quota_mb == "":
            final_quota_mb = DEFAULT_QUOTA_MB
        else:
            final_quota_mb = float(quota_mb)

        quota_bytes = final_quota_mb * self.MB 
        
        self.user_quotas[user_id] = {
            'limit': quota_bytes,
            'usage': 0
        }
        self.passwords[user_id] = password
        self.save_data()
        return final_quota_mb

    def delete_user_data(self, user_id):
        """Kullanıcı verilerini sistemden kaldırır."""
        if user_id in self.user_quotas:
            del self.user_quotas[user_id]
        if user_id in self.passwords:
            del self.passwords[user_id]
        self.save_data()

    def set_quota(self, user_id, new_quota_mb): 
        """Yönetici tarafından kota güncelleme."""
        if user_id not in self.user_quotas:
            return False, f"HATA: Kullanıcı '{user_id}' sistemde kayıtlı değil."
        
        new_quota_bytes = new_quota_mb * self.MB
        
        if self.user_quotas[user_id]['usage'] > new_quota_bytes:
            current_usage_mb = self.user_quotas[user_id]['usage'] / self.MB
            return False, f"HATA: Yeni kota ({new_quota_mb} MB) mevcut kullanımdan ({current_usage_mb:.2f} MB) düşük olamaz."
            
        self.user_quotas[user_id]['limit'] = new_quota_bytes
        self.save_data()
        return True, f"BAŞARILI: '{user_id}' için yeni kota {new_quota_mb} MB olarak ayarlandı."

    def check_password(self, user_id, password):
        return self.passwords.get(user_id) == password

    def check_and_update_usage(self, user_id, required_size_bytes):
        if user_id not in self.user_quotas:
            return False, "HATA: Kullanıcı bulunamadı."

        quota_data = self.user_quotas[user_id]
        current_usage = quota_data['usage']
        limit = quota_data['limit']

        if current_usage + required_size_bytes > limit:
            remaining_mb = (limit - current_usage) / self.MB
            return False, f"HATA: Kota aşıldı! ({current_usage/self.MB:.2f} MB / {limit/self.MB:.2f} MB kullanılıyor). Kullanılabilecek alan: {remaining_mb:.2f} MB."

        quota_data['usage'] += required_size_bytes
        self.save_data()
        return True, f"-> Kullanım Güncellendi: {current_usage/self.MB:.2f} MB -> {quota_data['usage']/self.MB:.2f} MB"

    def decrease_usage(self, user_id, deleted_size_bytes):
        if user_id in self.user_quotas:
            # Kullanımı düşür
            self.user_quotas[user_id]['usage'] -= deleted_size_bytes
            
            # Kullanım sıfırın altına düşerse (çok nadir bir hata durumudur), sıfırla.
            if self.user_quotas[user_id]['usage'] < 0:
                self.user_quotas[user_id]['usage'] = 0
                
            # Diske kaydet
            self.save_data()
            return True
        return False

    def get_status(self, user_id):
        if user_id in self.user_quotas:
            data = self.user_quotas[user_id]
            return (data['usage'] / self.MB, data['limit'] / self.MB)
        return (0, 0)