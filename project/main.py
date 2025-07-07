import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
from customtkinter import CTkImage
from veritabani import kullanici_giris, baglanti_olustur, sifre_uret, sifre_hashle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Tema ayarları
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Ana pencere
pencere = ctk.CTk()
pencere.title("Diyabet Takip Sistemi - Giriş")
pencere.geometry("320x240")
pencere.minsize(300, 200)
pencere.resizable(True, True)

# ── Dinamik Arka Plan ───────────────────────────────────────────────
bg_path = fr"C:\Users\sadik\Desktop\KOU CENG 2\2.DÖNEM\Prolab\Prolab3\230201040_230201065\assets\background.png"
orijinal_bg = Image.open(bg_path)

bg_label = ctk.CTkLabel(pencere, text="")
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

def arka_plani_guncelle(event):
    gen, yuk = pencere.winfo_width(), pencere.winfo_height()
    gorsel = orijinal_bg.resize((gen, yuk))
    ctkgorsel = CTkImage(light_image=gorsel, size=(gen, yuk))
    bg_label.configure(image=ctkgorsel)
    bg_label.image = ctkgorsel

pencere.bind("<Configure>", arka_plani_guncelle)

# ── İçerik Paneli ────────────────────────────────────────────────────
icerik = ctk.CTkFrame(pencere, fg_color="transparent")
icerik.place(relx=0.5, rely=0.5, anchor="center")

def icerigi_temizle():
    for widget in icerik.winfo_children():
        widget.destroy()

# ── Giriş Ekranı ──────────────────────────────────────────────────────
def giris_ekrani():
    icerigi_temizle()
    # TC
    ctk.CTkLabel(icerik, text="TC Kimlik No").pack(pady=(5,3))
    entry_tc = ctk.CTkEntry(icerik, placeholder_text="Örn: 12345678901")
    entry_tc.pack()
    # Şifre
    ctk.CTkLabel(icerik, text="Şifre").pack(pady=(10,3))
    entry_sifre = ctk.CTkEntry(icerik, show="*", placeholder_text="Şifrenizi girin")
    entry_sifre.pack()
    # Şifreyi Göster
    check_var = ctk.BooleanVar()
    def sifre_goster_kontrol():
        entry_sifre.configure(show="" if check_var.get() else "*")
    ctk.CTkCheckBox(
        icerik, text="Şifreyi Göster",
        variable=check_var, command=sifre_goster_kontrol
    ).pack(pady=(5,0))

    # Giriş ve Şifremi Unuttum butonları
    def giris_yap():
        tc = entry_tc.get().strip()
        sifre = entry_sifre.get().strip()

        if len(tc)!=11 or not tc.isdigit():
            messagebox.showerror(
                "Hata",
                "TC Kimlik No 11 haneli ve sadece rakamlardan oluşmalıdır."
            )
            return

        uid, rol = kullanici_giris(tc, sifre)
        if uid is None:
            messagebox.showerror("Hata", "Geçersiz TC veya şifre.")
            return

        pencere.destroy()
        if rol == "doktor":
            from ekranlar.doktor_ekrani import doktor_paneli
            doktor_paneli(uid)
        else:
            from ekranlar.hasta_ekrani import hasta_paneli
            hasta_paneli(uid)

    ctk.CTkButton(icerik, text="Giriş Yap", command=giris_yap).pack(pady=10)
    ctk.CTkButton(
        icerik, text="Şifremi Unuttum",
        fg_color="gray", command=sifremi_unuttum_ekrani
    ).pack(pady=(0,10))

# ── Şifremi Unuttum Ekranı ───────────────────────────────────────────
def sifremi_unuttum_ekrani():
    icerigi_temizle()
    ctk.CTkLabel(
        icerik, text="Kayıtlı e-posta adresinizi girin:", font=("Arial",13)
    ).pack(pady=(10,5))
    entry_email = ctk.CTkEntry(icerik, placeholder_text="mail@example.com")
    entry_email.pack(pady=5)

    def sifreyi_gonder():
        email = entry_email.get().strip()
        if not email:
            messagebox.showwarning("Uyarı", "E-posta boş olamaz.")
            return

        try:
            # 1) Kullanıcıyı bul
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute(
                "SELECT KullaniciID, Ad, Soyad FROM Kullanici WHERE Email = %s",
                (email,)
            )
            row = cur.fetchone()
            conn.close()

            if not row:
                messagebox.showerror(
                    "Hata",
                    "Bu e-posta ile kayıtlı kullanıcı bulunamadı."
                )
                return

            uid, ad, soyad = row

            # 2) Yeni şifre oluştur ve hash’le
            yeni_sifre = sifre_uret()
            sifre_hash = sifre_hashle(yeni_sifre)
            print(f"[DEBUG] Üretilen yeni şifre: {yeni_sifre}")
            print(f"[DEBUG] Üretilen hash:      {sifre_hash}")

            # 3) UPDATE ve rowcount kontrolü
            conn = baglanti_olustur()
            cur = conn.cursor()
            cur.execute(
                "UPDATE Kullanici SET SifreHash = %s WHERE KullaniciID = %s",
                (sifre_hash, uid)
            )
            print(f"[DEBUG] UPDATE satır sayısı: {cur.rowcount}")
            if cur.rowcount == 0:
                messagebox.showwarning(
                    "Uyarı",
                    "Şifre güncellenemedi—Kullanıcı bulunamadı."
                )
                conn.close()
                return
            conn.commit()

            # 4) DB’den tekrar çekip kontrol et
            cur.execute(
                "SELECT SifreHash FROM Kullanici WHERE KullaniciID = %s",
                (uid,)
            )
            db_hash = cur.fetchone()[0]
            print(f"[DEBUG] Veritabanındaki hash: {db_hash}")
            conn.close()

            # 5) E-postayı gönder
            msg = MIMEMultipart()
            msg["From"] = "dortyuz9@gmail.com"
            msg["To"] = email
            msg["Subject"] = "Yeni Şifreniz – Diyabet Takip Sistemi"
            body = (
                f"Merhaba {ad} {soyad},\n\n"
                f"Yeni şifreniz: {yeni_sifre}\n\n"
                "Lütfen sistemde giriş yapınız."
            )
            msg.attach(MIMEText(body, "plain", "utf-8"))
            with smtplib.SMTP("smtp.gmail.com", 587) as s:
                s.starttls()
                s.login("dortyuz9@gmail.com", "ydxo yqpa uszn fivc")
                s.send_message(msg)

            messagebox.showinfo(
                "Başarılı",
                "Yeni şifreniz e-posta adresinize gönderildi."
            )
            giris_ekrani()

        except Exception as e:
            messagebox.showerror("Hata", f"İşlem başarısız:\n{e}")
            try:
                conn.close()
            except:
                pass

    ctk.CTkButton(
        icerik, text="Yeni Şifre Gönder", command=sifreyi_gonder
    ).pack(pady=10)
    ctk.CTkButton(
        icerik, text="← Geri Dön",
        fg_color="gray", command=giris_ekrani
    ).pack(pady=(0,10))

# ── Uygulamayı Başlat ────────────────────────────────────────────────
giris_ekrani()
pencere.mainloop()
