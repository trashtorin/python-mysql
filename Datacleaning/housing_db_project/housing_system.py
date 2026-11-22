import os
import statistics
from decimal import Decimal

import pandas as pd

import import_data
import clean_du_lieu
from database import DatabaseManager

FILE_THO_MAC_DINH = "data/raw_dataset_tv3.csv"
FILE_SACH_MAC_DINH = "data/cleaned_dataset_tv3.csv"


def dinh_dang_gia_ty(v):
    if v is None:
        return "-"
    return f"{float(v):,.2f} tỷ"


def dinh_dang_gia_m2(v):
    if v is None:
        return "-"
    return f"{float(v):,.1f} tr/m2"


def dinh_dang(c, v):
    if v is None:
        return "-"
    if "gia_m2" in c:
        return dinh_dang_gia_m2(v)
    if "gia" in c:
        return dinh_dang_gia_ty(v)
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        if c in ("dien_tich", "mat_tien", "duong_vao", "dien_tich_tb"):
            return f"{float(v):,.2f}"
        return f"{float(v):,.0f}"
    return str(v)[:40]


def in_bang(rows, cot=None):
    if not rows:
        print("(Không có dữ liệu)")
        return
    if cot is None:
        cot = list(rows[0].keys())
    du_lieu = [[dinh_dang(c, r.get(c)) for c in cot] for r in rows]
    ten_cot = [c.replace("_", " ").upper() for c in cot]
    do_rong = [max(len(ten_cot[i]), max(len(d[i]) for d in du_lieu)) for i in range(len(cot))]
    ke = "-" * (sum(do_rong) + 3 * len(cot) + 1)
    print(ke)
    print(" | ".join(ten_cot[i].ljust(do_rong[i]) for i in range(len(cot))))
    print(ke)
    for d in du_lieu:
        print(" | ".join(d[i].ljust(do_rong[i]) for i in range(len(cot))))
    print(ke)


class HousingSystem:
    def __init__(self, config):
        self.db = DatabaseManager(config)
        self.thu_muc = os.path.dirname(os.path.abspath(__file__))

    def khoi_dong(self, duong_dan_schema=None):
        if duong_dan_schema is None:
            duong_dan_schema = os.path.join(self.thu_muc, "schema.sql")
        if not self.db.ket_noi():
            return False
        return self.db.tao_bang(duong_dan_schema)

    def dong(self):
        self.db.dong_ket_noi()

    def nhap_file_tho(self, duong_dan=None):
        if duong_dan is None:
            duong_dan = os.path.join(self.thu_muc, FILE_THO_MAC_DINH)
        df = import_data.doc_file_tho(duong_dan)
        if df is None:
            return 0
        so_dong = import_data.doi_raw_vao_db(self.db, df)
        print(f"Đã nhập {so_dong} bản ghi thô vào bảng nha_dat ({self.db.dem('nha_dat')} bản ghi hiện có).")
        return so_dong

    def nhap_file_sach(self, duong_dan=None):
        if duong_dan is None:
            duong_dan = os.path.join(self.thu_muc, FILE_SACH_MAC_DINH)
        df = import_data.doc_file_sach(duong_dan)
        if df is None:
            return 0
        so_dong = import_data.doi_sach_vao_db(self.db, df)
        print(f"Bảng nha_dat_sach hiện có {self.db.dem('nha_dat_sach')} bản ghi.")
        return so_dong

    def lam_sach(self, duong_dan_tho=None):
        if duong_dan_tho is None:
            duong_dan_tho = os.path.join(self.thu_muc, FILE_THO_MAC_DINH)
        df = clean_du_lieu.load_dataset(duong_dan_tho)
        print(f"Đã đọc {df.shape[0]} dòng dữ liệu thô, bắt đầu quy trình làm sạch...")
        df = clean_du_lieu.normalize_text_columns(df)
        df = clean_du_lieu.extract_location_features(df)
        df = clean_du_lieu.remove_duplicates(df)
        df = clean_du_lieu.fix_anomalies_and_outliers(df)
        df = clean_du_lieu.impute_missing_values(df)
        df = clean_du_lieu.engineer_features(df)
        print(f"Quy trình làm sạch hoàn tất: {df.shape[0]} dòng dữ liệu sạch.")
        df = import_data.doi_ten_cot_sach(df)
        if df is None:
            return 0
        so_dong = import_data.doi_sach_vao_db(self.db, df)
        print(f"Bảng nha_dat_sach hiện có {self.db.dem('nha_dat_sach')} bản ghi.")
        return so_dong

    def kiem_tra_du_lieu_sach(self):
        tong = self.db.dem("nha_dat_sach")
        khong_gia = self.db.dem("nha_dat_sach", "gia_ty IS NULL")
        khong_gia_m2 = self.db.dem("nha_dat_sach", "gia_m2_tr IS NULL")
        khong_dt = self.db.dem("nha_dat_sach", "dien_tich IS NULL")
        khong_quan = self.db.dem("nha_dat_sach", "quan IS NULL OR quan = 'Unknown'")
        khong_dc = self.db.dem("nha_dat_sach", "dia_chi IS NULL")
        sai_fk = self.db.dem("nha_dat_sach s LEFT JOIN nha_dat n ON n.ma_tin = s.ma_tin", "n.ma_tin IS NULL")
        print("=" * 50)
        print("KIỂM TRA DỮ LIỆU SẠCH (bảng nha_dat_sach)")
        print("=" * 50)
        print(f"Tổng số bản ghi          : {tong}")
        print(f"Thiếu giá (gia_ty)       : {khong_gia}")
        print(f"Thiếu giá/m2             : {khong_gia_m2}")
        print(f"Thiếu diện tích          : {khong_dt}")
        print(f"Quận không xác định      : {khong_quan}")
        print(f"Thiếu địa chỉ            : {khong_dc}")
        print(f"Lỗi khóa ngoại (mồ côi)  : {sai_fk}")
        if tong == 0:
            print("Chưa có dữ liệu sạch để kiểm tra.")
        elif sai_fk == 0 and tong > 0:
            print("Kết luận: dữ liệu sạch lưu trữ đầy đủ, khóa ngoại hoạt động đúng.")
        return {"tong": tong, "sai_fk": sai_fk}

    def doc_danh_sach_tin(self, gioi_han=10, bat_dau=0):
        sql = ("SELECT ma_tin, dia_chi, gia_ty, gia_m2_tr, dien_tich, so_phong_ngu, "
               "quan, tinh_thanh, phap_ly, noi_that "
               "FROM nha_dat_sach ORDER BY ma_tin LIMIT %s OFFSET %s")
        return self.db.doc(sql, (int(gioi_han), int(bat_dau)))

    def doc_tin(self, ma_tin):
        return self.db.doc_theo_ma("nha_dat", ma_tin)

    def tim_kiem(self, tu_khoa=None, quan=None, tinh=None, gia_min=None, gia_max=None,
                 dt_min=None, dt_max=None, phong=None, huong=None, gioi_han=20):
        sql = ("SELECT ma_tin, dia_chi, gia_ty, gia_m2_tr, dien_tich, so_phong_ngu, so_tang, "
               "quan, tinh_thanh, phap_ly, noi_that, huong_nha "
               "FROM nha_dat_sach WHERE 1=1")
        tham_so = []
        if tu_khoa:
            sql += " AND dia_chi LIKE %s"
            tham_so.append(f"%{tu_khoa}%")
        if quan:
            sql += " AND quan LIKE %s"
            tham_so.append(f"%{quan}%")
        if tinh:
            sql += " AND tinh_thanh LIKE %s"
            tham_so.append(f"%{tinh}%")
        if gia_min is not None:
            sql += " AND gia_ty >= %s"
            tham_so.append(gia_min)
        if gia_max is not None:
            sql += " AND gia_ty <= %s"
            tham_so.append(gia_max)
        if dt_min is not None:
            sql += " AND dien_tich >= %s"
            tham_so.append(dt_min)
        if dt_max is not None:
            sql += " AND dien_tich <= %s"
            tham_so.append(dt_max)
        if phong is not None:
            sql += " AND so_phong_ngu = %s"
            tham_so.append(phong)
        if huong:
            sql += " AND huong_nha = %s"
            tham_so.append(huong)
        sql += " ORDER BY gia_m2_tr LIMIT %s"
        tham_so.append(int(gioi_han))
        rows = self.db.doc(sql, tuple(tham_so))
        print(f"Tìm thấy {len(rows)} tin rao (hiển thị tối đa {gioi_han}, sắp xếp theo giá/m2 tăng dần):")
        in_bang(rows)
        return rows

    def thong_ke_tong_quan(self):
        tong_tho = self.db.dem("nha_dat")
        tong_sach = self.db.dem("nha_dat_sach")
        rows_m2 = self.db.doc("SELECT gia_m2_tr FROM nha_dat_sach WHERE gia_m2_tr IS NOT NULL")
        rows_gia = self.db.doc("SELECT gia_ty FROM nha_dat_sach WHERE gia_ty IS NOT NULL")
        ds_m2 = [float(r["gia_m2_tr"]) for r in rows_m2]
        ds_gia = [float(r["gia_ty"]) for r in rows_gia]
        print("=" * 55)
        print("THỐNG KÊ TỔNG QUAN GIÁ NHÀ ĐẤT")
        print("=" * 55)
        print(f"Tổng tin rao thô     : {tong_tho}")
        print(f"Tổng bản ghi sạch    : {tong_sach}")
        if ds_m2:
            print(f"Giá/m2 trung bình    : {statistics.mean(ds_m2):,.1f} tr/m2")
            print(f"Giá/m2 trung vị      : {statistics.median(ds_m2):,.1f} tr/m2")
            print(f"Độ phân tán giá/m2 (độ lệch chuẩn): {statistics.stdev(ds_m2):,.1f} tr/m2" if len(ds_m2) > 1 else "")
            print(f"Giá/m2 thấp nhất     : {min(ds_m2):,.1f} tr/m2")
            print(f"Giá/m2 cao nhất      : {max(ds_m2):,.1f} tr/m2")
        if ds_gia:
            print(f"Giá tin trung bình   : {statistics.mean(ds_gia):,.2f} tỷ")
            print(f"Giá tin trung vị     : {statistics.median(ds_gia):,.2f} tỷ")
        else:
            print("Chưa có dữ liệu sạch để thống kê giá.")
        return {"tong_tho": tong_tho, "tong_sach": tong_sach}

    def thong_ke_theo_quan(self, gioi_han=15):
        rows = self.db.doc(f"SELECT * FROM vw_thong_ke_quan ORDER BY so_tin DESC LIMIT {int(gioi_han)}")
        print(f"THỐNG KÊ GIÁ THEO QUẬN/HUYỆN (top {gioi_han} khu vực có nhiều tin nhất):")
        in_bang(rows)
        return rows

    def thong_ke_theo_tinh(self):
        rows = self.db.doc("SELECT * FROM vw_thong_ke_tinh ORDER BY so_tin DESC")
        print("THỐNG KÊ GIÁ THEO TỈNH/THÀNH PHỐ:")
        in_bang(rows)
        return rows

    def thong_ke_theo_dien_tich(self):
        rows = self.db.doc("SELECT * FROM vw_thong_ke_dien_tich")
        print("THỐNG KÊ GIÁ THEO KHOẢNG DIỆN TÍCH:")
        in_bang(rows)
        return rows

    def thong_ke_theo_phong_ngu(self):
        rows = self.db.doc("SELECT * FROM vw_thong_ke_phong_ngu")
        print("THỐNG KÊ GIÁ THEO SỐ PHÒNG NGỦ:")
        in_bang(rows)
        return rows

    def phan_tich_phap_ly(self):
        rows = self.db.doc("SELECT phap_ly, ma_phap_ly, COUNT(*) AS so_tin, "
                           "ROUND(AVG(gia_m2_tr), 1) AS gia_m2_tb "
                           "FROM nha_dat_sach WHERE phap_ly IS NOT NULL "
                           "GROUP BY phap_ly, ma_phap_ly ORDER BY so_tin DESC")
        print("PHÂN TÍCH GIÁ THEO TÌNH TRẠNG PHÁP LÝ:")
        in_bang(rows)
        return rows

    def top_gia(self, n=10, cao=True):
        thu_tu = "DESC" if cao else "ASC"
        ten = "cao nhất" if cao else "thấp nhất"
        sql = (f"SELECT ma_tin, dia_chi, gia_m2_tr, gia_ty, dien_tich, quan, tinh_thanh "
               f"FROM nha_dat_sach WHERE gia_m2_tr IS NOT NULL "
               f"ORDER BY gia_m2_tr {thu_tu} LIMIT {int(n)}")
        rows = self.db.doc(sql)
        print(f"TOP {n} TIN CÓ GIÁ/M2 {ten.upper()}:")
        in_bang(rows)
        return rows

    def cap_nhat_tin(self, ma_tin, du_lieu):
        ok = self.db.cap_nhat("nha_dat", ma_tin, du_lieu)
        if ok and set(du_lieu.keys()) & {"gia_ty", "dien_tich", "so_tang", "so_phong_ngu", "so_phong_tam", "mat_tien", "duong_vao"}:
            print("Lưu ý: đã cập nhật dữ liệu thô, hãy chạy lại chức năng làm sạch (mục 4) để cập nhật dữ liệu sạch.")
        return ok

    def xoa_tin(self, ma_tin):
        ok = self.db.xoa("nha_dat", ma_tin)
        if ok:
            print(f"Đã xóa tin {ma_tin} (kèm bản ghi sạch liên quan do ON DELETE CASCADE).")
        return ok

    def lay_du_lieu_phan_tich(self, quan=None, tinh=None):
        sql = ("SELECT ma_tin, dia_chi, dien_tich, mat_tien, duong_vao, huong_nha, huong_ban_cong, "
               "so_tang, so_phong_ngu, so_phong_tam, phap_ly, ma_phap_ly, noi_that, ma_noi_that, "
               "gia_ty, quan, tinh_thanh, gia_m2_tr FROM nha_dat_sach WHERE gia_m2_tr IS NOT NULL")
        tham_so = []
        if quan:
            sql += " AND quan LIKE %s"
            tham_so.append(f"%{quan}%")
        if tinh:
            sql += " AND tinh_thanh LIKE %s"
            tham_so.append(f"%{tinh}%")
        return self.db.doc_dataframe(sql, tuple(tham_so))

    def xuat_csv_sach(self, duong_dan=None):
        if duong_dan is None:
            duong_dan = os.path.join(self.thu_muc, "du_lieu_sach_xuat.csv")
        df = self.db.doc_dataframe("SELECT * FROM nha_dat_sach")
        if df.empty:
            print("Chưa có dữ liệu sạch để xuất.")
            return None
        df.to_csv(duong_dan, index=False, encoding="utf-8-sig")
        print(f"Đã xuất {len(df)} bản ghi sạch ra file: {duong_dan}")
        return duong_dan
