import customtkinter as ctk
from tkinter import messagebox, ttk
from veritabani import baglanti_olustur
from datetime import datetime, date, time
from tkcalendar import DateEntry
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import io
from tkinter import filedialog
from PIL import Image
from customtkinter import CTkImage

def hasta_paneli(kullanici_id):
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    # Yardımcı fonksiyonlar
    def donemi_belirle(zaman_obj: datetime) -> str:
        t = zaman_obj.time()
        if time(7, 0) <= t < time(9, 0):
            return "sabah"
        elif time(12, 0) <= t < time(13, 30):
            return "öğlen"
        elif time(15, 0) <= t < time(16, 30):
            return "ikindi"
        elif time(18, 0) <= t < time(19, 30):
            return "akşam"
        elif time(22, 0) <= t < time(23, 59):
            return "gece"
        else:
            return "geçersiz"

    def olcum_gecerli_mi(kayit_zamani: datetime) -> bool:
        donem_araliklari = {
            "sabah":  (time(7, 0),  time(8, 0)),
            "öğlen":  (time(12, 0), time(13, 0)),
            "ikindi": (time(15, 0), time(16, 0)),
            "akşam":  (time(18, 0), time(19, 0)),
            "gece":   (time(22, 0), time(23, 0)),
        }
        donem = donemi_belirle(kayit_zamani)
        if donem not in donem_araliklari:
            return False
        baslangic, bitis = donem_araliklari[donem]
        saat = kayit_zamani.time()
        return baslangic <= saat <= bitis

    def sabah_olcumu_var_mi(conn, hasta_id, tarih):
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM Olcum
            WHERE HastaID = %s
            AND DATE(TarihSaat) = %s
            AND TIME(TarihSaat) BETWEEN '07:00:00' AND '08:00:00'
        """, (hasta_id, tarih))
        return cur.fetchone()[0] > 0
    

    # Hasta bilgilerini al
    conn = baglanti_olustur()
    hasta_id = None
    adsoyad = ""
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT h.HastaID, k.Ad, k.Soyad
                FROM Hasta h
                JOIN Kullanici k ON k.KullaniciID = h.KullaniciID
                WHERE k.KullaniciID = %s
            """, (kullanici_id,))
            row = cur.fetchone()
            if row:
                hasta_id, ad, soyad = row
                adsoyad = f"{ad} {soyad}"
        finally:
            conn.close()

    if not hasta_id:
        messagebox.showerror("Hata", "Hasta bilgisi bulunamadı.")
        return

    # Ana pencere
    root = ctk.CTk()
    root.title("Hasta Paneli - Diyabet Takip Sistemi")
    root.geometry("1200x800")
    root.configure(fg_color="#f0f0f0")

    # Header Frame
    header_frame = ctk.CTkFrame(root, height=100, fg_color="#2b5ce6", corner_radius=0)
    header_frame.pack(fill="x", padx=0, pady=0)
    header_frame.pack_propagate(False)

    # Profil fotoğrafı için placeholder
    profile_frame = ctk.CTkFrame(header_frame, width=80, height=80, fg_color="white")
    profile_frame.place(x=20, y=10)
    
    profile_img_label = ctk.CTkLabel(profile_frame, text="👤", font=("Arial", 30))
    profile_img_label.pack(expand=True)

    # Kullanıcı bilgileri
    user_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    user_info_frame.place(x=120, y=15)
    
    ctk.CTkLabel(user_info_frame, text=f"Hoşgeldiniz, {adsoyad}", 
                font=("Arial", 24, "bold"), text_color="white").pack(anchor="w")
    ctk.CTkLabel(user_info_frame, text="Hasta Paneli", 
                font=("Arial", 14), text_color="#cccccc").pack(anchor="w")

    # Profil düzenleme butonu
    profile_btn = ctk.CTkButton(header_frame, text="Profil Fotoğrafı", width=120, height=30,
                               fg_color="#1e4cc9", hover_color="#164a9e")
    profile_btn.place(x=1050, y=35)

    # Ana içerik frame'i
    main_frame = ctk.CTkFrame(root, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    # Yeni: active_panel değişkeni tanımlandı, sağ alandaki geçici paneller bu değişkende tutulacak.
    active_panel = None

    # Sol panel - Eylemler
    left_panel = ctk.CTkFrame(main_frame, width=400, fg_color="white", corner_radius=15)
    left_panel.pack(side="left", fill="y", padx=(0, 10))
    left_panel.pack_propagate(False)

    # Sol panel başlık
    ctk.CTkLabel(left_panel, text="📝 Hızlı İşlemler", font=("Arial", 20, "bold"),
                text_color="#2b5ce6").pack(pady=(20, 10))

    # Ölçüm ekleme formu
    olcum_frame = ctk.CTkFrame(left_panel, fg_color="#f8f9fa", corner_radius=10)
    olcum_frame.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(olcum_frame, text="🩸 Kan Şekeri Ölçümü", 
                font=("Arial", 16, "bold"), text_color="#333").pack(pady=(15, 5))

    # Tarih girişi
    date_frame = ctk.CTkFrame(olcum_frame, fg_color="transparent")
    date_frame.pack(fill="x", padx=15, pady=5)
    ctk.CTkLabel(date_frame, text="Tarih:", font=("Arial", 12)).pack(anchor="w")
    tarih_entry = DateEntry(date_frame, date_pattern="dd-MM-yyyy", width=12)
    tarih_entry.pack(fill="x", pady=2)

    # Saat girişi
    time_frame = ctk.CTkFrame(olcum_frame, fg_color="transparent")
    time_frame.pack(fill="x", padx=15, pady=5)
    ctk.CTkLabel(time_frame, text="Saat (HH:MM):", font=("Arial", 12)).pack(anchor="w")
    saat_entry = ctk.CTkEntry(time_frame, placeholder_text="Örn: 14:30")
    saat_entry.pack(fill="x", pady=2)

    # Ölçüm değeri girişi
    value_frame = ctk.CTkFrame(olcum_frame, fg_color="transparent")
    value_frame.pack(fill="x", padx=15, pady=5)
    ctk.CTkLabel(value_frame, text="Ölçüm (mg/dL):", font=("Arial", 12)).pack(anchor="w")
    deger_entry = ctk.CTkEntry(value_frame, placeholder_text="Örn: 110")
    deger_entry.pack(fill="x", pady=2)

    def olcum_kaydet():
        # Kontrol: Sabah ölçümü var mı?
        try:
            conn_check = baglanti_olustur()
            cur_check = conn_check.cursor()
            cur_check.execute("""
                SELECT COUNT(*) FROM Olcum
                WHERE HastaID = %s
                AND TIME(TarihSaat) BETWEEN '07:00:00' AND '08:00:00'
            """, (hasta_id,))
            sabah_var = cur_check.fetchone()[0] > 0
            if not sabah_var:
                messagebox.showwarning("Uyarı", "Önce doktora muayene olmalısınız.")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Kontrol hatası:\n{e}")
            return
        finally:
            if conn_check:
                conn_check.close()

        # Tarih ve saat kontrolü
        try:
            secilen_tarih = tarih_entry.get_date()
            secilen_saat = datetime.strptime(saat_entry.get().strip(), "%H:%M").time()
            kayit_zamani = datetime.combine(secilen_tarih, secilen_saat)
            donem = donemi_belirle(kayit_zamani)

            if donem == "sabah":
                conn_check = baglanti_olustur()
                if sabah_olcumu_var_mi(conn_check, hasta_id, kayit_zamani.date()):
                    conn_check.close()
                    messagebox.showwarning("Geçersiz İşlem", 
                                         "Bu güne ait sabah ölçümü zaten girilmiş.")
                    return
                conn_check.close()
        except Exception:
            messagebox.showerror("Hata", "Lütfen geçerli tarih ve saat girin.")
            return

        # Değer kontrolü
        try:
            val = int(deger_entry.get())
            gecerli = olcum_gecerli_mi(kayit_zamani)
            
            if not gecerli:
                messagebox.showwarning("Geç Giriş", 
                                     "Bu saat seçilen döneme uygun değil.")
            if val < 0 or val > 500:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "0–500 arası geçerli bir sayı girin.")
            return

        # Veritabanına kaydet
        try:
            conn2 = baglanti_olustur()
            cur2 = conn2.cursor()
            cur2.execute(
                "INSERT INTO Olcum (HastaID, TarihSaat, SeviyeMgDl, Gecerli) VALUES (%s, %s, %s, %s)",
                (hasta_id, kayit_zamani, val, gecerli)
            )
            conn2.commit()
            messagebox.showinfo("Başarılı", "Ölçüm kaydedildi!")
            
            # Formu temizle
            saat_entry.delete(0, "end")
            deger_entry.delete(0, "end")
            
            # Grafikleri güncelle
            grafik_guncelle()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası:\n{e}")
        finally:
            if conn2:
                conn2.close()

    ctk.CTkButton(olcum_frame, text="Ölçümü Kaydet", command=olcum_kaydet,
                 fg_color="#28a745", hover_color="#218838").pack(pady=15)

    # Diyet ve Egzersiz takip frame'i
    lifestyle_frame = ctk.CTkFrame(left_panel, fg_color="#f8f9fa", corner_radius=10)
    lifestyle_frame.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(lifestyle_frame, text="🥗 Günlük Takip", 
                font=("Arial", 16, "bold"), text_color="#333").pack(pady=(15, 5))

    def diyet_egzersiz_kaydet(tip):
        nonlocal active_panel  # Yeni eklenen aktif panel değişkeni
        # Kontrol
        try:
            conn_check = baglanti_olustur()
            cur_check = conn_check.cursor()
            cur_check.execute("""
                SELECT COUNT(*) FROM Olcum
                WHERE HastaID = %s
                AND TIME(TarihSaat) BETWEEN '07:00:00' AND '08:00:00'
            """, (hasta_id,))
            sabah_olcum_var = cur_check.fetchone()[0] > 0
            if not sabah_olcum_var:
                messagebox.showwarning("Uyarı", "Önce doktora muayene olmalısınız.")
                return
        except Exception as e:
            messagebox.showerror("Hata", f"Kontrol hatası:\n{e}")
            return
        finally:
            conn_check.close()

        # Eğer daha önce bir panel açıldıysa sil
        if active_panel is not None:
            active_panel.destroy()
    
        right_panel.pack_forget()  # Eski içerik alanını gizle
        kayit_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
        kayit_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        active_panel = kayit_frame

        header = ctk.CTkFrame(kayit_frame, height=60, fg_color="#2b5ce6")
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"📊 {tip.capitalize()} Takibi", font=("Arial",18,"bold"), text_color="white").pack(expand=True)

        content = ctk.CTkFrame(kayit_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Durum seçimi
        ctk.CTkLabel(content, text=f"{tip.capitalize()} Durumu:", 
                    font=("Arial", 14, "bold")).pack(pady=(10, 5))
        
        durum_var = ctk.StringVar(value="yapıldı")
        durum_frame = ctk.CTkFrame(content, fg_color="#f8f9fa")
        durum_frame.pack(fill="x", pady=5)
        
        rb_yapildi = ctk.CTkRadioButton(durum_frame, text="✅ Yapıldı", 
                                       variable=durum_var, value="yapıldı")
        rb_yapilmadi = ctk.CTkRadioButton(durum_frame, text="❌ Yapılmadı", 
                                         variable=durum_var, value="yapılmadı")
        rb_yapildi.pack(pady=10, padx=20)
        rb_yapilmadi.pack(pady=10, padx=20)

        # Tür seçimi
        tur_secenekleri = (["Az Şekerli", "Şekersiz", "Dengeli"] if tip=="diyet" 
                          else ["Yürüyüş", "Bisiklet", "Klinik Egzersiz"])
        
        ctk.CTkLabel(content, text=f"{tip.capitalize()} Türü:", 
                    font=("Arial", 14, "bold")).pack(pady=(15, 5))
        tur_var = ctk.StringVar(value=tur_secenekleri[0])
        tur_menu = ctk.CTkOptionMenu(content, variable=tur_var, values=tur_secenekleri)
        tur_menu.pack(pady=5, fill="x")

        def durum_degisti():
            if durum_var.get() == "yapıldı":
                tur_menu.pack(pady=5, fill="x")
            else:
                tur_menu.pack_forget()

        rb_yapildi.configure(command=durum_degisti)
        rb_yapilmadi.configure(command=durum_degisti)

        def kaydet_de():
            nonlocal active_panel
            durum = durum_var.get()
            tur = tur_var.get() if durum=="yapıldı" else None
            try:
                conn2 = baglanti_olustur()
                cur2 = conn2.cursor()
                cur2.execute(
                    "INSERT INTO DiyetEgzersiz (HastaID, Tarih, Tip, Durum, Tur) VALUES (%s, %s, %s, %s, %s)",
                    (hasta_id, date.today(), tip, durum, tur)
                )
                conn2.commit()
                message = f"{tip.capitalize()} kaydedildi: {durum}"
                if tur:
                    message += f" ({tur})"
                messagebox.showinfo("Başarılı", message)
                active_panel.destroy()
                active_panel = None
                right_panel.pack(side="right", fill="both", expand=True)
            except Exception as e:
                messagebox.showerror("Hata", f"Kayıt hatası:\n{e}")
            finally:
                if conn2:
                    conn2.close()

        ctk.CTkButton(content, text="💾 Kaydet", command=kaydet_de,
                     fg_color="#28a745", hover_color="#218838").pack(pady=20, fill="x")
        # Geri butonu: aktif panel silinip varsayılan sağ paneli yeniden göster
        ctk.CTkButton(content, text="← Geri", 
                  command=lambda: (active_panel.destroy(), setattr(__import__('__main__'), 'active_panel', None), right_panel.pack(side="right", fill="both", expand=True)),
                  fg_color="#6c757d", hover_color="#545b62").pack(pady=10, fill="x")

    # Diyet ve egzersiz butonları
    btn_frame = ctk.CTkFrame(lifestyle_frame, fg_color="transparent")
    btn_frame.pack(fill="x", padx=15, pady=10)

    ctk.CTkButton(btn_frame, text="🥗 Diyet Takibi", 
                 command=lambda: diyet_egzersiz_kaydet("diyet"),
                 fg_color="#17a2b8", hover_color="#138496").pack(fill="x", pady=2)
    
    ctk.CTkButton(btn_frame, text="🏃 Egzersiz Takibi", 
                 command=lambda: diyet_egzersiz_kaydet("egzersiz"),
                 fg_color="#ffc107", hover_color="#e0a800", text_color="black").pack(fill="x", pady=2)

    # Sağ panel - Veriler ve Grafikler
    right_panel = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
    right_panel.pack(side="right", fill="both", expand=True)

    # Sağ panel başlık
    ctk.CTkLabel(right_panel, text="📊 Verilerim", font=("Arial", 20, "bold"),
                text_color="#2b5ce6").pack(pady=(20, 10))

    # Notebook (Tab sistemi)
    notebook_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
    notebook_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Tab butonları
    tab_frame = ctk.CTkFrame(notebook_frame, height=50, fg_color="#f8f9fa")
    tab_frame.pack(fill="x", pady=(0, 10))
    tab_frame.pack_propagate(False)

    # Tab içerikleri için frame
    content_frame = ctk.CTkFrame(notebook_frame, fg_color="white")
    content_frame.pack(fill="both", expand=True)

    # Aktif tab
    aktif_tab = ctk.StringVar(value="grafik")

    # Tab içerikleri
    def tab_goster(tab_name):
        aktif_tab.set(tab_name)
        # Tüm çocukları temizle
        for widget in content_frame.winfo_children():
            widget.destroy()
            
        if tab_name == "grafik":
            grafik_goster()
        elif tab_name == "gecmis":
            gecmis_goster()

    # Tab butonları
    ctk.CTkButton(tab_frame, text="📈 Grafik", command=lambda: tab_goster("grafik"),
                 fg_color="#2b5ce6" if aktif_tab.get() == "grafik" else "#6c757d").pack(side="left", padx=5, pady=5)
    
    ctk.CTkButton(tab_frame, text="📋 Geçmiş", command=lambda: tab_goster("gecmis"),
                 fg_color="#2b5ce6" if aktif_tab.get() == "gecmis" else "#6c757d").pack(side="left", padx=5, pady=5)

    def grafik_goster():
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute(
                "SELECT TarihSaat, SeviyeMgDl FROM Olcum WHERE HastaID = %s ORDER BY TarihSaat ASC",
                (hasta_id,)
            )
            veriler = cur.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Veri alınamadı: {e}")
            return

        if not veriler:
            ctk.CTkLabel(content_frame, text="📊 Henüz ölçüm verisi bulunmuyor", 
                        font=("Arial", 16)).pack(expand=True)
            return

        tarihler = [v[0] for v in veriler]
        seviyeler = [v[1] for v in veriler]

        fig = Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        ax.plot(tarihler, seviyeler, marker='o', linestyle='-', color='#2b5ce6', linewidth=2, markersize=6)
        ax.set_title("Kan Şekeri Takip Grafiği", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("Tarih/Saat", fontsize=12)
        ax.set_ylabel("mg/dL", fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#f8f9fa')
        fig.autofmt_xdate()

        # Normal aralık çizgileri
        ax.axhline(y=70, color='green', linestyle='--', alpha=0.7, label='Alt Normal (70)')
        ax.axhline(y=140, color='orange', linestyle='--', alpha=0.7, label='Üst Normal (140)')
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("""
                SELECT Tip, Tur FROM DiyetEgzersiz 
                WHERE HastaID = %s AND DATE(Tarih) = %s
            """, (hasta_id, date.today()))
            rows = cur.fetchall()
            conn.close()

            if rows:
                for tip, tur in rows:
                    bilgi = f"✅ Bugünkü {tip.capitalize()} Türü: {tur}"
                    ctk.CTkLabel(content_frame, text=bilgi, 
                                font=("Arial", 12), text_color="#2b5ce6").pack(pady=2)
            else:
                ctk.CTkLabel(content_frame, text="Bugün için diyet/egzersiz kaydı bulunamadı.", 
                            font=("Arial", 12), text_color="#999999").pack(pady=5)
        except Exception as e:
            messagebox.showerror("Hata", f"Diyet/Egzersiz bilgisi alınamadı: {e}")

    def gecmis_goster():
        # Treeview ile geçmiş göster
        tree_frame = ctk.CTkFrame(content_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Treeview
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))

        tree = ttk.Treeview(tree_frame, columns=("Tarih", "Saat", "Seviye", "Durum"), show="headings", height=15)
        tree.heading("Tarih", text="📅 Tarih")
        tree.heading("Saat", text="🕐 Saat")
        tree.heading("Seviye", text="🩸 Seviye (mg/dL)")
        tree.heading("Durum", text="✅ Durum")

        tree.column("Tarih", width=120)
        tree.column("Saat", width=80)
        tree.column("Seviye", width=120)
        tree.column("Durum", width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Verileri yükle
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute(
                "SELECT TarihSaat, SeviyeMgDl, Gecerli FROM Olcum WHERE HastaID = %s ORDER BY TarihSaat DESC",
                (hasta_id,)
            )
            
            for row in cur.fetchall():
                tarih_saat, seviye, gecerli = row
                tarih = tarih_saat.strftime("%d.%m.%Y")
                saat = tarih_saat.strftime("%H:%M")
                durum = "Geçerli" if gecerli else "Geçersiz"
                
                # Renk kodlaması
                if seviye < 70:
                    tag = "dusuk"
                elif seviye > 140:
                    tag = "yuksek"
                else:
                    tag = "normal"
                    
                tree.insert("", "end", values=(tarih, saat, seviye, durum), tags=(tag,))
            
            # Renk etiketleri
            tree.tag_configure("normal", background="#d4edda")
            tree.tag_configure("dusuk", background="#f8d7da")
            tree.tag_configure("yuksek", background="#fff3cd")
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Hata", f"Geçmiş yüklenemedi: {e}")

    def grafik_guncelle():
        if aktif_tab.get() == "grafik":
            grafik_goster()

    # Profil fotoğrafı işlemleri
    DEFAULT_IMG_PATH = fr"C:\Users\sadik\Desktop\KOU CENG 2\2.DÖNEM\Prolab\Prolab3\230201040_230201065\assets\default.png"

    def profil_foto_yukle():
        nonlocal active_panel
        if active_panel is not None:
            active_panel.destroy()
        right_panel.pack_forget()
        profil_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
        profil_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        active_panel = profil_frame
        
        header = ctk.CTkFrame(profil_frame, height=60, fg_color="#2b5ce6")
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="👤 Profil Fotoğrafı", font=("Arial",18,"bold"), text_color="white").pack(expand=True)
        
        content = ctk.CTkFrame(profil_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        img_label = ctk.CTkLabel(content, text="Fotoğraf yok", width=200, height=200)
        img_label.pack(pady=20)

        def gorsel_goster(img_data):
            img = Image.open(io.BytesIO(img_data)).resize((200,200))
            foto = CTkImage(light_image=img, size=(200,200))
            img_label.configure(image=foto, text="")
            img_label.image = foto
            # Update header profile (assumes profile_img_label exists)
            mini_img = Image.open(io.BytesIO(img_data)).resize((60,60))
            mini_foto = CTkImage(light_image=mini_img, size=(60,60))
            profile_img_label.configure(image=mini_foto, text="")
            profile_img_label.image = mini_foto

        # Mevcut fotoğrafı yükle
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT ProfilResim FROM Kullanici WHERE KullaniciID = %s", (kullanici_id,))
            sonuc = cur.fetchone()

            if sonuc and sonuc[0]:
                gorsel_goster(sonuc[0])
            else:
                with open(DEFAULT_IMG_PATH, "rb") as f:
                    gorsel_goster(f.read())
        except Exception as e:
            messagebox.showerror("Hata", f"Fotoğraf yüklenemedi:\n{e}")
        finally:
            if conn:
                conn.close()

        def foto_yukle():
            dosya = filedialog.askopenfilename(
                title="Fotoğraf Seç", 
                filetypes=[("Görsel Dosyalar", "*.png *.jpg *.jpeg *.bmp")]
            )
            if not dosya:
                return
            try:
                with open(dosya, "rb") as f:
                    img_binary = f.read()
                conn = baglanti_olustur()
                cur = conn.cursor()
                cur.execute("UPDATE Kullanici SET ProfilResim = %s WHERE KullaniciID = %s",
                            (img_binary, kullanici_id))
                conn.commit()
                gorsel_goster(img_binary)
                messagebox.showinfo("Başarılı", "Profil fotoğrafı güncellendi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Kayıt başarısız:\n{e}")
            finally:
                if conn:
                    conn.close()
        
        def foto_sil():
            try:
                conn = baglanti_olustur()
                cur = conn.cursor()
                cur.execute("UPDATE Kullanici SET ProfilResim = NULL WHERE KullaniciID = %s", (kullanici_id,))
                conn.commit()
                try:
                    with open(DEFAULT_IMG_PATH, "rb") as f:
                        gorsel_goster(f.read())
                except:
                    profile_img_label.configure(image="", text="👤")
                    img_label.configure(image="", text="Varsayılan Profil")
                messagebox.showinfo("Başarılı", "Profil fotoğrafı silindi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Silme hatası:\n{e}")
            finally:
                if conn:
                    conn.close()
        
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        ctk.CTkButton(btn_frame, text="📁 Fotoğraf Seç", command=foto_yukle,
                     fg_color="#28a745", hover_color="#218838").pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="🗑️ Fotoğrafı Sil", command=foto_sil,
                     fg_color="#dc3545", hover_color="#c82333").pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="← Geri", 
                  command=lambda: (profil_frame.destroy(), setattr(__import__('__main__'), 'active_panel', None), right_panel.pack(side="right", fill="both", expand=True)),
                  fg_color="#6c757d", hover_color="#545b62").pack(fill="x", pady=5)

    profile_btn.configure(command=profil_foto_yukle)

    # Başlangıçta profil fotoğrafını yükle
    def baslangic_profil_yukle():
        try:
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute("SELECT ProfilResim FROM Kullanici WHERE KullaniciID = %s", (kullanici_id,))
            sonuc = cur.fetchone()

            if sonuc and sonuc[0]:
                img = Image.open(io.BytesIO(sonuc[0])).resize((60, 60))
                foto = CTkImage(light_image=img, size=(60, 60))
                profile_img_label.configure(image=foto, text="")
                profile_img_label.image = foto
            else:
                try:
                    with open(DEFAULT_IMG_PATH, "rb") as f:
                        img = Image.open(io.BytesIO(f.read())).resize((60, 60))
                        foto = CTkImage(light_image=img, size=(60, 60))
                        profile_img_label.configure(image=foto, text="")
                        profile_img_label.image = foto
                except:
                    pass  # Varsayılan emoji göster
        except Exception:
            pass  # Hata durumunda varsayılan emoji göster
        finally:
            if conn:
                conn.close()

    baslangic_profil_yukle()

    # Footer
    footer_frame = ctk.CTkFrame(root, height=60, fg_color="#343a40", corner_radius=0)
    footer_frame.pack(fill="x", side="bottom")
    footer_frame.pack_propagate(False)

    # Footer içeriği
    footer_left = ctk.CTkFrame(footer_frame, fg_color="transparent")
    footer_left.pack(side="left", fill="y", padx=20)
    
    ctk.CTkLabel(footer_left, text="💊 Diyabet Takip Sistemi", 
                font=("Arial", 14, "bold"), text_color="white").pack(anchor="w", pady=5)
    ctk.CTkLabel(footer_left, text="Sağlığınız bizim önceliğimiz", 
                font=("Arial", 10), text_color="#adb5bd").pack(anchor="w")

    # Çıkış butonu
    ctk.CTkButton(footer_frame, text="🚪 Çıkış Yap", width=120, height=35,
                 fg_color="#dc3545", hover_color="#c82333", 
                 command=root.destroy).place(x=1050, y=12.5)

    # İlk tab'ı göster
    tab_goster("grafik")

    # Ana döngü
    root.mainloop()