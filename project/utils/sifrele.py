import hashlib

def sifrele(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def sifre_kontrol(girilen, kayitli_hash):
    return sifrele(girilen) == kayitli_hash
