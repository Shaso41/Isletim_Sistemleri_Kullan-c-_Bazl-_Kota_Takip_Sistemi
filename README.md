# 🖥️ Kullanıcı Bazlı Kota Takip Sistemi (İşletim Sistemleri Projesi)

Bu proje, Python (Flask) ve JavaScript kullanılarak geliştirilmiş, web tabanlı bir **İşletim Sistemi Dosya Yönetimi Simülasyonudur**.

Proje; kullanıcı yönetimi, dosya izinleri (RWX), disk kotası takibi ve yönetici (Admin) yetkileri gibi temel işletim sistemi kavramlarını simüle eder.

## 🚀 Özellikler

* **🔐 Kullanıcı Sistemi:** Kayıt olma, giriş yapma ve güvenli oturum yönetimi.
* **📂 Dosya İşlemleri:**
    * **Oluşturma (Create):** Belirtilen boyutta dosya oluşturma (Yer ayırma).
    * **Yazma (Write):** Dosya sonuna metin ekleme (Append).
    * **Okuma (Read/Cat):** Dosya içeriğini görüntüleme.
    * **Silme (Delete):** Dosyayı diskten ve kayıtlardan silme.
    * **Listeleme (Ls):** Dizin içeriğini görüntüleme.
* **🛡️ İzin Simülasyonu (RWX):** Okuma, Yazma ve Çalıştırma izinlerinin simülasyonu. (Güvenlik gereği çalıştırma izni engellenmiştir).
* **💾 Kalıcılık (Persistence):** Sunucu kapansa bile veriler JSON ve fiziksel klasör yapısı sayesinde korunur.
* **📊 Kota Yönetimi:** Her kullanıcının varsayılan 100MB disk kotası vardır.
* **👑 Admin Paneli:** Özel yönetici yetkileri ile kullanıcıları yönetme ve kotaları değiştirme imkanı.

## 🛠️ Teknolojiler

* **Backend:** Python 3, Flask
* **Frontend:** HTML5, CSS3, JavaScript (Fetch API)
* **Veri Tabanı:** JSON (Dosya tabanlı NoSQL yaklaşımı)

## ⚙️ Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1.  **Repoyu klonlayın:**
    ```bash
    git clone [https://github.com/Shaso41/Isletim_Sistemleri_Kullan-c-_Bazl-_Kota_Takip_Sistemi.git](https://github.com/Shaso41/Isletim_Sistemleri_Kullan-c-_Bazl-_Kota_Takip_Sistemi.git)
    cd Isletim_Sistemleri_Kullan-c-_Bazl-_Kota_Takip_Sistemi
    ```

2.  **Backend klasörüne gidin:**
    ```bash
    cd backend
    ```

3.  **Uygulamayı başlatın:**
    ```bash
    python -m flask run
    ```

4.  **Tarayıcıda açın:**
    `http://127.0.0.1:5000` adresine gidin.

## 📖 Komut Listesi

Web terminalinde kullanabileceğiniz komutlar:

### Temel Komutlar
| Komut | Açıklama |
| :--- | :--- |
register <id> <şifre> [MB] | Yeni kullanıcı oluşturur. (Sadece Admin. Kota girilmezse 100MB). |
| `login <id> <şifre>` | Sisteme giriş yapar. |
| `logout` | Oturumu kapatır. |
| `help` | Komut listesini gösterir. |

### Dosya İşlemleri (Giriş Yapılmalı)
| Komut | Açıklama |
| :--- | :--- |
| `ls` | Dosyaları listeler. |
| `create <MB> <yol>` | Belirtilen boyutta dosya oluşturur. |
| `write <yol> <metin>` | Dosyanın içine metin yazar/ekler. |
| `overwrite <yol> <metin>` | Dosyanın içeriğini tamamen siler ve yenisini yazar. |
| `truncate <yol>` | Dosyanın içeriğini tamamen boşaltır (0 byte yapar). |
| `cat <yol>` | Dosyanın içeriğini okur. |
| `delete <yol>` | Dosyayı siler. |
| `run <yol>` | Dosyayı çalıştırmayı dener (İzin testi). |
| `status` | Mevcut kota durumunu gösterir. |

### Yönetici (Admin) Komutları
**Admin Girişi:** `login admin admin`

| Komut | Açıklama |
| :--- | :--- |
| `list_users` | Sistemdeki tüm kullanıcıları ve kotalarını listeler. |
| `delete_user <id>` | Bir kullanıcıyı ve tüm dosyalarını siler. |
| `set_quota <id> <MB>` | Kullanıcının disk kotasını günceller. |

## 🏗️ Proje Yapısı