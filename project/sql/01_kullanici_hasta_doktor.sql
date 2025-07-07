
-- ──────────────── 1) Veritabanı yarat ────────────────
CREATE DATABASE IF NOT EXISTS `diyabet_takip`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE `diyabet_takip`;

-- ──────────────── 2) Kullanici tablosu ────────────────
CREATE TABLE IF NOT EXISTS `Kullanici` (
  `KullaniciID` INT AUTO_INCREMENT PRIMARY KEY,
  `TC`          CHAR(11)    NOT NULL UNIQUE COMMENT 'TC Kimlik No',
  `Ad`          VARCHAR(50) NOT NULL,
  `Soyad`       VARCHAR(50) NOT NULL,
  `Email`       VARCHAR(100),
  `Cinsiyet`    ENUM('E','K') DEFAULT NULL,
  `DogumTarihi` DATE        DEFAULT NULL,
  `SifreHash`   CHAR(64)    NOT NULL COMMENT 'SHA-256 hash (hex)',
  `ProfilResim` LONGBLOB    DEFAULT NULL COMMENT 'Profil fotoğrafı binary',
  `CreatedAt`   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `UpdatedAt`   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
                   ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────── 3) Doktor tablosu ────────────────
CREATE TABLE IF NOT EXISTS `Doktor` (
  `DoktorID`    INT AUTO_INCREMENT PRIMARY KEY,
  `KullaniciID` INT           NOT NULL,
  FOREIGN KEY (`KullaniciID`)
    REFERENCES `Kullanici`(`KullaniciID`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) Hasta tablosu (düzeltildi)
CREATE TABLE IF NOT EXISTS `Hasta` (
  `HastaID`     INT AUTO_INCREMENT PRIMARY KEY,
  `KullaniciID` INT           NOT NULL,
  `DoktorID`    INT           DEFAULT NULL,
  FOREIGN KEY (`KullaniciID`)
    REFERENCES `Kullanici`(`KullaniciID`)
    ON DELETE CASCADE,
  FOREIGN KEY (`DoktorID`)
    REFERENCES `Doktor`(`DoktorID`)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ──────────────── 5) Olcum tablosu ────────────────
CREATE TABLE IF NOT EXISTS `Olcum` (
  `OlcumID`    INT AUTO_INCREMENT PRIMARY KEY,
  `HastaID`    INT       NOT NULL,
  `TarihSaat`  DATETIME  NOT NULL,
  `SeviyeMgDl` INT       NOT NULL,
  
  FOREIGN KEY (`HastaID`)
    REFERENCES `Hasta`(`HastaID`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────── 6) Diyet & Egzersiz tablosu ────────────────
CREATE TABLE IF NOT EXISTS `DiyetEgzersiz` (
  `ID`       INT AUTO_INCREMENT PRIMARY KEY,
  `HastaID`  INT       NOT NULL,
  `Tarih`    DATE      NOT NULL,
  `Tip`      ENUM('diyet','egzersiz')        NOT NULL,
  `Durum`    ENUM('yapıldı','yapılmadı')    NOT NULL,
  `Tur`      VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  FOREIGN KEY (`HastaID`)
    REFERENCES `Hasta`(`HastaID`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────── 7) Belirti tablosu ────────────────
CREATE TABLE IF NOT EXISTS `Belirti` (
  `BelirtiID` INT AUTO_INCREMENT PRIMARY KEY,
  `HastaID`   INT       NOT NULL,
  `TarihSaat` DATETIME  NOT NULL,
  `Tip`       ENUM(
      'poliüri','polifaji','polidipsi','nöropati',
      'kilo kaybı','yorgunluk','yara','bulanık görme'
  ) NOT NULL,
  FOREIGN KEY (`HastaID`)
    REFERENCES `Hasta`(`HastaID`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────── 8) Örnek doktor kaydı ────────────────
INSERT INTO `Kullanici`
  (TC, Ad, Soyad, Email, Cinsiyet, DogumTarihi, SifreHash)
VALUES
  (
    '10061279994',       -- TC
    'Sadık',             -- Ad
    'Gölpek',            -- Soyad
    'sadik.golpek@ornek.com',
    'E',                 -- Cinsiyet
    '1995-06-10',        -- Doğum Tarihi
    '9baa6a7a3b12b993181f9df978ea5de0c4086c05cb4788c0944dd6373ba89c29'
    -- SHA-256("4540")
  );

INSERT INTO `Doktor` (`KullaniciID`)
VALUES (LAST_INSERT_ID());


-- ──────────────── 9) İkinci örnek doktor: Ali Kılınç ────────────────
INSERT INTO `Kullanici`
  (TC, Ad, Soyad, Email, Cinsiyet, DogumTarihi, SifreHash)
VALUES
  (
    '22233445566',       -- TC
    'Ali',               -- Ad
    'Kılınç',            -- Soyad
    'ali.kilinc@ornek.com',
    'E',                 -- Cinsiyet
    '1997-03-14',        -- Doğum Tarihi
    '96cae35ce8a9b0244178bf28e4966c2ce1b8385723a96a6b838858cdd6ca0a1e'
    -- SHA-256("123123")
  );

INSERT INTO `Doktor` (`KullaniciID`)
VALUES (LAST_INSERT_ID());





