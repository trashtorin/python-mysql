import re
import unicodedata
import pandas as pd

import clean_du_lieu

COT_RAW = ["Address", "Area", "Frontage", "Access Road", "House direction",
           "Balcony direction", "Floors", "Bedrooms", "Bathrooms",
           "Legal status", "Furniture state", "Price"]

COT_SACH = COT_RAW + ["District", "City_Province", "Price_per_m2",
                      "Legal_status_code", "Furniture_state_code"]

BAN_MAP_RAW = {
    "address": "dia_chi", "area": "dien_tich", "frontage": "mat_tien",
    "access_road": "duong_vao", "house_direction": "huong_nha",
    "balcony_direction": "huong_ban_cong", "floors": "so_tang",
    "bedrooms": "so_phong_ngu", "bathrooms": "so_phong_tam",
    "legal_status": "phap_ly", "furniture_state": "noi_that", "price": "gia_ty",
}

BAN_MAP_SACH = dict(BAN_MAP_RAW)
BAN_MAP_SACH.update({
    "district": "quan", "city_province": "tinh_thanh",
    "price_per_m2": "gia_m2_tr", "legal_status_code": "ma_phap_ly",
    "furniture_state_code": "ma_noi_that",
})

COT_SO = ["dien_tich", "mat_tien", "duong_vao", "gia_ty", "gia_m2_tr"]
COT_NGUYEN = ["so_tang", "so_phong_ngu", "so_phong_tam", "ma_phap_ly", "ma_noi_that"]


def chuan_hoa_dia_chi(gia_tri):
    if gia_tri is None or (isinstance(gia_tri, float) and pd.isna(gia_tri)):
        return None
    s = unicodedata.normalize("NFC", str(gia_tri).strip())
    s = s.rstrip(".")
    s = re.sub(r"\s+giá\s+\d+.*$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def doc_file_tho(duong_dan):
    try:
        df = clean_du_lieu.load_dataset(duong_dan)
    except Exception as e:
        print(f"Lỗi đọc file {duong_dan}: {e}")
        return None
    ban_do = {}
    for cot in df.columns:
        key = str(cot).strip().lower().replace(" ", "_")
        if key in BAN_MAP_RAW:
            ban_do[cot] = BAN_MAP_RAW[key]
    df = df.rename(columns=ban_do)
    thieu = [c for c in BAN_MAP_RAW.values() if c not in df.columns]
    if thieu:
        print(f"File dữ liệu thô thiếu các cột: {', '.join(thieu)}")
        return None
    return df


def doi_ten_cot_sach(df):
    ban_do = {}
    for cot in df.columns:
        key = str(cot).strip().lower().replace(" ", "_")
        if key in BAN_MAP_SACH:
            ban_do[cot] = BAN_MAP_SACH[key]
    df = df.rename(columns=ban_do)
    thieu = [c for c in BAN_MAP_SACH.values() if c not in df.columns]
    if thieu:
        print(f"DataFrame dữ liệu sạch thiếu các cột: {', '.join(thieu)}")
        return None
    return df


def doc_file_sach(duong_dan):
    try:
        df = clean_du_lieu.load_dataset(duong_dan)
    except Exception as e:
        print(f"Lỗi đọc file {duong_dan}: {e}")
        return None
    return doi_ten_cot_sach(df)


def lam_tron(gia_tri, so_le):
    if gia_tri is None or (isinstance(gia_tri, float) and pd.isna(gia_tri)):
        return None
    try:
        return round(float(gia_tri), so_le)
    except (TypeError, ValueError):
        return None


def lam_tron_nguyen(gia_tri):
    if gia_tri is None or (isinstance(gia_tri, float) and pd.isna(gia_tri)):
        return None
    try:
        return int(round(float(gia_tri)))
    except (TypeError, ValueError):
        return None


def chuan_hoa_dong(gia_tri_nguon, danh_sach_cot):
    dong = {}
    for cot_db in danh_sach_cot:
        v = gia_tri_nguon.get(cot_db)
        if isinstance(v, float) and pd.isna(v):
            dong[cot_db] = None
        elif isinstance(v, str):
            dong[cot_db] = unicodedata.normalize("NFC", v.strip()) or None
        elif cot_db in COT_SO:
            dong[cot_db] = lam_tron(v, 2)
        elif cot_db in COT_NGUYEN:
            dong[cot_db] = lam_tron_nguyen(v)
        else:
            dong[cot_db] = v
    return dong


def doi_raw_vao_db(db, df):
    if df is None or df.empty:
        return 0
    ds_dong = []
    for i, (_, dong) in enumerate(df.iterrows(), start=1):
        g = chuan_hoa_dong(dong, list(BAN_MAP_RAW.values()))
        g["ma_tin"] = i
        if g["dia_chi"] is None and g["dien_tich"] is None and g["gia_ty"] is None:
            continue
        ds_dong.append(g)
    so_dong = db.them_nhieu("nha_dat", ds_dong)
    return so_dong


def tao_chi_muc_raw(db):
    chi_muc_3 = {}
    chi_muc_2 = {}
    max_ma_tin = 0
    for dong in db.doc("SELECT ma_tin, dia_chi, dien_tich, gia_ty FROM nha_dat"):
        dia_chi = chuan_hoa_dia_chi(dong.get("dia_chi"))
        dien_tich = lam_tron(dong.get("dien_tich"), 2)
        gia_ty = lam_tron(dong.get("gia_ty"), 2)
        ma_tin = int(dong["ma_tin"])
        max_ma_tin = max(max_ma_tin, ma_tin)
        if dia_chi is None or gia_ty is None:
            continue
        k2 = (dia_chi, gia_ty)
        chi_muc_2.setdefault(k2, []).append((ma_tin, dien_tich))
        if dien_tich is not None:
            k3 = (dia_chi, dien_tich, gia_ty)
            chi_muc_3.setdefault(k3, []).append(ma_tin)
    return chi_muc_2, chi_muc_3, max_ma_tin


def doi_sach_vao_db(db, df):
    if df is None or df.empty:
        return 0
    chi_muc_2, chi_muc_3, max_ma_tin = tao_chi_muc_raw(db)
    da_dung = set()
    ds_sach = []
    ds_raw_thieu = []
    ma_tin_tu_dong = 10_000_000
    for _, dong in df.iterrows():
        g = chuan_hoa_dong(dong, list(BAN_MAP_SACH.values()))
        dia_chi = chuan_hoa_dia_chi(g.get("dia_chi"))
        dien_tich = lam_tron(g.get("dien_tich"), 2)
        gia_ty = lam_tron(g.get("gia_ty"), 2)
        if dia_chi is None or gia_ty is None:
            continue
        ma_tin = None
        if dia_chi is not None and gia_ty is not None:
            if dien_tich is not None:
                for i, mt in enumerate(chi_muc_3.get((dia_chi, dien_tich, gia_ty), [])):
                    if mt not in da_dung:
                        ma_tin = mt
                        chi_muc_3[(dia_chi, dien_tich, gia_ty)].pop(i)
                        break
            if ma_tin is None:
                for i, (mt, _) in enumerate(chi_muc_2.get((dia_chi, gia_ty), [])):
                    if mt not in da_dung:
                        ma_tin = mt
                        chi_muc_2[(dia_chi, gia_ty)].pop(i)
                        break
        if ma_tin is None:
            ma_tin = ma_tin_tu_dong
            ma_tin_tu_dong += 1
            ds_raw_thieu.append({
                "ma_tin": ma_tin,
                "dia_chi": dia_chi,
                "dien_tich": dien_tich,
                "gia_ty": gia_ty,
            })
        else:
            da_dung.add(ma_tin)
        g["ma_tin"] = ma_tin
        ds_sach.append(g)
    if ds_raw_thieu:
        db.them_nhieu("nha_dat", ds_raw_thieu)
    so_dong = db.them_nhieu("nha_dat_sach", ds_sach)
    if ds_raw_thieu:
        print(f"Đã khớp {so_dong - len(ds_raw_thieu)}/{len(ds_sach)} bản ghi sạch với dữ liệu thô; "
              f"{len(ds_raw_thieu)} bản ghi không tìm thấy dữ liệu thô gốc nên đã tự tạo bản ghi thô tối thiểu.")
    else:
        print(f"Đã khớp toàn bộ {so_dong}/{len(ds_sach)} bản ghi sạch với dữ liệu thô.")
    return so_dong
