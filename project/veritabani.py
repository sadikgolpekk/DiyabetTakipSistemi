# veritabani.py

import mysql.connector
from mysql.connector import Error
import hashlib
import random
import string
from utils.sifrele import sifre_kontrol

def baglanti_olustur():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="diyabet_takip"  # dikkat: diyabet_sistemi değil!
        )
        return conn
    except Error as e:
        print("Veritabanı bağlantı hatası:", e)
        return None

def kullanici_giris(tc, sifre):
    conn = baglanti_olustur()
    if not conn:
        return None, None
    cursor = conn.cursor()
    cursor.execute("SELECT KullaniciID, SifreHash FROM Kullanici WHERE TC = %s", (tc,))
    row = cursor.fetchone()
    if row:
        uid, hash_db = row
        if sifre_kontrol(sifre, hash_db):  # doğruysa
            cursor.execute("SELECT COUNT(*) FROM Doktor WHERE KullaniciID = %s", (uid,))
            is_doc = cursor.fetchone()[0] > 0
            rol = "doktor" if is_doc else "hasta"
            return uid, rol
    conn.close()
    return None, None


def sifre_uret(uzunluk=6):
    karakterler = string.ascii_letters + string.digits
    return ''.join(random.choice(karakterler) for _ in range(uzunluk))

def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def hasta_ekle(tc, ad, soyad, email, sifre_hash, cinsiyet, dogum_tarihi):
    conn = baglanti_olustur()
    if conn:
        try:
            cursor = conn.cursor()

            # Önce kullanıcı tablosuna ekle
            cursor.execute("""
                INSERT INTO Kullanici
                    (TC, Ad, Soyad, Email, SifreHash, Cinsiyet, DogumTarihi)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (tc, ad, soyad, email, sifre_hash, cinsiyet[0], dogum_tarihi))

            kullanici_id = cursor.lastrowid

            # Doktor ID'sini sabit belirleyelim (örneğin ilk doktor)
            cursor.execute("SELECT DoktorID FROM Doktor LIMIT 1")
            doktor = cursor.fetchone()
            doktor_id = doktor[0] if doktor else 1

            # Hasta tablosuna ekle
            cursor.execute("""
                INSERT INTO Hasta (KullaniciID, DoktorID)
                VALUES (%s, %s)
            """, (kullanici_id, doktor_id))

            conn.commit()
            return True
        except Exception as e:
            print("Hasta ekleme hatası:", e)
            conn.rollback()
            return False
        finally:
            conn.close()
    return False
