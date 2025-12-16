import json
import os
import hashlib # Hashing kütüphanesi

DEFAULT_QUOTA_MB = 100

class QuotaManager:
    def __init__(self):
        self.user_quotas = {}
        self.passwords = {}
        self.file_path = "users.json"
        self.MB = 1024 * 1024  # 1 MB in Bytes

    def _hash_password(self, password):
        """Şifreyi SHA-256 ile hashler."""
        return hashlib.sha256(password.encode()).hexdigest()

    def load_and_sync_data(self, project_root):
        """Verileri JSON dosyasından yükler, yoksa default admin oluşturur."""
        # JSON dosyasını backend klasöründe (app.py ile aynı yerde) arayalım
        self.file_path = os.path.join(project_root, "backend", "users.json")
        
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_quotas = data.get('quotas', {})
                    self.passwords = data.get('passwords', {})
            except Exception as e:
                print(f"[HATA] Veritabanı okunamadı: {e}")
        else:
            print("[Sistem] Veritabanı bulunamadı, yeni oluşturuluyor...")
            # İŞTE BURASI DÜZELDİ: Admin şifresini hashleyerek kaydediyoruz
            self.user_quotas['admin'] = {'limit': float('inf'), 'usage': 0}
            self.passwords['admin'] = self._hash_password('admin') 
            self.save_data()

    def save_data(self):
        data = {
            'quotas': self.user_quotas,
            'passwords': self.passwords
        }
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Kaydetme Hatası: {e}")

    def add_user(self, user_id, password, quota_mb=None):
        if quota_mb is None or quota_mb == "":
            final_quota_mb = DEFAULT_QUOTA_MB
        else:
            final_quota_mb = float(quota_mb)

        quota_bytes = final_quota_mb * self.MB
        
        self.user_quotas[user_id] = {
            'limit': quota_bytes,
            'usage': 0
        }
        # Şifreyi hashleyerek kaydet
        self.passwords[user_id] = self._hash_password(password)
        self.save_data()
        return final_quota_mb

    def check_password(self, user_id, password):
        stored_hash = self.passwords.get(user_id)
        # Girilen şifreyi hashleyip, kayıtlı hash ile kıyasla
        return stored_hash == self._hash_password(password)

    def check_and_update_usage(self, user_id, required_size_bytes):
        if user_id not in self.user_quotas:
            return False, "Kullanıcı bulunamadı."
            
        quota_data = self.user_quotas[user_id]
        current_usage = quota_data['usage']
        limit = quota_data['limit']

        # Admin için sınır yok
        if user_id == "admin": 
            # Admin de olsa istatistik için usage arttırılabilir ama limit kontrolü yok
            return True, ""

        if current_usage + required_size_bytes > limit:
            remaining_mb = (limit - current_usage) / self.MB
            return False, f"HATA: Kota aşıldı! Kalan: {remaining_mb:.2f} MB. (Gerekli: {required_size_bytes/self.MB:.2f} MB)"

        self.user_quotas[user_id]['usage'] += required_size_bytes
        self.save_data()
        return True, ""

    def decrease_usage(self, user_id, deleted_size_bytes):
        if user_id in self.user_quotas:
            self.user_quotas[user_id]['usage'] -= deleted_size_bytes
            if self.user_quotas[user_id]['usage'] < 0:
                self.user_quotas[user_id]['usage'] = 0
            self.save_data()
            return True
        return False

    def get_status(self, user_id):
        if user_id in self.user_quotas:
            u = self.user_quotas[user_id]['usage'] / self.MB
            l = self.user_quotas[user_id]['limit'] / self.MB
            return u, l
        return 0, 0
    
    def set_quota(self, target_user_id, new_quota_mb):
        if target_user_id not in self.user_quotas:
            return False, f"HATA: Kullanıcı {target_user_id} bulunamadı."
            
        try:
            limit_bytes = float(new_quota_mb) * self.MB
            self.user_quotas[target_user_id]['limit'] = limit_bytes
            self.save_data()
            return True, f"BAŞARILI: {target_user_id} kotası {new_quota_mb} MB yapıldı."
        except ValueError:
            return False, "HATA: Geçersiz kota değeri."
            
    def delete_user_data(self, user_id):
        if user_id in self.user_quotas: del self.user_quotas[user_id]
        if user_id in self.passwords: del self.passwords[user_id]
        self.save_data()