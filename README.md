# 🩺 Diyabet Takip Sistemi (Diabetes Monitoring System)

![Image](https://github.com/user-attachments/assets/7fef6433-da6b-41b2-b0db-65f13fcf5685)

Bu proje, diyabet hastalarının günlük kan şekeri ölçümlerini kaydedebileceği ve doktorlarıyla paylaşabileceği **Python** tabanlı masaüstü bir uygulamadır. Modern bir kullanıcı arayüzü, güvenli şifreleme, rol tabanlı erişim kontrolü ve grafiksel analiz özellikleri sunar.

---

## 📌 Özellikler

- 👤 **Rol Tabanlı Erişim:** Hasta ve doktor için ayrı paneller
- 💉 **Kan Şekeri Takibi:** Günlük ölçümleri kaydetme ve analiz etme
- 📊 **Veri Görselleştirme:** Geçmiş verilerin grafiksel sunumu
- 🔐 **SHA-256 ile Şifreleme:** Güvenli giriş sistemi
- 📧 **Mail ile Şifre Sıfırlama:** SMTP üzerinden geçici şifre gönderimi
- 🧠 **Kural Tabanlı Öneri:** Şeker seviyesi ve belirtilere göre diyet/egzersiz tavsiyesi

---

## 🧱 Kullanılan Teknolojiler

| Teknoloji        | Açıklama                        |
|------------------|----------------------------------|
| Python           | Programlama dili                |
| CustomTkinter    | Modern GUI arayüzü              |
| MySQL            | Veritabanı yönetimi             |
| XAMPP            | Yerel veritabanı sunucusu       |
| SHA-256          | Parola güvenliği                |
| SMTP             | E-posta gönderimi               |

---

## 🗃️ Veritabanı Yapısı (ER Diyagram)

![Image](https://github.com/user-attachments/assets/645a9d02-4fc8-4e15-9ebe-c5bbfa0f023a)

- `Kullanici`: Ortak kullanıcı yapısı (hasta/doktor)
- `Doktor`: KullaniciID ile bağlı
- `Hasta`: Hem KullaniciID hem de DoktorID içerir
- `Olcum`: HastaID üzerinden hasta ile ilişkili
- `DiyetEgzersiz`: Günlük sağlık aktiviteleri
- `Belirti`: Günlük semptom kayıtları

---

## 🧠 Kural Tabanlı Öneri Algoritması

```python
def KuralTabanliOneri(seviye, belirtiler):
    if not seviye or not belirtiler:
        return "⚠ Gerekli veriler eksik."

    b = [bel.lower() for bel in belirtiler]

    if seviye >= 180:
        if {"yaraların yavaş iyileşmesi", "polifaji", "polidipsi"}.issubset(b):
            return "Şekersiz Diyet önerilir. Klinik Egzersiz yapılmalı."
        if {"yaraların yavaş iyileşmesi", "kilo kaybı"}.issubset(b):
            return "Şekersiz Diyet önerilir. Yürüyüş yapılmalı."
    elif 110 < seviye < 180:
        if {"bulanık görme", "nöropati", "yorgunluk"}.issubset(b):
            return "Az Şekerli Diyet önerilir. Yürüyüş yapılmalı."
    elif 70 <= seviye <= 110:
        if {"yorgunluk", "kilo kaybı"}.issubset(b):
            return "Az Şekerli Diyet önerilir. Yürüyüş yapılmalı."
    elif seviye < 70:
        if {"nöropati", "polifaji", "yorgunluk"}.issubset(b):
            return "Dengeli Beslenme önerilir. Egzersiz yapılmamalı."

    return "⚠ Bu belirtiler ve seviye için öneri bulunamadı."
```

---


## 👨‍💻 Geliştiriciler

- Sadık Gölpek – [sadikgolpek@gmail.com](mailto:sadikgolpek@gmail.com)  
- Ali Kılınç – [aliklnc4104@gmail.com](mailto:aliklnc4104@gmail.com)

---

![Image](https://github.com/user-attachments/assets/a138142e-d592-4beb-90c4-8879c5569fb1)

![Image](https://github.com/user-attachments/assets/e1922ab0-623f-4944-9300-c637295f8546)

## 📚 Kaynakça

1. [Python Resmi Belgeleri](https://docs.python.org/)
2. [MySQL Referans Dokümantasyonu](https://dev.mysql.com/doc/)
3. [XAMPP Resmi Sitesi](https://www.apachefriends.org/)
4. [dbdiagram.io](https://dbdiagram.io/)
5. [Şadi Evren Şeker - Veritabanı Eğitimi (YouTube)](https://www.youtube.com/playlist?list=PLh9ECzBB8tJOS7WQKdeUaAa5fmPLYAouD)
