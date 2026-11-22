import os
import pandas as pd
import mysql.connector
from mysql.connector import Error


class DatabaseManager:
    def __init__(self, config):
        self.config = dict(config)
        self.conn = None

    def ket_noi(self):
        try:
            if self.conn is not None and self.conn.is_connected():
                return True
            self.conn = mysql.connector.connect(**self.config)
            return True
        except Error as e:
            print(f"Lỗi kết nối MySQL: {e}")
            return False

    def dong_ket_noi(self):
        if self.conn is not None and self.conn.is_connected():
            self.conn.close()
        self.conn = None

    def kiem_tra_ket_noi(self):
        if not self.ket_noi():
            return None
        cur = self.conn.cursor()
        cur.execute("SELECT VERSION()")
        phien_ban = cur.fetchone()[0]
        cur.close()
        return phien_ban

    def truy_van(self, sql, tham_so=None):
        if not self.ket_noi():
            return False
        cur = self.conn.cursor()
        try:
            cur.execute(sql, tham_so)
            self.conn.commit()
            return True
        except Error as e:
            self.conn.rollback()
            print(f"Lỗi truy vấn: {e}")
            return False
        finally:
            cur.close()

    def truy_van_nhieu(self, sql, danh_sach_tham_so):
        if not danh_sach_tham_so:
            return 0
        if not self.ket_noi():
            return 0
        cur = self.conn.cursor()
        try:
            cur.executemany(sql, danh_sach_tham_so)
            self.conn.commit()
            return len(danh_sach_tham_so)
        except Error as e:
            self.conn.rollback()
            print(f"Lỗi thêm dữ liệu hàng loạt: {e}")
            return 0
        finally:
            cur.close()

    def doc(self, sql, tham_so=None):
        if not self.ket_noi():
            return []
        cur = self.conn.cursor(dictionary=True)
        try:
            cur.execute(sql, tham_so)
            return cur.fetchall()
        except Error as e:
            print(f"Lỗi đọc dữ liệu: {e}")
            return []
        finally:
            cur.close()

    def doc_dataframe(self, sql, tham_so=None):
        ket_qua = self.doc(sql, tham_so)
        return pd.DataFrame(ket_qua)

    def dem(self, bang, dieu_kien=None, tham_so=None):
        sql = f"SELECT COUNT(*) AS so_luong FROM {bang}"
        if dieu_kien:
            sql += f" WHERE {dieu_kien}"
        rows = self.doc(sql, tham_so)
        return rows[0]["so_luong"] if rows else 0

    def doc_theo_ma(self, bang, ma_tin):
        rows = self.doc(f"SELECT * FROM {bang} WHERE ma_tin = %s", (ma_tin,))
        return rows[0] if rows else None

    def them_mot(self, bang, du_lieu):
        if not du_lieu:
            return False
        cot = ", ".join(du_lieu.keys())
        cho = ", ".join(["%s"] * len(du_lieu))
        cap_nhat = ", ".join([f"{c} = VALUES({c})" for c in du_lieu])
        sql = f"INSERT INTO {bang} ({cot}) VALUES ({cho}) ON DUPLICATE KEY UPDATE {cap_nhat}"
        return self.truy_van(sql, tuple(du_lieu.values()))

    def them_nhieu(self, bang, danh_sach_du_lieu):
        if not danh_sach_du_lieu:
            return 0
        cot = list(danh_sach_du_lieu[0].keys())
        cot_sql = ", ".join(cot)
        cho = ", ".join(["%s"] * len(cot))
        cap_nhat = ", ".join([f"{c} = VALUES({c})" for c in cot])
        sql = f"INSERT INTO {bang} ({cot_sql}) VALUES ({cho}) ON DUPLICATE KEY UPDATE {cap_nhat}"
        tham_so = [tuple(d[c] for c in cot) for d in danh_sach_du_lieu]
        return self.truy_van_nhieu(sql, tham_so)

    def cap_nhat(self, bang, ma_tin, du_lieu):
        if not du_lieu:
            return False
        ghep = ", ".join([f"{c} = %s" for c in du_lieu])
        sql = f"UPDATE {bang} SET {ghep} WHERE ma_tin = %s"
        tham_so = tuple(du_lieu.values()) + (ma_tin,)
        return self.truy_van(sql, tham_so)

    def xoa(self, bang, ma_tin):
        return self.truy_van(f"DELETE FROM {bang} WHERE ma_tin = %s", (ma_tin,))

    def doc_ten_bang(self):
        rows = self.doc("SHOW TABLES")
        return [list(r.values())[0] for r in rows]

    def tao_bang(self, duong_dan="schema.sql"):
        if not os.path.exists(duong_dan):
            print(f"Không tìm thấy file schema: {duong_dan}")
            return False
        with open(duong_dan, "r", encoding="utf-8") as f:
            noi_dung = f.read()
        for lenh in [s.strip() for s in noi_dung.split(";") if s.strip()]:
            if not self.truy_van(lenh):
                return False
        return True