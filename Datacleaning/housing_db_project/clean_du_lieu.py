import os
import unicodedata
import numpy as np
import pandas as pd


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Đọc dữ liệu an toàn: tự động kiểm tra chữ ký byte (magic bytes)
    để xử lý trường hợp file Excel (.xlsx) được đổi đuôi thành .csv.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Không tìm thấy file: {filepath}")

    with open(filepath, "rb") as f:
        magic_bytes = f.read(4)

    # PK\x03\x04 là header của định dạng ZIP/XLSX (OpenXML)
    if magic_bytes == b"PK\x03\x04":
        xls = pd.ExcelFile(filepath, engine="openpyxl")
        df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    else:
        df = pd.read_csv(filepath, encoding="utf-8-sig")

    return df


def normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    text_cols = df.select_dtypes(include="object").columns.tolist()

    for col in text_cols:
        df[col] = df[col].apply(
            lambda x: unicodedata.normalize("NFC", str(x).strip())
            if pd.notna(x) and str(x).strip() != ""
            else np.nan
        )

    if "Address" in df.columns:
        df["Address"] = (
            df["Address"]
            .str.rstrip(".")
            .str.replace(r"\s+giá\s+\d+.*$", "", regex=True, case=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    return df


def extract_location_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _parse_address(addr: str):
        if pd.isna(addr):
            return "Unknown", "Unknown"
        parts = [p.strip() for p in str(addr).split(",") if p.strip()]
        if len(parts) <= 1:
            return "Unknown", "Unknown"

        last = parts[-1]
        if last.upper() in ["TPHCM", "TP.HCM", "TP HCM", "HỒ CHÍ MINH", "TP HỒ CHÍ MINH"]:
            city = "Hồ Chí Minh"
            district = parts[-2] if len(parts) >= 2 else "Unknown"
        elif last == "Quận Bình Thạnh":
            city = "Hồ Chí Minh"
            district = "Bình Thạnh"
        elif last in ["Hà Nội", "Hà Nội"]:
            city = "Hà Nội"
            district = parts[-2] if len(parts) >= 2 else "Unknown"
        else:
            city = last
            district = parts[-2] if len(parts) >= 2 else "Unknown"

        return district, city

    parsed = df["Address"].apply(_parse_address)
    df["District"] = [item[0] for item in parsed]
    df["City_Province"] = [item[1] for item in parsed]
    return df


def fix_anomalies_and_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Hoán đổi các dòng bị nhập ngược giữa Area (< 10 m2) và Frontage (>= 15 m)
    swap_mask = (df["Area"] < 10) & (df["Frontage"] >= 15)
    df.loc[swap_mask, ["Area", "Frontage"]] = df.loc[swap_mask, ["Frontage", "Area"]].values

    # 2. Sửa lỗi thiếu dấu chấm thập phân khi Frontage > Area (ví dụ: 46.0m -> 4.6m)
    decimal_mask = df["Frontage"] > df["Area"]
    df.loc[decimal_mask, "Frontage"] = df.loc[decimal_mask, "Frontage"] / 10.0

    # 3. Giới hạn (Winsorization) các biến liên tục ở ngưỡng phân vị 0.5% và 99.5%
    for col in ["Area", "Frontage", "Access Road"]:
        if col in df.columns:
            lower_bound = df[col].quantile(0.005)
            upper_bound = df[col].quantile(0.995)
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound).round(2)

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_non_null_count"] = df.notnull().sum(axis=1)
    df = df.sort_values(by="_non_null_count", ascending=False)

    key_cols = ["Address", "Area", "Floors", "Bedrooms", "Bathrooms", "Price"]
    existing_keys = [c for c in key_cols if c in df.columns]
    df = df.drop_duplicates(subset=existing_keys, keep="first")

    df = df.drop(columns=["_non_null_count"]).sort_index().reset_index(drop=True)
    return df


def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Điền khuyết cho các cột phân loại
    categorical_cols = ["House direction", "Balcony direction", "Legal status", "Furniture state"]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    for col in ["Frontage", "Access Road"]:
        if col in df.columns:
            df[col] = df[col].fillna(
                df.groupby(["City_Province", "District"])[col].transform("median")
            )
            df[col] = df[col].fillna(
                df.groupby("City_Province")[col].transform("median")
            )
            df[col] = df[col].fillna(df[col].median()).round(2)

    for col in ["Floors", "Bedrooms", "Bathrooms"]:
        if col in df.columns:
            df[col] = df[col].fillna(
                df.groupby("City_Province")[col].transform("median")
            )
            df[col] = df[col].fillna(df[col].median()).round().astype("int64")

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Tính đơn giá (Price gốc tính theo Tỷ VNĐ -> nhân 1000 để ra Triệu VNĐ/m2)
    df["Price_per_m2"] = ((df["Price"] * 1000.0) / df["Area"]).round(2)

    legal_map = {"Have certificate": 2, "Sale contract": 1, "Unknown": 0}
    furniture_map = {"Full": 2, "Basic": 1, "Unknown": 0}

    if "Legal status" in df.columns:
        df["Legal_status_code"] = df["Legal status"].map(legal_map).fillna(0).astype("int64")
    if "Furniture state" in df.columns:
        df["Furniture_state_code"] = df["Furniture state"].map(furniture_map).fillna(0).astype("int64")

    # Loại bỏ trùng lặp toàn bộ một lần cuối sau khi điền khuyết
    df = df.drop_duplicates().reset_index(drop=True)
    return df

def clean_and_process_pipeline(
    input_path: str = "raw_dataset_tv3.csv",
    output_path: str = "cleaned_dataset_tv3.csv",
) -> pd.DataFrame:
    print(f"[1/6] Đang đọc dữ liệu từ '{input_path}'...")
    df_raw = load_dataset(input_path)
    print(f"      Kích thước ban đầu: {df_raw.shape[0]} dòng x {df_raw.shape[1]} cột")

    print("[2/6] Chuẩn hóa Unicode (NFC) và làm sạch chuỗi văn bản...")
    df = normalize_text_columns(df_raw)

    print("[3/6] Trích xuất Quận/Huyện (District) và Tỉnh/Thành phố (City_Province)...")
    df = extract_location_features(df)

    print("[4/6] Loại bỏ bản ghi trùng lặp và xử lý lỗi nhập liệu / ngoại lai...")
    df = remove_duplicates(df)
    df = fix_anomalies_and_outliers(df)

    print("[5/6] Điền khuyết (Imputation) theo phân nhóm địa lý...")
    df = impute_missing_values(df)

    print("[6/6] Tạo đặc trưng mới (Feature Engineering) và xuất file sạch...")
    df_clean = engineer_features(df)

    df_clean.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Hoàn tất! Đã lưu dữ liệu sạch tại '{output_path}' ({df_clean.shape[0]} dòng x {df_clean.shape[1]} cột).")
    return df_clean

if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    clean_and_process_pipeline(
        input_path=os.path.join(base_dir, "raw_dataset_tv3.csv"),
        output_path=os.path.join(base_dir, "cleaned_dataset_tv3.csv"),
    )
