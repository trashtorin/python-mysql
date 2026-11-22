CREATE DATABASE IF NOT EXISTS housing_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE housing_db;

CREATE TABLE IF NOT EXISTS nha_dat (
    ma_tin BIGINT PRIMARY KEY,
    dia_chi VARCHAR(300),
    dien_tich DECIMAL(10,2),
    mat_tien DECIMAL(10,2),
    duong_vao DECIMAL(10,2),
    huong_nha VARCHAR(50),
    huong_ban_cong VARCHAR(50),
    so_tang SMALLINT,
    so_phong_ngu SMALLINT,
    so_phong_tam SMALLINT,
    phap_ly VARCHAR(50),
    noi_that VARCHAR(50),
    gia_ty DECIMAL(12,2),
    INDEX idx_nd_dc (dia_chi),
    INDEX idx_nd_gia (gia_ty),
    INDEX idx_nd_dt (dien_tich)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS nha_dat_sach (
    ma_tin BIGINT PRIMARY KEY,
    dia_chi VARCHAR(300),
    dien_tich DECIMAL(10,2),
    mat_tien DECIMAL(10,2),
    duong_vao DECIMAL(10,2),
    huong_nha VARCHAR(50),
    huong_ban_cong VARCHAR(50),
    so_tang SMALLINT,
    so_phong_ngu SMALLINT,
    so_phong_tam SMALLINT,
    phap_ly VARCHAR(50),
    noi_that VARCHAR(50),
    gia_ty DECIMAL(12,2),
    quan VARCHAR(100),
    tinh_thanh VARCHAR(100),
    gia_m2_tr DECIMAL(12,2),
    ma_phap_ly TINYINT,
    ma_noi_that TINYINT,
    INDEX idx_sach_quan (quan),
    INDEX idx_sach_tinh (tinh_thanh),
    INDEX idx_sach_gia (gia_ty),
    INDEX idx_sach_gia_m2 (gia_m2_tr),
    INDEX idx_sach_dt (dien_tich),
    INDEX idx_sach_pn (so_phong_ngu),
    FOREIGN KEY (ma_tin) REFERENCES nha_dat(ma_tin) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW vw_thong_ke_quan AS
SELECT quan,
       tinh_thanh,
       COUNT(*) AS so_tin,
       ROUND(AVG(gia_ty), 2) AS gia_tb_ty,
       ROUND(AVG(gia_m2_tr), 1) AS gia_m2_tb,
       ROUND(MIN(gia_m2_tr), 1) AS gia_m2_thap_nhat,
       ROUND(MAX(gia_m2_tr), 1) AS gia_m2_cao_nhat,
       ROUND(COALESCE(STDDEV(gia_m2_tr), 0), 1) AS gia_m2_do_lech,
       ROUND(AVG(dien_tich), 1) AS dien_tich_tb
FROM nha_dat_sach
WHERE gia_m2_tr IS NOT NULL AND quan IS NOT NULL
GROUP BY quan, tinh_thanh;

CREATE OR REPLACE VIEW vw_thong_ke_tinh AS
SELECT tinh_thanh,
       COUNT(*) AS so_tin,
       ROUND(AVG(gia_ty), 2) AS gia_tb_ty,
       ROUND(AVG(gia_m2_tr), 1) AS gia_m2_tb,
       ROUND(MIN(gia_m2_tr), 1) AS gia_m2_thap_nhat,
       ROUND(MAX(gia_m2_tr), 1) AS gia_m2_cao_nhat,
       ROUND(COALESCE(STDDEV(gia_m2_tr), 0), 1) AS gia_m2_do_lech
FROM nha_dat_sach
WHERE gia_m2_tr IS NOT NULL
GROUP BY tinh_thanh;

CREATE OR REPLACE VIEW vw_thong_ke_dien_tich AS
SELECT CASE
           WHEN dien_tich < 50 THEN 'Dưới 50 m2'
           WHEN dien_tich < 80 THEN '50 - 80 m2'
           WHEN dien_tich < 120 THEN '80 - 120 m2'
           WHEN dien_tich < 200 THEN '120 - 200 m2'
           ELSE 'Từ 200 m2 trở lên'
       END AS khoang_dien_tich,
       COUNT(*) AS so_tin,
       ROUND(AVG(gia_ty), 2) AS gia_tb_ty,
       ROUND(AVG(gia_m2_tr), 1) AS gia_m2_tb
FROM nha_dat_sach
WHERE dien_tich IS NOT NULL AND gia_m2_tr IS NOT NULL
GROUP BY khoang_dien_tich;

CREATE OR REPLACE VIEW vw_thong_ke_phong_ngu AS
SELECT so_phong_ngu,
       COUNT(*) AS so_tin,
       ROUND(AVG(dien_tich), 1) AS dien_tich_tb,
       ROUND(AVG(gia_ty), 2) AS gia_tb_ty,
       ROUND(AVG(gia_m2_tr), 1) AS gia_m2_tb
FROM nha_dat_sach
WHERE so_phong_ngu IS NOT NULL AND gia_m2_tr IS NOT NULL
GROUP BY so_phong_ngu
ORDER BY so_phong_ngu;
