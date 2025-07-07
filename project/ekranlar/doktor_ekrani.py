import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinter.ttk import Treeview
from veritabani import baglanti_olustur, sifre_uret, sifre_hashle
from PIL import Image
from customtkinter import CTkImage
from datetime import datetime, date
from tkcalendar import DateEntry
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Tuple

# Sabitler
DEFAULT_IMG_PATH = fr"C:\Users\sadik\Desktop\KOU CENG 2\2.DÖNEM\Prolab\Prolab3\230201040_230201065\assets\default.png"
MAIL_GONDEREN = "dortyuz9@gmail.com"
MAIL_SIFRE = "ydxo yqpa uszn fivc"

class DoktorPanel:
    def __init__(self, kullanici_id):
        self.kullanici_id = kullanici_id
        self.doktor_id = None
        self.aktif_frame = None
        self.profil_img_label = None  # ek olarak header widget'ını tutacağız
        
        # Ana pencere ayarları
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Doktor Paneli")
        self.root.geometry("1200x700")
        
        self.doktor_id_al()
        self.ana_arayuz_olustur()
        
    def doktor_id_al(self) -> bool:
        """Doktor ID'sini veritabanından alır"""
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT DoktorID FROM Doktor WHERE KullaniciID = %s", (self.kullanici_id,))
            row = cur.fetchone()
            if row:
                self.doktor_id = row[0]
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Doktor ID alınamadı: {e}")
            
        if not self.doktor_id:
            messagebox.showerror("Hata", "Doktor ID bulunamadı.")
            return False
        return True
    
    def olcum_kontrolu(self, hasta_id, kontrol_tarihi: date) -> str:
        """Seçilen tarih için ölçümleri kontrol eder ve uyarı mesajı döner."""
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute(
                "SELECT SeviyeMgDl FROM Olcum WHERE HastaID = %s AND DATE(TarihSaat) = %s AND Gecerli = TRUE",
                (hasta_id, kontrol_tarihi)
            )
            measurements = cur.fetchall()
            conn.close()
        except Exception as e:
            return f"Hata: Ölçüm verileri alınamadı: {e}"
        
        formatted_date = kontrol_tarihi.strftime("%d.%m.%Y")
        alerts = []
        
        if not measurements:
            return f"Ölçüm Eksik Uyarısı: Seçilen tarihte hiçbir ölçüm yapılmamış! ({formatted_date})"
        
        count = len(measurements)
        if count < 3:
            alerts.append(f"Ölçüm Yetersiz Uyarısı: Seçilen tarihte sadece {count} ölçüm yapılmış!")
        
        avg = sum(m[0] for m in measurements) / count
        
        if avg < 70:
            alerts.append("Hastanın kan şekeri seviyesi 70 mg/dL'nin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir.")
        if 111 <= avg <= 150:
            alerts.append("Hastanın kan şekeri 111-150 mg/dL arasında. Durum izlenmeli.")
        if 151 <= avg <= 200:
            alerts.append("Hastanın kan şekeri 151-200 mg/dL arasında. Diyabet kontrolü gereklidir.")
        if avg > 200:
            alerts.append("Hastanın kan şekeri 200 mg/dL'nin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir.")
        
        if not alerts:
            alerts.append("Tüm ölçümler normal.")
        
        return "\n".join(alerts) + f"\n({formatted_date})"


    def olcum_kontrolu_yap(self):
        """Ölçüm kontrolü işlemini, seçili hasta ve seçilen tarihe göre gerçekleştirir."""
        sel = self.hasta_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin.")
            return
        
        # Seçili hasta bilgisini al
        tc = self.hasta_tree.item(sel[0])["values"][0]
        hasta_id = self.tc_den_hasta_id_al(tc)
        if not hasta_id:
            messagebox.showerror("Hata", "Hasta ID alınamadı.")
            return
        
        # Sağ paneldeki içerikleri temizle (sol panel yani hasta listesi korunur)
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        # Sağ panelde tarih seçici ve ilgili butonları ekleyelim
        ctk.CTkLabel(self.right_frame, text="Kontrol Tarihi:", font=("Arial", 14))\
            .pack(padx=10, pady=(20,5))
        tarih_secici = DateEntry(self.right_frame, date_pattern="dd-MM-yyyy")
        tarih_secici.pack(padx=10, pady=5)
        
        # "Kontrol Et" butonu
        def on_kontrol_et():
            selected_date = tarih_secici.get_date()
            uyarı_mesaji = self.olcum_kontrolu(hasta_id, selected_date)
            messagebox.showinfo("Ölçüm Kontrolü", uyarı_mesaji)
        
        ctk.CTkButton(self.right_frame, text="Kontrol Et", command=on_kontrol_et)\
            .pack(padx=10, pady=10)
        
        # "Geri" butonu: Sağ panelin orijinal içeriğine (örneğin hasta fotoğrafı ve butonlar) dönmek için
        ctk.CTkButton(self.right_frame, text="← Geri",
                      command=self.hasta_listesi_goster,
                      fg_color="#6c757d", hover_color="#545b62")\
            .pack(pady=10)



    # --- Modern Arayüz Düzenlemeleri ---
    def ana_arayuz_olustur(self):
        """Ana arayüzü oluşturur - modern düzen"""
        # Header: üste geniş, koyu mavi alan; profil resmi ve başlık bilgileri
        self.header_frame = ctk.CTkFrame(self.root, height=100, fg_color="#2b5ce6", corner_radius=0)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        profile_frame = ctk.CTkFrame(self.header_frame, width=80, height=80, fg_color="white")
        profile_frame.place(x=20, y=10)
        # Header profil resmi; bu widget ile güncellemeleri yapacağız:
        self.header_profile_label = ctk.CTkLabel(profile_frame, text="👤", font=("Arial", 30))
        self.header_profile_label.pack(expand=True)
        title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_frame.place(x=120, y=20)
        ctk.CTkLabel(title_frame, text="Doktor Paneli", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Diyabet Takip Sistemi", font=("Arial", 14), text_color="#cccccc").pack(anchor="w")
        
        # Sidebar: sol tarafta modern beyaz panel, hızlı işlem butonları
        self.sidebar_frame = ctk.CTkFrame(self.root, width=250, fg_color="white", corner_radius=15)
        self.sidebar_frame.place(x=20, y=120, relheight=0.78)
        ctk.CTkLabel(self.sidebar_frame, text="Hızlı İşlemler", font=("Arial", 20, "bold"),
                   text_color="#2b5ce6").pack(pady=(20,10))
        btn_texts_commands = [
            ("🏠 Ana Sayfa", self.ana_sayfa_goster),
            ("👤 Yeni Hasta Ekle", self.hasta_ekle_form_goster),
            ("📋 Hasta Listesi", self.hasta_listesi_goster),
            ("🔧 Profil Ayarları", self.profil_ayarlari_goster),
            ("📈 Geçmiş & Filtreleme", self.gecmis_filtreleme_goster),  # <<-- new button
            ("🚪 Çıkış", self.root.destroy)
        ]
        for text, cmd in btn_texts_commands:
            ctk.CTkButton(self.sidebar_frame, text=text, command=cmd,
                          width=200, height=40, font=("Arial", 12)).pack(pady=5, padx=20)
        
        # Ana içerik alanı: sağ panel modern beyaz kutu
        self.content_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=15)
        self.content_frame.place(x=290, y=120, relwidth=0.67, relheight=0.78)
        self.ana_sayfa_goster()
        
        # Footer: alt kısım, koyu gri alan
        self.footer_frame = ctk.CTkFrame(self.root, height=60, fg_color="#343a40", corner_radius=0)
        self.footer_frame.pack(side="bottom", fill="x")
        self.footer_frame.pack_propagate(False)
        footer_left = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        footer_left.pack(side="left", padx=20)
        ctk.CTkLabel(footer_left, text="💊 Diyabet Takip Sistemi", font=("Arial", 14, "bold"), text_color="white").pack(anchor="w", pady=5)
        ctk.CTkLabel(footer_left, text="Sağlığa önem verin!", font=("Arial", 10), text_color="#adb5bd").pack(anchor="w")
    
    def temizle_icerik(self):
        """İçerik panelini temizler"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def ana_sayfa_goster(self):
        """Ana sayfa içeriğini gösterir"""
        self.temizle_icerik()
        
        # Added enhanced banner
        banner_frame = ctk.CTkFrame(self.content_frame, fg_color="#e9ecef", corner_radius=10)
        banner_frame.pack(fill="x", padx=20, pady=(20,10))
        ctk.CTkLabel(banner_frame, text="Hoşgeldiniz, Doktor!", font=("Arial", 26, "bold"), text_color="#2b5ce6").pack(padx=10, pady=10)
        
        ctk.CTkLabel(self.content_frame, text="Doktor Paneli - Ana Sayfa", 
                    font=("Arial", 24, "bold")).pack(pady=30)
        
        # İstatistik kartları
        stats_frame = ctk.CTkFrame(self.content_frame)
        stats_frame.pack(pady=20, padx=20, fill="x")
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Hasta WHERE DoktorID = %s", (self.doktor_id,))
            hasta_sayisi = cur.fetchone()[0]
            conn.close()
            
            ctk.CTkLabel(stats_frame, text=f"Toplam Hasta Sayısı: {hasta_sayisi}", 
                        font=("Arial", 16)).pack(pady=10)
        except:
            ctk.CTkLabel(stats_frame, text="İstatistikler yüklenemedi", 
                        font=("Arial", 16)).pack(pady=10)
        
        # Hoş geldin mesajı
        hosgeldin_frame = ctk.CTkFrame(self.content_frame)
        hosgeldin_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(hosgeldin_frame, 
                    text="Diyabet Takip Sistemi'ne hoş geldiniz!\n\n"
                         "Sol menüden işlemlerinizi gerçekleştirebilirsiniz:\n"
                         "• Yeni hasta ekleyebilirsiniz\n"
                         "• Hasta listesini görüntüleyebilirsiniz\n"
                         "• Profil ayarlarınızı düzenleyebilirsiniz",
                    font=("Arial", 14), justify="left").pack(pady=30)
    
    def hasta_ekle_form_goster(self):
        """Hasta ekleme formunu gösterir"""
        self.temizle_icerik()
        
        ctk.CTkLabel(self.content_frame, text="Yeni Hasta Ekle", 
                    font=("Arial", 20, "bold")).pack(pady=20)
        
        # Form frame'i
        form_frame = ctk.CTkFrame(self.content_frame)
        form_frame.pack(pady=20, padx=50, fill="both", expand=True)
        
        # Form alanları
        self.entry_tc = ctk.CTkEntry(form_frame, placeholder_text="TC Kimlik No", width=300, height=40)
        self.entry_tc.pack(pady=10)
        
        self.entry_ad = ctk.CTkEntry(form_frame, placeholder_text="Ad", width=300, height=40)
        self.entry_ad.pack(pady=10)
        
        self.entry_soyad = ctk.CTkEntry(form_frame, placeholder_text="Soyad", width=300, height=40)
        self.entry_soyad.pack(pady=10)
        
        self.entry_email = ctk.CTkEntry(form_frame, placeholder_text="Email", width=300, height=40)
        self.entry_email.pack(pady=10)
        
        ctk.CTkLabel(form_frame, text="Cinsiyet", font=("Arial", 14)).pack(pady=(20, 5))
        self.var_cinsiyet = ctk.StringVar(value="E")
        ctk.CTkOptionMenu(form_frame, variable=self.var_cinsiyet, values=["E", "K"], width=300).pack(pady=5)
        
        self.entry_dogum = ctk.CTkEntry(form_frame, placeholder_text="Doğum Tarihi (YYYY-AA-GG)", width=300, height=40)
        self.entry_dogum.pack(pady=10)
        
        # Kaydet butonu
        ctk.CTkButton(form_frame, text="Hastayı Kaydet", command=self.hasta_kaydet,
                     width=300, height=50, font=("Arial", 14, "bold")).pack(pady=30)
    
    def hasta_kaydet(self):
        """Yeni hasta kaydeder"""
        tc = self.entry_tc.get().strip()
        ad = self.entry_ad.get().strip()
        soyad = self.entry_soyad.get().strip()
        email = self.entry_email.get().strip()
        cinsiyet = self.var_cinsiyet.get()
        dogum_tarihi = self.entry_dogum.get().strip()
        
        if len(tc) != 11 or not tc.isdigit():
            messagebox.showerror("Hata", "TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır.")
            return
        
        if not all([ad, soyad, email, dogum_tarihi]):
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun.")
            return
        
        sifre = sifre_uret()
        sifre_hash = sifre_hashle(sifre)
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO Kullanici (TC, Ad, Soyad, Email, Cinsiyet, DogumTarihi, SifreHash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (tc, ad, soyad, email, cinsiyet[0], dogum_tarihi, sifre_hash))
            conn.commit()
            
            cur.execute("SELECT LAST_INSERT_ID()")
            yeni_uid = cur.fetchone()[0]
            cur.execute("INSERT INTO Hasta (KullaniciID, DoktorID) VALUES (%s, %s)", (yeni_uid, self.doktor_id))
            conn.commit()
            
            print(f"[TERMINAL] Hasta eklendi: TC={tc}, Şifre={sifre}")
            
            with open("sifre_kayitlari.txt", "a", encoding="utf-8") as f:
                f.write(f"{ad} {soyad} - TC: {tc} -  Şifre: {sifre}\n")
            
            self.mail_gonder(email, ad, soyad, tc, sifre)
            
            messagebox.showinfo("Başarılı", f"{ad} {soyad} kaydedildi.\n şifre: {sifre}")
            
            # Formu temizle
            for entry in [self.entry_tc, self.entry_ad, self.entry_soyad, self.entry_email, self.entry_dogum]:
                entry.delete(0, "end")
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Hasta eklenemedi: {e}")
            if conn:
                conn.rollback()
                conn.close()
    
    def mail_gonder(self, alici, ad, soyad, tc, sifre):
        """E-posta gönderir"""
        try:
            msg = MIMEMultipart()
            msg["From"] = MAIL_GONDEREN
            msg["To"] = alici
            msg["Subject"] = "Diyabet Takip Sistemi – Giriş Bilgileri"
            
            icerik = f"""Merhaba {ad} {soyad},

Diyabet Takip Sistemi'ne kaydınız başarıyla oluşturulmuştur.

TC Kimlik Numaranız: {tc}
Geçici Şifreniz: {sifre}

Lütfen bu bilgileri kimseyle paylaşmayınız ve ilk girişte şifrenizi değiştiriniz.

Sağlıklı günler dileriz."""
            
            msg.attach(MIMEText(icerik, "plain", "utf-8"))
            
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(MAIL_GONDEREN, MAIL_SIFRE)
                server.send_message(msg)
            
            print("✅ E-posta gönderildi.")
            
        except Exception as e:
            print("❌ E-posta gönderilemedi:", e)
    
    def hasta_listesi_goster(self):
        """Hasta listesini gösterir"""
        self.temizle_icerik()
        
        ctk.CTkLabel(self.content_frame, text="Hasta Listesi", 
                     font=("Arial", 20, "bold")).pack(pady=20)
        
        # Ana container
        main_container = ctk.CTkFrame(self.content_frame)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sol: Hasta listesi
        list_frame = ctk.CTkFrame(main_container)
        list_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        
        cols = ("TC", "Ad", "Soyad", "Email", "Cinsiyet", "Doğum Tarihi")
        self.hasta_tree = Treeview(list_frame, columns=cols, show="headings", height=15)
        for c in cols:
            self.hasta_tree.heading(c, text=c)
            self.hasta_tree.column(c, width=120, anchor="center")
        self.hasta_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sağ: Hasta fotoğrafı ve işlemler
        self.right_frame = ctk.CTkFrame(main_container, width=300)
        self.right_frame.pack(side="right", fill="y", padx=(5, 10), pady=10)
        self.right_frame.pack_propagate(False)
        
        self.hasta_foto_label = ctk.CTkLabel(self.right_frame, text="Hasta Fotoğrafı")
        self.hasta_foto_label.pack(pady=10)
        
        # İşlem butonları
        button_frame = ctk.CTkFrame(self.right_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        buttons = [
            ("🔍 Analiz Grafiği", self.hasta_analiz_goster),
            ("📊 Kural Tabanlı Panel", self.kural_panel_ac),
            ("📏 Ölçüm Kontrolü Yap", self.olcum_kontrolu_yap),
            ("🍽️ Diyet ve Egzersiz", self.diyet_ve_egzersiz_goster),
            ("🗑️ Hastayı Sil", self.hasta_sil)
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(button_frame, text=text, command=command, width=250, height=40)
            if "Sil" in text:
                btn.configure(fg_color="red", hover_color="darkred")
            btn.pack(pady=5)
        
        # Event binding
        self.hasta_tree.bind("<<TreeviewSelect>>", self.hasta_secim_degisti)
        
        self.hasta_listesi_yukle()
    
    def hasta_listesi_yukle(self):
        """Hasta listesini veritabanından yükler"""
        for item in self.hasta_tree.get_children():
            self.hasta_tree.delete(item)
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("""
                SELECT k.TC, k.Ad, k.Soyad, k.Email, k.Cinsiyet, k.DogumTarihi
                FROM Hasta h
                JOIN Kullanici k ON k.KullaniciID = h.KullaniciID
                WHERE h.DoktorID = %s
            """, (self.doktor_id,))
            
            for row in cur.fetchall():
                self.hasta_tree.insert("", "end", values=row)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Hasta listesi yüklenemedi: {e}")
    
    def hasta_secim_degisti(self, event):
        """Hasta seçimi değiştiğinde çalışır"""
        sel = self.hasta_tree.selection()
        if sel:
            tc = self.hasta_tree.item(sel[0])["values"][0]
            self.hasta_foto_goster(tc)
    
    def _get_image(self, img_binary: Optional[bytes], size: Tuple[int, int]) -> Optional[CTkImage]:
        """Görseli oku ve istenilen boyuta yeniden boyutlandır."""
        try:
            if img_binary:
                img_data = io.BytesIO(img_binary)
            else:
                with open(DEFAULT_IMG_PATH, "rb") as f:
                    img_data = io.BytesIO(f.read())
            img = Image.open(img_data).resize(size)
            return CTkImage(light_image=img, size=size)
        except Exception as e:
            print(f"Image loading error: {e}")
            return None
    
    def hasta_foto_goster(self, tc: str) -> None:
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT KullaniciID, ProfilResim FROM Kullanici WHERE TC = %s", (tc,))
            row = cur.fetchone()
            foto = None
            if row and row[1]:
                foto = self._get_image(row[1], (150, 150))
            else:
                foto = self._get_image(None, (150, 150))
            if foto:
                self.hasta_foto_label.configure(image=foto, text="")
                self.hasta_foto_label.image = foto
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Fotoğraf yüklenemedi: {e}")
    
    def hasta_analiz_goster(self):
        """Seçili hastanın analiz grafiğini gösterir"""
        sel = self.hasta_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin.")
            return
        
        tc = self.hasta_tree.item(sel[0])["values"][0]
        hasta_id = self.tc_den_hasta_id_al(tc)
        if not hasta_id:
            return
        
        self.analiz_grafigi_goster(hasta_id)

    def diyet_ve_egzersiz_goster(self):
            # Seçili hasta kontrolü
        sel = self.hasta_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin.")
            return
        tc = self.hasta_tree.item(sel[0])["values"][0]
        hasta_id = self.tc_den_hasta_id_al(tc)
        if not hasta_id:
            messagebox.showerror("Hata", "Hasta ID alınamadı.")
            return

        try:
            conn = baglanti_olustur()
            cur = conn.cursor()

            # Diyet için kayıtlar (yapıldı ve yapılmadı olanlar)
            cur.execute("""
                SELECT COUNT(*) FROM DiyetEgzersiz 
                WHERE HastaID = %s AND Tip = 'diyet' AND Durum IN ('yapıldı', 'yapılmadı')
            """, (hasta_id,))
            toplam_diyet = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM DiyetEgzersiz 
                WHERE HastaID = %s AND Tip = 'diyet' AND Durum = 'yapıldı'
            """, (hasta_id,))
            yapilan_diyet = cur.fetchone()[0]

            # Egzersiz için kayıtlar
            cur.execute("""
                SELECT COUNT(*) FROM DiyetEgzersiz 
                WHERE HastaID = %s AND Tip = 'egzersiz' AND Durum IN ('yapıldı', 'yapılmadı')
            """, (hasta_id,))
            toplam_egzersiz = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM DiyetEgzersiz 
                WHERE HastaID = %s AND Tip = 'egzersiz' AND Durum = 'yapıldı'
            """, (hasta_id,))
            yapilan_egzersiz = cur.fetchone()[0]
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Veri çekme hatası: {e}")
            return

        # Yüzdelik hesaplamaları
        yuzde_diyet = (yapilan_diyet / toplam_diyet * 100) if toplam_diyet > 0 else 0
        yuzde_egzersiz = (yapilan_egzersiz / toplam_egzersiz * 100) if toplam_egzersiz > 0 else 0

        # İçerik alanını temizleyip yeni panel oluşturun
        self.temizle_icerik()
        panel_frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=15)
        panel_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(panel_frame, text="Diyet ve Egzersiz Yüzdeleri", 
                    font=("Arial", 20, "bold")).pack(pady=10)

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Diyet için donut grafik
        fig1 = Figure(figsize=(4, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        data1 = [yuzde_diyet, 100 - yuzde_diyet]
        labels1 = [f"Yapıldı: {yuzde_diyet:.1f}%", f"Yapılmadı: {100 - yuzde_diyet:.1f}%"]
        ax1.pie(data1, labels=labels1, autopct="%1.1f%%", startangle=90, wedgeprops=dict(width=0.5))
        ax1.set_title("Diyet", fontsize=16)
        ax1.axis("equal")
        canvas1 = FigureCanvasTkAgg(fig1, master=panel_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side="left", expand=True, padx=10, pady=10)

        # Egzersiz için donut grafik
        fig2 = Figure(figsize=(4, 4), dpi=100)
        ax2 = fig2.add_subplot(111)
        data2 = [yuzde_egzersiz, 100 - yuzde_egzersiz]
        labels2 = [f"Yapıldı: {yuzde_egzersiz:.1f}%", f"Yapılmadı: {100 - yuzde_egzersiz:.1f}%"]
        ax2.pie(data2, labels=labels2, autopct="%1.1f%%", startangle=90, wedgeprops=dict(width=0.5))
        ax2.set_title("Egzersiz", fontsize=16)
        ax2.axis("equal")
        canvas2 = FigureCanvasTkAgg(fig2, master=panel_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side="right", expand=True, padx=10, pady=10)

        # Geri butonu
        ctk.CTkButton(panel_frame, text="← Geri", 
                    command=self.hasta_listesi_goster,
                    fg_color="#6c757d", hover_color="#545b62").pack(pady=10)           
    
    def tc_den_hasta_id_al(self, tc):
        """TC'den hasta ID'sini alır"""
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT KullaniciID FROM Kullanici WHERE TC = %s", (tc,))
            uid = cur.fetchone()[0]
            cur.execute("SELECT HastaID FROM Hasta WHERE KullaniciID = %s", (uid,))
            hasta_id = cur.fetchone()[0]
            conn.close()
            return hasta_id
        except Exception as e:
            messagebox.showerror("Hata", f"Hasta ID alınamadı: {e}")
            return None
    
    def analiz_grafigi_goster(self, hasta_id):
        """Analiz grafiği paneli içerisinde gösterilir"""
        # Eski Toplevel yerine içerik paneli kullanılacak:
        self.temizle_icerik()
        panel_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        panel_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    DATE(o.TarihSaat) AS gun,
                    AVG(o.SeviyeMgDl) AS ort_seker,
                    MAX(CASE WHEN d.Tip = 'diyet' THEN d.Tur ELSE NULL END) AS diyet_turu,
                    MAX(CASE WHEN d.Tip = 'egzersiz' THEN d.Tur ELSE NULL END) AS egzersiz_turu
                FROM Olcum o
                LEFT JOIN DiyetEgzersiz d ON DATE(o.TarihSaat) = d.Tarih AND o.HastaID = d.HastaID
                WHERE o.HastaID = %s AND o.Gecerli = TRUE
                GROUP BY DATE(o.TarihSaat)
                ORDER BY gun ASC
            """, (hasta_id,))
            veriler = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return
        
        if not veriler:
            ctk.CTkLabel(panel_frame, text="📊 Analiz verisi bulunamadı", 
                        font=("Arial", 16)).pack(expand=True)
            # Added Back button for no data case
            ctk.CTkButton(self.content_frame, text="← Geri", 
                          command=self.hasta_listesi_goster,
                          fg_color="#6c757d", hover_color="#545b62").pack(pady=10)
            return
        
        gunler = [row[0].strftime("%Y-%m-%d") for row in veriler]
        sekerler = [row[1] for row in veriler]
        diyetler = [row[2] or "—" for row in veriler]
        egzersizler = [row[3] or "—" for row in veriler]

        fig = Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(gunler, sekerler, marker='o', color='blue', label="Ortalama Şeker")
        for i, gun in enumerate(gunler):
            etik = f"D: {diyetler[i]}\nE: {egzersizler[i]}"
            ax.annotate(etik, (gunler[i], sekerler[i] + 2), fontsize=8, ha='center')
        ax.set_title("Günlük Şeker Seviyesi & Diyet/Egzersiz Etkisi")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("mg/dL")
        ax.grid(True)
        ax.legend()
        fig.autofmt_xdate()
        canvas = FigureCanvasTkAgg(fig, master=panel_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        # Added: Back button
        ctk.CTkButton(self.content_frame, text="← Geri", 
                      command=self.hasta_listesi_goster,
                      fg_color="#6c757d", hover_color="#545b62").pack(pady=10)
    
    def kural_panel_ac(self):
        """Kural tabanlı panel açar"""
        sel = self.hasta_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin.")
            return
        
        tc = self.hasta_tree.item(sel[0])["values"][0]
        hasta_id = self.tc_den_hasta_id_al(tc)
        if hasta_id:
            self.kural_tabanli_panel(hasta_id)
    
    def kural_tabanli_panel(self, hasta_id):
        """Kural tabanlı öneri paneli"""
        panel_win = ctk.CTkFrame(self.content_frame)
        panel_win.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("""
                SELECT SeviyeMgDl, TarihSaat FROM Olcum
                WHERE HastaID = %s ORDER BY OlcumID ASC LIMIT 1
            """, (hasta_id,))
            ilk_kayit = cur.fetchone()
            
            if ilk_kayit:
                # Mevcut kayıt varsa bilgileri göster
                self.mevcut_kayit_goster(panel_win, hasta_id, ilk_kayit, cur)
            else:
                # İlk kayıt formunu göster
                self.ilk_kayit_formu(panel_win, hasta_id)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Panel açılamadı: {e}")
            panel_win.destroy()
    
    def mevcut_kayit_goster(self, parent, hasta_id, ilk_kayit, cur):
        """Mevcut kayıt bilgilerini gösterir"""
        seviye, tarih = ilk_kayit
        
        # Belirti ve öneriler al
        cur.execute("SELECT Tip FROM Belirti WHERE HastaID = %s AND DATE(TarihSaat) = DATE(%s)", 
                   (hasta_id, tarih))
        belirtiler = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT Tip, Tur FROM DiyetEgzersiz WHERE HastaID = %s AND Tarih = %s", 
                   (hasta_id, tarih.date()))
        oneriler = cur.fetchall()
        
        cur.execute("SELECT SeviyeMgDl FROM Olcum WHERE HastaID = %s AND DATE(TarihSaat) = %s AND Gecerli = TRUE", 
                   (hasta_id, tarih.date()))
        olcumler = [row[0] for row in cur.fetchall()]
        
        # Bilgileri göster
        info_frame = ctk.CTkScrollableFrame(parent)
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(info_frame, text="Mevcut Kayıt Bilgileri", 
                    font=("Arial", 18, "bold")).pack(pady=10)
        
        ctk.CTkLabel(info_frame, text=f"Şeker Seviyesi: {seviye} mg/dL").pack(pady=5)
        ctk.CTkLabel(info_frame, text=f"Kayıt Tarihi: {tarih.strftime('%d.%m.%Y %H:%M')}").pack(pady=5)
        
        if belirtiler:
            ctk.CTkLabel(info_frame, text=f"Belirtiler: {', '.join(belirtiler)}").pack(pady=5)
        
        if oneriler:
            ctk.CTkLabel(info_frame, text="Öneriler:", font=("Arial", 14, "bold")).pack(pady=(10, 5))
            for tip, tur in oneriler:
                ctk.CTkLabel(info_frame, text=f"• {tip.capitalize()}: {tur}").pack(pady=2)
        
        if olcumler:
            ort = sum(olcumler) / len(olcumler)
            doz = self.insulin_dozu_hesapla(ort)
            ctk.CTkLabel(info_frame, text=f"Ortalama Şeker: {ort:.1f} mg/dL").pack(pady=5)
            ctk.CTkLabel(info_frame, text=f"İnsülin Önerisi: {doz}").pack(pady=5)
        
        # Tüm verileri sil butonu
        def tum_verileri_sil():
            if messagebox.askyesno("Emin misiniz?", "Bu hastaya ait TÜM veriler silinecek!"):
                try:
                    conn = baglanti_olustur()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM Olcum WHERE HastaID = %s", (hasta_id,))
                    cur.execute("DELETE FROM Belirti WHERE HastaID = %s", (hasta_id,))
                    cur.execute("DELETE FROM DiyetEgzersiz WHERE HastaID = %s", (hasta_id,))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Başarılı", "Tüm veriler silindi.")
                    parent.destroy()
                except Exception as e:
                    messagebox.showerror("Hata", f"Silme hatası: {e}")
        
        ctk.CTkButton(info_frame, text="Tüm Verileri Sil", 
                     fg_color="red", hover_color="darkred", 
                     command=tum_verileri_sil).pack(pady=20)
    
    def ilk_kayit_formu(self, parent, hasta_id):
        """İlk kayıt formu gösterir"""
        form_frame = ctk.CTkScrollableFrame(parent)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(form_frame, text="İlk Kayıt Formu", font=("Arial", 18, "bold")).pack(pady=10)
        
        # Tarih seçici
        ctk.CTkLabel(form_frame, text="Tarih:").pack(pady=(10, 2))
        tarih_secici = DateEntry(form_frame, date_pattern="yyyy-MM-dd")
        tarih_secici.pack(pady=5)
        
        # Saat
        ctk.CTkLabel(form_frame, text="Saat (HH:MM):").pack(pady=(10, 2))
        saat_entry = ctk.CTkEntry(form_frame, placeholder_text="Örn: 14:30")
        saat_entry.pack(pady=5)
        
        # Şeker seviyesi
        ctk.CTkLabel(form_frame, text="Kan Şekeri (mg/dL):").pack(pady=(10, 2))
        seker_entry = ctk.CTkEntry(form_frame, placeholder_text="Örn: 125")
        seker_entry.pack(pady=5)
        
        # Belirtiler
        ctk.CTkLabel(form_frame, text="Belirtiler (En fazla 3 adet):").pack(pady=(15, 5))
        
        belirtiler_listesi = [
            "nöropati", "polifaji", "yorgunluk", "kilo kaybı",
            "polidipsi", "bulanık görme", "yaraların yavaş iyileşmesi", "poliüri"
        ]
        
        belirti_vars = {}
        belirti_checkboxes = []
        
        def belirti_kontrol():
            aktif_sayi = sum(var.get() for var in belirti_vars.values())
            for belirti, var in belirti_vars.items():
                idx = belirtiler_listesi.index(belirti)
                checkbox = belirti_checkboxes[idx]
                if not var.get():
                    checkbox.configure(state="normal" if aktif_sayi < 3 else "disabled")
        
        for belirti in belirtiler_listesi:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(form_frame, text=belirti, variable=var, command=belirti_kontrol)
            cb.pack(anchor="w", padx=20, pady=2)
            belirti_vars[belirti] = var
            belirti_checkboxes.append(cb)
        
        def kaydet_ve_oner():
            try:
                # Validasyon kontrolü yapın (örneğin, maksimum 3 belirti)
                if sum(var.get() for var in belirti_vars.values()) > 3:
                    messagebox.showwarning("Uyarı", "En fazla 3 belirti seçebilirsiniz.")
                    return
                
                seviye = int(seker_entry.get())
                secilen_tarih = tarih_secici.get_date()
                secilen_saat = datetime.strptime(saat_entry.get().strip(), "%H:%M").time()
                kayit_zamani = datetime.combine(secilen_tarih, secilen_saat)
                
                conn = baglanti_olustur()
                cur = conn.cursor()
                
                # Ölçüm kaydet
                cur.execute("INSERT INTO Olcum (HastaID, TarihSaat, SeviyeMgDl) VALUES (%s, %s, %s)",
                            (hasta_id, kayit_zamani, seviye))
                
                # Belirtileri kaydet
                for belirti, var in belirti_vars.items():
                    if var.get():
                        cur.execute("INSERT INTO Belirti (HastaID, TarihSaat, Tip) VALUES (%s, %s, %s)",
                                    (hasta_id, kayit_zamani, belirti))
                
                conn.commit()
                conn.close()
                
                # Seçilen belirtileri liste olarak toplayın:
                secilen_belirtiler = [belirti for belirti, var in belirti_vars.items() if var.get()]
                # kural_tabanli_oneri ile öneriyi hesaplayın:
                oneri = kural_tabanli_oneri(seviye, secilen_belirtiler)
                
                # Diyet veya egzersiz önerisi olarak (örneğin "diyet"), veritabanına aktarın:
                oneriyi_veritabani_aktar(hasta_id, kayit_zamani.date(), "diyet", oneri)
                # Eğer egzersiz için de otomatik öneri oluşturuluyorsa, "egzersiz" tipinde de INSERT yapılabilir.
                
                messagebox.showinfo("Başarılı", "İlk kayıt başarıyla yapıldı ve öneri veritabanına aktarıldı.")
                parent.destroy()
                
            except Exception as e:
                    messagebox.showerror("Hata", f"Kayıt başarısız: {e}")
        
        ctk.CTkButton(form_frame, text="Kaydet ve Öner", command=kaydet_ve_oner,
                     width=200, height=40).pack(pady=30)
    
    def insulin_dozu_hesapla(self, ortalama):
        """İnsülin dozunu hesaplar"""
        if ortalama < 70:
            return "Yok (Hipoglisemi)"
        elif ortalama <= 110:
            return "Yok (Normal)"
        elif ortalama <= 150:
            return "1 ml (Orta Yüksek)"
        elif ortalama <= 200:
            return "2 ml (Yüksek)"
        else:
            return "3 ml (Çok Yüksek)"
    
    def hasta_sil(self):
        """Seçili hastayı siler"""
        sel = self.hasta_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin.")
            return
        
        tc = self.hasta_tree.item(sel[0])["values"][0]
        ad_soyad = f"{self.hasta_tree.item(sel[0])['values'][1]} {self.hasta_tree.item(sel[0])['values'][2]}"
        
        if not messagebox.askyesno("Emin misiniz?", f"{ad_soyad} ({tc}) silinecek.\nBu işlem geri alınamaz!"):
            return
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            
            # Kullanıcı ID al
            cur.execute("SELECT KullaniciID FROM Kullanici WHERE TC = %s", (tc,))
            uid = cur.fetchone()[0]
            
            # Hasta ve kullanıcı sil
            cur.execute("DELETE FROM Hasta WHERE KullaniciID = %s", (uid,))
            cur.execute("DELETE FROM Kullanici WHERE KullaniciID = %s", (uid,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Başarılı", "Hasta başarıyla silindi.")
            self.hasta_listesi_yukle()  # Listeyi güncelle
            
        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatası: {e}")
    
    def profil_ayarlari_goster(self):
        """Profil ayarları panelini gösterir"""
        self.temizle_icerik()
        
        ctk.CTkLabel(self.content_frame, text="Profil Ayarları", 
                    font=("Arial", 20, "bold")).pack(pady=20)
        
        # Profil fotoğrafı bölümü
        foto_frame = ctk.CTkFrame(self.content_frame)
        foto_frame.pack(pady=20, padx=50, fill="x")
        
        ctk.CTkLabel(foto_frame, text="Profil Fotoğrafı", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.buyuk_profil_label = ctk.CTkLabel(foto_frame, text="")
        self.buyuk_profil_label.pack(pady=10)
        
        # Butonlar
        button_frame = ctk.CTkFrame(foto_frame)
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text="Fotoğraf Yükle", 
                     command=self.profil_foto_yukle_secim).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Fotoğrafı Sil", 
                     fg_color="red", hover_color="darkred",
                     command=self.profil_foto_sil).pack(side="left", padx=10)
        
        # Büyük profil fotoğrafını yükle
        self.buyuk_profil_foto_yukle()
    
    def profil_foto_yukle(self) -> None:
        """Profil fotoğrafını yükler (küçük widget için)"""
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT ProfilResim FROM Kullanici WHERE KullaniciID = %s", (self.kullanici_id,))
            sonuc = cur.fetchone()
            # self.header_profile_label kullanılarak güncellenecek
            foto = self._get_image(sonuc[0] if sonuc and sonuc[0] else None, (80, 80))
            if foto:
                self.header_profile_label.configure(image=foto, text="")  # header widget güncellendi
                self.header_profile_label.image = foto
            conn.close()
        except Exception as e:
            print(f"Profil fotoğrafı yüklenemedi: {e}")
    
    def buyuk_profil_foto_yukle(self) -> None:
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT ProfilResim FROM Kullanici WHERE KullaniciID = %s", (self.kullanici_id,))
            sonuc = cur.fetchone()
            foto = self._get_image(sonuc[0] if sonuc and sonuc[0] else None, (200, 200))
            if foto:
                self.buyuk_profil_label.configure(image=foto, text="")
                self.buyuk_profil_label.image = foto
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Profil fotoğrafı yüklenemedi: {e}")
    
    def profil_foto_yukle_secim(self):
        """Profil fotoğrafı seçme ve yükleme"""
        dosya = filedialog.askopenfilename(
            title="Profil Fotoğrafı Seç",
            filetypes=[("Görsel Dosyalar", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if not dosya:
            return
        
        try:
            with open(dosya, "rb") as f:
                img_binary = f.read()
            
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("UPDATE Kullanici SET ProfilResim = %s WHERE KullaniciID = %s",
                        (img_binary, self.kullanici_id))
            conn.commit()
            conn.close()
            # Güncelleme: header widget'i kullanılıyor
            self.profil_foto_yukle()
            self.buyuk_profil_foto_yukle()
            messagebox.showinfo("Başarılı", "Profil fotoğrafı güncellendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Fotoğraf yüklenemedi: {e}")
    
    def profil_foto_sil(self):
        """Profil fotoğrafını siler"""
        if not messagebox.askyesno("Emin misiniz?", "Profil fotoğrafınız silinecek."):
            return
        
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("UPDATE Kullanici SET ProfilResim = NULL WHERE KullaniciID = %s",
                       (self.kullanici_id,))
            conn.commit()
            conn.close()
            
            # Fotoğrafları güncelle (varsayılan fotoğraf gösterilir)
            self.profil_foto_yukle()
            self.buyuk_profil_foto_yukle()
            
            messagebox.showinfo("Başarılı", "Profil fotoğrafı silindi.")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Fotoğraf silinemedi: {e}")
    
    def gecmis_filtreleme_goster(self):
        """Tüm hastaların geçmiş verilerini ve filtreleme seçeneklerini gösterir."""
        self.temizle_icerik()
        ctk.CTkLabel(self.content_frame, text="Hastalar – Geçmiş & Filtreleme", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Filter panel
        filter_frame = ctk.CTkFrame(self.content_frame)
        filter_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(filter_frame, text="Min Şeker:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        self.filter_min_entry = ctk.CTkEntry(filter_frame, width=80)
        self.filter_min_entry.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(filter_frame, text="Max Şeker:", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5)
        self.filter_max_entry = ctk.CTkEntry(filter_frame, width=80)
        self.filter_max_entry.grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkLabel(filter_frame, text="Belirti:", font=("Arial", 12)).grid(row=0, column=4, padx=5, pady=5)
        # Change: use dropdown for belirti selections instead of entry.
        self.filter_belirti_var = ctk.StringVar(value="Tümü")
        self.filter_belirti_menu = ctk.CTkOptionMenu(filter_frame, variable=self.filter_belirti_var, 
                                                      values=["Tümü", "nöropati", "polifaji", "yorgunluk", 
                                                              "kilo kaybı", "polidipsi", "bulanık görme", 
                                                              "yaraların yavaş iyileşmesi", "poliüri"], width=100)
        self.filter_belirti_menu.grid(row=0, column=5, padx=5, pady=5)
        ctk.CTkButton(filter_frame, text="Filtrele", command=self.filtrele_hastalar).grid(row=0, column=6, padx=5, pady=5)
        
        # Treeview for filtered patients
        table_frame = ctk.CTkFrame(self.content_frame)
        table_frame.pack(pady=10, padx=20, fill="both", expand=True)
        cols = ("TC", "Ad", "Soyad", "Email", "Ortalama Şeker")
        self.filtered_tree = Treeview(table_frame, columns=cols, show="headings", height=10)
        for c in cols:
            self.filtered_tree.heading(c, text=c)
            self.filtered_tree.column(c, width=120, anchor="center")
        self.filtered_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Button to view patient history (geçmiş)
        ctk.CTkButton(self.content_frame, text="Geçmişi İncele", command=self.hasta_gecmisi_goster,
                      width=200, height=40, font=("Arial", 12)).pack(pady=10)
    
    def filtrele_hastalar(self):
        """Filtreleme kriterlerine göre tüm hastaları listeler."""
        min_seker = self.filter_min_entry.get().strip()
        max_seker = self.filter_max_entry.get().strip()
        # Use the dropdown value for belirti; if "Tümü" selected, then no belirti filter is applied.
        belirti = self.filter_belirti_var.get().strip().lower()
        if belirti == "tümü":
            belirti = ""
        for item in self.filtered_tree.get_children():
            self.filtered_tree.delete(item)
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            # Basit bir filtre sorgusu: Hastanın ortalama kan şekeri
            query = """
                SELECT k.TC, k.Ad, k.Soyad, k.Email, AVG(o.SeviyeMgDl)
                FROM Hasta h 
                JOIN Kullanici k ON k.KullaniciID = h.KullaniciID
                LEFT JOIN Olcum o ON h.HastaID = o.HastaID
                GROUP BY k.KullaniciID
            """
            cur.execute(query)
            for row in cur.fetchall():
                ort_seker = row[4] if row[4] is not None else 0
                if min_seker and ort_seker < float(min_seker):
                    continue
                if max_seker and ort_seker > float(max_seker):
                    continue
                # If a specific belirti was selected, check it.
                if belirti:
                    cur.execute("SELECT COUNT(*) FROM Belirti WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = (SELECT KullaniciID FROM Kullanici WHERE TC = %s)) AND LOWER(Tip) = %s", (row[0], belirti))
                    if cur.fetchone()[0] == 0:
                        continue
                self.filtered_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], f"{ort_seker:.1f}"))
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Filtreleme hatası: {e}")
    
    def hasta_gecmisi_goster(self):
        """Seçilen hastanın geçmiş verilerini gösterir."""
        sel = self.filtered_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Önce bir hasta seçin.")
            return
        tc = self.filtered_tree.item(sel[0])["values"][0]
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            # Tüm geçmiş ölçümleri al
            cur.execute("""
                SELECT DATE(TarihSaat), SeviyeMgDl
                FROM Olcum
                WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = (SELECT KullaniciID FROM Kullanici WHERE TC = %s))
                ORDER BY TarihSaat ASC
            """, (tc,))
            veriler = cur.fetchall()
            # Fetch latest ölçüm bilgisi
            cur.execute("""
                SELECT SeviyeMgDl, TarihSaat
                FROM Olcum
                WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = (SELECT KullaniciID FROM Kullanici WHERE TC = %s))
                ORDER BY TarihSaat DESC LIMIT 1
            """, (tc,))
            latest = cur.fetchone()
            if latest:
                latest_seviye, latest_tarih = latest
                cur.execute("""
                    SELECT Tip FROM Belirti 
                    WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = (SELECT KullaniciID FROM Kullanici WHERE TC = %s))
                    AND DATE(TarihSaat) = DATE(%s)
                """, (tc, latest_tarih))
                belirtiler = [row[0] for row in cur.fetchall()]
            else:
                latest_seviye, latest_tarih, belirtiler = None, None, []
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Geçmiş verileri alınamadı: {e}")
            return
        
        if not veriler:
            messagebox.showinfo("Bilgi", "Geçmiş verisi bulunamadı.")
            return
        
        # Removed Toplevel; now display in content_frame:
        self.temizle_icerik()
        main_frame = ctk.CTkFrame(self.content_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        right_frame = ctk.CTkFrame(main_frame, width=300)
        right_frame.pack(side="right", fill="y", padx=5, pady=5)
        right_frame.pack_propagate(False)
        
        # Graph: Zaman içerisinde şeker değişimi
        gunler = [row[0] for row in veriler]
        sekerler = [row[1] for row in veriler]
        fig = Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(gunler, sekerler, marker='o', color='green', label="Şeker Seviyesi")
        ax.set_title("Geçmiş Kan Şekeri Değerleri")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("mg/dL")
        ax.grid(True)
        ax.legend()
        fig.autofmt_xdate()
        canvas = FigureCanvasTkAgg(fig, master=left_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Right panel: Son ölçüm, belirtiler, ve öneri
        if latest_seviye is not None:
            ctk.CTkLabel(right_frame, text="Son Ölçüm", font=("Arial", 16, "bold")).pack(pady=10)
            ctk.CTkLabel(right_frame, text=f"Şeker: {latest_seviye} mg/dL", font=("Arial", 14)).pack(pady=5)
            ctk.CTkLabel(right_frame, text=f"Tarih: {latest_tarih.strftime('%d.%m.%Y %H:%M')}", font=("Arial", 12)).pack(pady=5)
            ctk.CTkLabel(right_frame, text="Belirtiler:", font=("Arial", 14, "bold")).pack(pady=10)
            if belirtiler:
                for b in belirtiler:
                    ctk.CTkLabel(right_frame, text=f"• {b}", font=("Arial", 12)).pack(anchor="w", padx=10)
            else:
                ctk.CTkLabel(right_frame, text="Belirti yok", font=("Arial", 12)).pack(pady=5)
            oneri = kural_tabanli_oneri(latest_seviye, belirtiler)
            ctk.CTkLabel(right_frame, text="Öneri:", font=("Arial", 14, "bold")).pack(pady=10)
            ctk.CTkLabel(right_frame, text=oneri, font=("Arial", 12), wraplength=280, justify="left").pack(pady=5)
        else:
            ctk.CTkLabel(right_frame, text="Ölçüm verisi bulunamadı.", font=("Arial", 14)).pack(pady=10)
        
        # Eklenen: Geri butonu - Geçmiş & Filtreleme ana ekranına dön
        ctk.CTkButton(self.content_frame, text="← Geri", 
                      command=self.gecmis_filtreleme_goster,
                      fg_color="#6c757d", hover_color="#545b62").pack(pady=10)
    
    def calistir(self):
        """Ana döngüyü başlatır"""
        self.root.mainloop()
    
    def uygulama_yuzdeleri_goster(self):
        """Doktora ait hastaların diyet ve egzersiz uygulama yüzdelerini hesaplar ve listeler."""
        self.temizle_icerik()
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("""
                SELECT k.KullaniciID, k.TC, k.Ad, k.Soyad 
                FROM Hasta h 
                JOIN Kullanici k ON k.KullaniciID = h.KullaniciID 
                WHERE h.DoktorID = %s
            """, (self.doktor_id,))
            hastalar = cur.fetchall()
            sonuc = []
            for hasta in hastalar:
                kullanici_id, tc, ad, soyad = hasta
                # Diyet hesaplaması
                cur.execute("""
                    SELECT COUNT(*) FROM DiyetEgzersiz 
                    WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = %s) 
                    AND Tip = 'diyet'
                """, (kullanici_id,))
                toplam_diyet = cur.fetchone()[0]
                cur.execute("""
                    SELECT COUNT(*) FROM DiyetEgzersiz 
                    WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = %s) 
                    AND Tip = 'diyet' AND Durum = 'yapıldı'
                """, (kullanici_id,))
                yapilan_diyet = cur.fetchone()[0]
                yuzde_diyet = (yapilan_diyet / toplam_diyet * 100) if toplam_diyet > 0 else 0
                # Egzersiz hesaplaması
                cur.execute("""
                    SELECT COUNT(*) FROM DiyetEgzersiz 
                    WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = %s) 
                    AND Tip = 'egzersiz'
                """, (kullanici_id,))
                toplam_egzersiz = cur.fetchone()[0]
                cur.execute("""
                    SELECT COUNT(*) FROM DiyetEgzersiz 
                    WHERE HastaID = (SELECT HastaID FROM Hasta WHERE KullaniciID = %s) 
                    AND Tip = 'egzersiz' AND Durum = 'yapıldı'
                """, (kullanici_id,))
                yapilan_egzersiz = cur.fetchone()[0]
                yuzde_egzersiz = (yapilan_egzersiz / toplam_egzersiz * 100) if toplam_egzersiz > 0 else 0
                sonuc.append((tc, ad, soyad, yuzde_diyet, yuzde_egzersiz))
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Yüzdelik hesaplaması hatası: {e}")
            return
        
        baslik = ctk.CTkLabel(self.content_frame, text="Uygulama Yüzdeleri", font=("Arial", 24, "bold"))
        baslik.pack(pady=20)
        liste_frame = ctk.CTkFrame(self.content_frame)
        liste_frame.pack(fill="both", expand=True, padx=20, pady=20)
        tree = Treeview(liste_frame, columns=("TC", "Ad", "Soyad", "Diyet %", "Egzersiz %"), show="headings", height=15)
        for col in ("TC", "Ad", "Soyad", "Diyet %", "Egzersiz %"):
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        for row in sonuc:
            tc, ad, soyad, dy, ey = row

            # Eğer ikisi de %50'nin altında ise kırmızı
            if dy < 50 and ey < 50:
                renk_tag = "kirmizi"
            else:
                renk_tag = "turuncu"

            tree.insert("", "end", values=(tc, ad, soyad, f"{dy:.1f}%", f"{ey:.1f}%"), tags=(renk_tag,))

        # Renk etiketlerini tanımla
        tree.tag_configure("kirmizi", background="#f8d7da", foreground="black")   # Açık kırmızı
        tree.tag_configure("turuncu", background="#fff3cd", foreground="black")   # Açık turuncu


# Ana fonksiyon
def doktor_paneli(kullanici_id):
    """Doktor panelini başlatır"""
    panel = DoktorPanel(kullanici_id)
    panel.calistir()

# --- New: kural_tabanli_oneri fonksiyonu ---
def kural_tabanli_oneri(seviye, belirtiler):
	"""Belirtilen seviye ve belirtilere göre öneri üretir."""
	if seviye is None or not belirtiler:
		return "⚠ Gerekli veriler eksik."
	b = set(t.lower() for t in belirtiler)
	if seviye >= 180:
		if {"yaraların yavaş iyileşmesi", "polifaji", "polidipsi"}.issubset(b):
			return "Şekersiz Diyet önerilir. Klinik Egzersiz yapılmalı."
		elif {"yaraların yavaş iyileşmesi", "kilo kaybı"}.issubset(b):
			return "Şekersiz Diyet önerilir. Yürüyüş yapılmalı."
	elif 110 < seviye < 180:
		if {"bulanık görme", "nöropati", "yorgunluk"}.issubset(b):
			return "Az Şekerli Diyet önerilir. Yürüyüş yapılmalı."
		elif {"poliüri", "polidipsi"}.issubset(b):
			return "Şekersiz Diyet önerilir. Klinik Egzersiz yapılmalı."
		elif {"bulanık görme", "nöropati"}.issubset(b):
			return "Az Şekerli Diyet önerilir. Klinik Egzersiz yapılmalı."
	elif 70 <= seviye <= 110:
		if {"yorgunluk", "kilo kaybı"}.issubset(b):
			return "Az Şekerli Diyet önerilir. Yürüyüş yapılmalı."
		elif {"polifaji", "polidipsi"}.issubset(b):
			return "Dengeli Beslenme önerilir. Yürüyüş yapılmalı."
	elif seviye < 70:
		if {"nöropati", "polifaji", "yorgunluk"}.issubset(b):
			return "Dengeli Beslenme önerilir. Egzersiz yapılmamalı."
	return "⚠ Bu belirtiler ve seviye için öneri bulunamadı."

def oneriyi_veritabani_aktar(hasta_id, kayit_tarihi, tip, oneri_metni, durum="otomatik"):
    """
    Üretilen öneri metnini DiyetEgzersiz tablosuna aktarır.
    Parametreler:
      - hasta_id: İlgili hasta kimliği
      - kayit_tarihi: Önerinin geçerli olduğu tarih (örn. kaydın yapıldığı tarih)
      - tip: 'diyet' veya 'egzersiz'
      - oneri_metni: kural_tabanli_oneri fonksiyonundan dönen öneri metni
      - durum: Genellikle 'otomatik' olarak kaydedilir
    """
    try:
        conn = baglanti_olustur()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO DiyetEgzersiz (HastaID, Tarih, Tip, Durum, Tur) VALUES (%s, %s, %s, %s, %s)",
            (hasta_id, kayit_tarihi, tip, durum, oneri_metni)
        )
        conn.commit()
        conn.close()
        print("Öneri veritabanına aktarıldı.")
    except Exception as e:
        messagebox.showerror("Hata", f"Öneri eklenemedi:\n{e}")

