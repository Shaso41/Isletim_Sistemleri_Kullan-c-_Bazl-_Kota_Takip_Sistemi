# backend/FileSystem.py
import os
import shutil 
import datetime
from QuotaManager import QuotaManager, DEFAULT_QUOTA_MB 

class FileSystem:
    def __init__(self, quota_manager):
        self.qm = quota_manager
        self.files = {} 
        self.home_dirs = {} 
        self.current_user = None 
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        
        self.qm.load_and_sync_data(self.project_root)
        self.sync_on_startup() 

    # --- YARDIMCI METOTLAR ---
    def _get_active_user(self):
        if self.current_user is None:
            raise PermissionError("HATA: Lütfen önce bir kullanıcı ile oturum açın (login).")
        return self.current_user
    
    def _get_physical_dir_path(self, user_id):
        home_dir_name = user_id + "_home" 
        return os.path.join(self.project_root, home_dir_name)

    def _get_physical_path(self, user_id, file_path_logical):
        file_name = os.path.basename(file_path_logical)
        physical_dir_path = self._get_physical_dir_path(user_id)
        return os.path.join(physical_dir_path, file_name)

    def is_in_user_directory(self, user_id, file_path):
        home_path = self.home_dirs.get(user_id, '')
        return file_path.startswith(home_path)
    
    def log_action(self, user_id, action, details):
        """Sistemi izlemek için log kaydı tutar."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] USER: {user_id} | ACTION: {action} | {details}\n"
        
        try:
            with open("system.log", "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Log yazma hatası: {e}")

    def sync_on_startup(self):
        print("[Sistem] Fiziksel dizinler taranıyor...")
        for user_id in self.qm.user_quotas.keys():
            if user_id == "admin": continue 
            
            home_path_logical = f"/home/{user_id}/"
            self.home_dirs[user_id] = home_path_logical 
            
            physical_dir_path = self._get_physical_dir_path(user_id)
            if os.path.isdir(physical_dir_path):
                for file_name in os.listdir(physical_dir_path):
                    if file_name.startswith('.'): continue
                    logical_path = os.path.join(home_path_logical, file_name).replace('\\', '/')
                    self.files[logical_path] = {'owner': user_id, 'size': 0}
        print("[Sistem] Dosya sistemi senkronizasyonu tamamlandı.")

    # --- KULLANICI YÖNETİMİ ---
    def register_user(self, user_id, password, quota_mb=None):
        # 1. Admin Kontrolü
        if self.current_user != 'admin':
            return "HATA: Yeni kullanıcı oluşturma yetkisi sadece 'admin' hesabına aittir."
            
        if user_id in self.qm.user_quotas: return f"HATA: Kullanıcı {user_id} zaten kayıtlı."
        if user_id == "admin": return "HATA: 'admin' ismi kullanılamaz."

        try: 
            # 2. Kota Yöneticisine gönder (Quota opsiyonel)
            assigned_quota = self.qm.add_user(user_id, password, quota_mb)
        except Exception as e: return f"HATA: Kullanıcı eklenemedi: {e}"
        
        self.home_dirs[user_id] = f"/home/{user_id}/"
        physical_dir_path = self._get_physical_dir_path(user_id)
        try:
            os.makedirs(physical_dir_path, exist_ok=True)
            
            # LOG EKLEME
            self.log_action("admin", "REGISTER", f"New User: {user_id}, Quota: {assigned_quota}MB")
            
            return f"BAŞARILI: Kullanıcı '{user_id}' oluşturuldu. (Kota: {assigned_quota} MB)"
        except OSError as e: return f"HATA: Dizin oluşturulamadı: {e}"
            
    def login(self, user_id, password):
        if user_id not in self.qm.user_quotas: return "HATA: Geçersiz kullanıcı ID."
        if self.qm.check_password(user_id, password):
            self.current_user = user_id
            
            # LOG EKLEME
            self.log_action(user_id, "LOGIN", "Successful login")
            
            return f"[{user_id}] Başarıyla giriş yapıldı."
        else: 
            # Hatalı girişi de loglayabiliriz (Opsiyonel ama güvenlik için iyi)
            self.log_action(user_id, "LOGIN_FAILED", "Wrong password attempt")
            return "HATA: Şifre yanlış."

    def logout(self):
        logged_out_user = self.current_user
        if logged_out_user:
            # LOG EKLEME
            self.log_action(logged_out_user, "LOGOUT", "Session ended")
            
        self.current_user = None
        return f"[{logged_out_user}] Oturum kapatıldı."
        
    def delete_user(self, user_id):
        if self.current_user != 'admin':
            return "HATA: Bu işlem sadece yönetici (admin) tarafından gerçekleştirilebilir."
        if user_id == 'admin': return "HATA: Yönetici hesabı silinemez."
        if user_id not in self.qm.user_quotas: return f"HATA: Kullanıcı '{user_id}' kayıtlı değil."
            
        physical_dir_path = self._get_physical_dir_path(user_id)
        try:
            if os.path.isdir(physical_dir_path):
                shutil.rmtree(physical_dir_path)
                print(f"[Sistem] Fiziksel dizin '{os.path.basename(physical_dir_path)}' silindi.")
        except Exception as e:
            print(f"[UYARI] Fiziksel silme hatası: {e}. Mantıksal silmeye devam ediliyor.")
        
        self.qm.delete_user_data(user_id) 
        if user_id in self.home_dirs: del self.home_dirs[user_id]
        self.files = {path: info for path, info in self.files.items() if info['owner'] != user_id}

        # LOG EKLEME
        self.log_action("admin", "DELETE_USER", f"Deleted User: {user_id}")

        return f"BAŞARILI: Kullanıcı '{user_id}' silindi."

    def set_user_quota(self, target_user_id, new_quota_mb): 
        if self.current_user != 'admin':
            return f"HATA: Bu işlem sadece yönetici (admin) tarafından gerçekleştirilebilir."
        if target_user_id == 'admin': return "HATA: Admin kotası güncellenemez."
        
        success, message = self.qm.set_quota(target_user_id, new_quota_mb)
        
        if success:
            # LOG EKLEME
            self.log_action("admin", "SET_QUOTA", f"User: {target_user_id}, New Quota: {new_quota_mb}MB")
            
        return message

    def list_users(self):
        if self.current_user != 'admin':
            return "HATA: Bu işlem sadece yönetici (admin) tarafından gerçekleştirilebilir."
        user_list = []
        if not self.qm.user_quotas: return "Sistemde kayıtlı kullanıcı bulunmamaktadır."
        for user_id in self.qm.user_quotas:
            usage_mb, limit_mb = self.qm.get_status(user_id)
            user_list.append(f"-> Kullanıcı ID: {user_id}, Kota: {limit_mb:.2f} MB, Kullanım: {usage_mb:.2f} MB")
        header = "--- Kayıtlı Kullanıcılar ve Kota Durumları ---\n"
        return header + "\n".join(user_list)

    # --- DOSYA İŞLEMLERİ (RWX) ---
    def create_file(self, file_path, size_mb):
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin hesabı dosya oluşturamaz." 

        size_bytes = size_mb * self.qm.MB 
        if not self.is_in_user_directory(user_id, file_path):
            return f"Erişim Reddedildi: Yalnızca kendi dizininde işlem yapabilirsin."

        success, message = self.qm.check_and_update_usage(user_id, size_bytes)
        if success:
            physical_dir_path = self._get_physical_dir_path(user_id)
            if not os.path.isdir(physical_dir_path):
                 try: os.makedirs(physical_dir_path)
                 except Exception as e:
                    self.qm.decrease_usage(user_id, size_bytes)
                    return f"HATA: Fiziksel dizin onarılamadı: {e}."

            physical_path = self._get_physical_path(user_id, file_path)
            try:
                # GÜNCELLEME: create işleminde utf-8 zorunlu
                with open(physical_path, 'w', encoding='utf-8') as f:
                    f.write(f"Bu dosya {size_mb} MB (simülasyon).")
                self.files[file_path] = {'owner': user_id, 'size': size_bytes}
                
                # LOG EKLEME
                self.log_action(user_id, "CREATE_FILE", f"Path: {file_path}, Size: {size_mb}MB")
                
                return f"BAŞARILI: '{file_path}' oluşturuldu. {message}"
            except Exception as e:
                self.qm.decrease_usage(user_id, size_bytes)
                return f"HATA: Yazma sorunu: {e}."
        else: 
            # Kota aşımını da loglayabiliriz
            self.log_action(user_id, "QUOTA_EXCEEDED", f"Attempted Size: {size_mb}MB")
            return message

    def write_to_file(self, file_path, content):
        """Dosyaya metin yazar (Append)."""
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin hesabı dosya içeriği değiştiremez."
        if file_path not in self.files: return "HATA: Yazılacak dosya bulunamadı."
        if self.files[file_path]['owner'] != user_id: return "Erişim Reddedildi."

        physical_path = self._get_physical_path(user_id, file_path)
        try:
            # GÜNCELLEME: write işleminde utf-8 zorunlu
            with open(physical_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{content}")
            
            # LOG EKLEME
            self.log_action(user_id, "WRITE_FILE", f"Path: {file_path} (Append)")
            
            return f"BAŞARILI: '{file_path}' dosyasına metin eklendi."
        except Exception as e: return f"HATA: {e}"

    def read_file(self, file_path):
        """Dosyanın içeriğini okur (cat)."""
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin hesabı dosya içeriğini okuyamaz."
        if file_path not in self.files: return "HATA: Okunacak dosya bulunamadı."
        if self.files[file_path]['owner'] != user_id: return "Erişim Reddedildi."

        physical_path = self._get_physical_path(user_id, file_path)
        try:
            if not os.path.exists(physical_path): return "HATA: Fiziksel dosya yok."
            
            # GÜNCELLEME: Okurken hata verirse (errors='replace') karakteri  ile değiştir, çökmesin.
            with open(physical_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # LOG EKLEME (Opsiyonel: Okuma işlemleri çok log yaratabilir ama denetim için iyidir)
            self.log_action(user_id, "READ_FILE", f"Path: {file_path}")
            
            return content if content else "[Dosya Boş]"
        except Exception as e: return f"HATA: {e}"

    def execute_file(self, file_path):
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if file_path not in self.files: return "HATA: Çalıştırılacak dosya bulunamadı."
        
        # LOG EKLEME (Engellenen işlemi de kaydediyoruz)
        self.log_action(user_id, "EXECUTE_ATTEMPT", f"Path: {file_path} (BLOCKED)")
        
        return f"HATA: [{user_id}] '{file_path}' dosyasında çalıştırma (Execute) izni yoktur."

    def delete_file(self, file_path):
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin hesabı dosya silemez."
        if file_path not in self.files: return "HATA: Dosya bulunamadı."
        if self.files[file_path]['owner'] != user_id: return "Erişim Reddedildi."
        
        # 1. Silinecek boyutu AL (Silmeden Önce!)
        deleted_size = self.files[file_path]['size'] 

        physical_path = self._get_physical_path(user_id, file_path)
        
        # 2. Fiziksel silme
        try: os.remove(physical_path)
        except FileNotFoundError: pass 
        except Exception as e: return f"HATA: {e}"

        # 3. Kota kullanımını DÜŞ
        self.qm.decrease_usage(user_id, deleted_size)
        
        # 4. Mantıksal kaydı sil
        del self.files[file_path]
        
        # LOG EKLEME
        self.log_action(user_id, "DELETE_FILE", f"Path: {file_path}, Size: {deleted_size} bytes")

        return f"BAŞARILI: '{file_path}' silindi."

    def list_files(self):
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin hesabı dosya listeleyemez." 
            
        home_path = self.home_dirs.get(user_id, '')
        file_list = []
        for path, info in self.files.items():
            if path.startswith(home_path):
                size_mb = info['size'] / self.qm.MB
                file_name = os.path.basename(path)
                file_list.append(f"-> {file_name} ({size_mb:.2f} MB)")
        
        if not file_list: return f"[{user_id}] Dizin boş: {home_path}"
        usage_mb, _ = self.qm.get_status(user_id)
        return f"[{user_id}] Dizin İçeriği ({usage_mb:.2f} MB Kullanım):\n" + "\n".join(file_list)
    
    def get_user_status(self):
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "[admin] Yönetici Hesabı: Kota takibi yoktur." 
        usage, limit = self.qm.get_status(user_id)
        return f"[{user_id}] Kota Durumu: {usage:.2f} MB / {limit:.2f} MB"
    def overwrite_file(self, file_path, content):
        """Dosyanın içeriğini silip yenisini yazar (Overwrite)."""
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin dosya içeriği değiştiremez."
        if file_path not in self.files: return "HATA: Dosya bulunamadı."
        if self.files[file_path]['owner'] != user_id: return "Erişim Reddedildi."

        physical_path = self._get_physical_path(user_id, file_path)
        try:
            # 'w' kipi dosyayı açarken içeriğini siler!
            with open(physical_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_action(user_id, "OVERWRITE_FILE", f"Path: {file_path}")
            return f"BAŞARILI: '{file_path}' içeriği değiştirildi."
        except Exception as e: return f"HATA: {e}"

    def truncate_file(self, file_path):
        """Dosyanın içeriğini tamamen temizler."""
        try: user_id = self._get_active_user()
        except PermissionError as e: return str(e)
        if user_id == "admin": return "HATA: Admin dosya değiştiremez."
        if file_path not in self.files: return "HATA: Dosya bulunamadı."
        if self.files[file_path]['owner'] != user_id: return "Erişim Reddedildi."

        physical_path = self._get_physical_path(user_id, file_path)
        try:
            # İçine hiçbir şey yazmadan 'w' ile açıp kapatmak içini temizler.
            with open(physical_path, 'w', encoding='utf-8') as f:
                pass 
            
            self.log_action(user_id, "TRUNCATE_FILE", f"Path: {file_path} (Cleared)")
            return f"BAŞARILI: '{file_path}' içi temizlendi."
        except Exception as e: return f"HATA: {e}"