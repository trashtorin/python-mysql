from housing_system import HousingSystem, in_bang
from config import DB_CONFIG

COT_TIN = ["ma_tin", "dia_chi", "gia_ty", "gia_m2_tr", "dien_tich", "so_phong_ngu", "quan", "tinh_thanh", "phap_ly"]

COT_SUOA_DUOC = ["dia_chi", "dien_tich", "mat_tien", "duong_vao", "huong_nha", "huong_ban_cong",
                 "so_tang", "so_phong_ngu", "so_phong_tam", "phap_ly", "noi_that", "gia_ty"]

COT_SO_NHAP = {"dien_tich", "mat_tien", "duong_vao", "so_tang", "so_phong_ngu", "so_phong_tam", "gia_ty"}

DS_HUONG = ["Bắc", "Nam", "Đông", "Tây", "Đông - Bắc", "Đông - Nam", "Tây - Bắc", "Tây - Nam"]


def doc_lenh(msg):
    try:
        return input(msg)
    except EOFError:
        return "0"


def doc_so(msg, kieu=float):
    s = doc_lenh(msg).strip()
    if not s:
        return None
    try:
        return kieu(s.replace(",", "."))
    except ValueError:
        print("Giá trị không hợp lệ, bỏ qua điều kiện này.")
        return None


def in_menu():
    print()
    print("=" * 58)
    print("   HỆ THỐNG DỮ LIỆU NHÀ ĐẤT - batdongsan.com.vn")
    print("=" * 58)
    print(" 1. Kiểm tra kết nối cơ sở dữ liệu")
    print(" 2. Khởi tạo bảng dữ liệu (schema.sql)")
    print(" 3. Nhập dữ liệu thô từ Excel/CSV (kết quả scraper)")
    print(" 4. Làm sạch dữ liệu thô thành dữ liệu sạch (từ file)")
    print(" 5. Nhập dữ liệu sạch từ file (file đã làm sạch sẵn)")
    print(" 6. Kiểm tra dữ liệu sạch đã lưu trong DB")
    print(" 7. Xem danh sách tin rao (phân trang)")
    print(" 8. Tìm kiếm tin rao")
    print(" 9. Cập nhật thông tin tin rao")
    print("10. Xóa tin rao")
    print("11. Thống kê tổng quan giá nhà")
    print("12. Thống kê giá theo quận/huyện")
    print("13. Thống kê giá theo tỉnh/thành phố")
    print("14. Thống kê theo khoảng diện tích / số phòng ngủ")
    print("15. Phân tích theo pháp lý / Top giá cao thấp nhất")
    print("16. Xuất dữ liệu sạch ra CSV (phục vụ phân tích)")
    print(" 0. Thoát")
    print("=" * 58)


def nhap_file_tho(ht):
    duong_dan = doc_lenh("Đường dẫn file dữ liệu thô (Enter = data/raw_dataset_tv3.csv): ").strip()
    if not duong_dan:
        duong_dan = None
    ht.nhap_file_tho(duong_dan)


def nhap_file_sach(ht):
    duong_dan = doc_lenh("Đường dẫn file dữ liệu sạch (Enter = data/cleaned_dataset_tv3.csv): ").strip()
    if not duong_dan:
        duong_dan = None
    ht.nhap_file_sach(duong_dan)


def xem_danh_sach(ht):
    so_dong = doc_so("Số dòng mỗi trang (Enter = 10): ", int) or 10
    bat_dau = 0
    while True:
        rows = ht.doc_danh_sach_tin(so_dong, bat_dau)
        if not rows:
            if bat_dau == 0:
                print("(Không có dữ liệu sạch, hãy nhập dữ liệu trước)")
            else:
                print("Đã hết dữ liệu.")
            break
        print(f"Các tin rao từ {bat_dau + 1} đến {bat_dau + len(rows)}:")
        in_bang(rows, COT_TIN)
        bat_dau += so_dong
        if doc_lenh("Enter = trang tiếp theo, n = dừng: ").strip().lower() == "n":
            break


def tim_kiem(ht):
    print("Nhập điều kiện tìm kiếm (Enter để bỏ qua):")
    tu_khoa = doc_lenh("Từ khóa trong địa chỉ (VD: Vinhomes, Gò Vấp): ").strip() or None
    quan = doc_lenh("Quận/huyện (VD: Bình Thạnh, Quận 1): ").strip() or None
    tinh = doc_lenh("Tỉnh/thành phố (VD: Hồ Chí Minh): ").strip() or None
    gia_min = doc_so("Giá tối thiểu (tỷ đồng, VD 3.5): ")
    gia_max = doc_so("Giá tối đa (tỷ đồng): ")
    dt_min = doc_so("Diện tích tối thiểu (m2): ")
    dt_max = doc_so("Diện tích tối đa (m2): ")
    phong = doc_so("Số phòng ngủ: ", int)
    huong = doc_lenh(f"Hướng nhà ({', '.join(DS_HUONG)}): ").strip() or None
    gioi_han = doc_so("Số kết quả tối đa (Enter = 20): ", int) or 20
    ht.tim_kiem(tu_khoa=tu_khoa, quan=quan, tinh=tinh, gia_min=gia_min, gia_max=gia_max,
                dt_min=dt_min, dt_max=dt_max, phong=phong, huong=huong, gioi_han=gioi_han)


def cap_nhat_tin(ht):
    ma_tin = doc_so("Mã tin cần cập nhật: ", int)
    if ma_tin is None:
        return
    tin = ht.doc_tin(ma_tin)
    if not tin:
        print("Không tìm thấy tin với mã này.")
        return
    in_bang([tin])
    print("Các cột có thể sửa:", ", ".join(COT_SUOA_DUOC))
    cot = doc_lenh("Tên cột cần sửa: ").strip()
    if cot not in COT_SUOA_DUOC:
        print("Cột không hợp lệ.")
        return
    gia_tri_moi = doc_lenh(f"Giá trị mới cho '{cot}': ").strip()
    if not gia_tri_moi:
        print("Giá trị rỗng, không cập nhật.")
        return
    if cot in COT_SO_NHAP:
        try:
            gia_tri_moi = float(gia_tri_moi.replace(",", "."))
        except ValueError:
            print("Giá trị không phải số.")
            return
    if ht.cap_nhat_tin(ma_tin, {cot: gia_tri_moi}):
        print("Cập nhật thành công.")
        in_bang([ht.doc_tin(ma_tin)])


def xoa_tin(ht):
    ma_tin = doc_so("Mã tin cần xóa: ", int)
    if ma_tin is None:
        return
    tin = ht.doc_tin(ma_tin)
    if not tin:
        print("Không tìm thấy tin với mã này.")
        return
    in_bang([tin])
    xac_nhan = doc_lenh("Bạn chắc chắn muốn xóa? (y/n): ").strip().lower()
    if xac_nhan == "y":
        ht.xoa_tin(ma_tin)
    else:
        print("Đã hủy xóa.")


def thong_ke_dien_tich_phong(ht):
    print("a. Theo khoảng diện tích")
    print("b. Theo số phòng ngủ")
    chon = doc_lenh("Chọn: ").strip().lower()
    if chon == "a":
        ht.thong_ke_theo_dien_tich()
    elif chon == "b":
        ht.thong_ke_theo_phong_ngu()


def thong_ke(ht):
    print("a. Tổng quan giá nhà")
    print("b. Theo quận/huyện")
    print("c. Theo tỉnh/thành phố")
    print("d. Theo khoảng diện tích")
    print("e. Theo số phòng ngủ")
    print("f. Theo pháp lý")
    print("g. Top giá cao/thấp nhất")
    chon = doc_lenh("Chọn loại thống kê: ").strip().lower()
    if chon == "a":
        ht.thong_ke_tong_quan()
    elif chon == "b":
        ht.thong_ke_theo_quan()
    elif chon == "c":
        ht.thong_ke_theo_tinh()
    elif chon == "d":
        ht.thong_ke_theo_dien_tich()
    elif chon == "e":
        ht.thong_ke_theo_phong_ngu()
    elif chon == "f":
        ht.phan_tich_phap_ly()
    elif chon == "g":
        n = doc_so("Số tin mỗi nhóm (Enter = 10): ", int) or 10
        ht.top_gia(n, cao=True)
        ht.top_gia(n, cao=False)


def xuat_csv(ht):
    duong_dan = doc_lenh("File xuất (Enter = du_lieu_sach_xuat.csv): ").strip() or None
    ht.xuat_csv_sach(duong_dan)


def chay_chuc_nang(ht, lua_chon):
    if lua_chon == "1":
        phien_ban = ht.db.kiem_tra_ket_noi()
        print(f"Kết nối OK - MySQL/MariaDB phiên bản: {phien_ban}")
        print("Các bảng hiện có:", ", ".join(ht.db.doc_ten_bang()))
    elif lua_chon == "2":
        if ht.khoi_dong():
            print("Đã khởi tạo các bảng dữ liệu.")
            print("Các bảng hiện có:", ", ".join(ht.db.doc_ten_bang()))
    elif lua_chon == "3":
        nhap_file_tho(ht)
    elif lua_chon == "4":
        ht.lam_sach()
    elif lua_chon == "5":
        nhap_file_sach(ht)
    elif lua_chon == "6":
        ht.kiem_tra_du_lieu_sach()
    elif lua_chon == "7":
        xem_danh_sach(ht)
    elif lua_chon == "8":
        tim_kiem(ht)
    elif lua_chon == "9":
        cap_nhat_tin(ht)
    elif lua_chon == "10":
        xoa_tin(ht)
    elif lua_chon == "11":
        ht.thong_ke_tong_quan()
    elif lua_chon == "12":
        ht.thong_ke_theo_quan()
    elif lua_chon == "13":
        ht.thong_ke_theo_tinh()
    elif lua_chon == "14":
        thong_ke_dien_tich_phong(ht)
    elif lua_chon == "15":
        thong_ke(ht)
    elif lua_chon == "16":
        xuat_csv(ht)
    elif lua_chon == "0":
        print("Đã thoát chương trình.")
    else:
        print("Lựa chọn không hợp lệ.")


def main():
    ht = HousingSystem(DB_CONFIG)
    phien_ban = ht.db.kiem_tra_ket_noi()
    if phien_ban is None:
        print("Không thể kết nối MySQL. Hãy kiểm tra config.py và đảm bảo MySQL đang chạy.")
        return
    print(f"Đã kết nối MySQL ({phien_ban}) - cơ sở dữ liệu: {DB_CONFIG['database']}")
    while True:
        in_menu()
        lua_chon = doc_lenh("Chọn chức năng: ").strip()
        try:
            chay_chuc_nang(ht, lua_chon)
        except Exception as e:
            print(f"Lỗi khi thực hiện chức năng: {e}")
        if lua_chon == "0":
            break
    ht.dong()


if __name__ == "__main__":
    main()
