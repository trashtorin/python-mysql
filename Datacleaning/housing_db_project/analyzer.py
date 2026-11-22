import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

COLUMN_MAP = {
    "Price": "gia_ty",
    "Price_per_m2": "gia_m2_tr",
    "Area": "dien_tich",
    "Frontage": "mat_tien",
    "Access Road": "duong_vao",
    "House direction": "huong_nha",
    "Balcony direction": "huong_ban_cong",
    "Floors": "so_tang",
    "Bedrooms": "so_phong_ngu",
    "Bathrooms": "so_phong_tam",
    "Legal status": "phap_ly",
    "Furniture state": "noi_that",
    "District": "quan",
    "City_Province": "tinh_thanh",
    "Address": "dia_chi"
}

class HousingAnalyzer:

    def __init__(self, dataframe):
        self.df = dataframe.rename(
            columns = {v: k for k, v in COLUMN_MAP.items()}
        ).copy()

    #Tổng quan dataset
    def overview(self):
        print("===== DATASET OVERVIEW =====")
        print("Dataset shape:", self.df.shape)

        #Hiển thị thông tin của dataset (số cột, kiểu dữ liệu,...)
        print("\nDataset information:")
        self.df.info()

        #Đếm số thông tin bị trùng (lặp)
        print("\nDuplicates:", self.df.duplicated().sum())

    def check_columns(self, columns, method_name=""):
        missing = [
            col for col in columns
            if col not in self.df.columns
        ]
        if missing:
            print(f"Cannot perform {method_name}.")
            print("Missing columns:", missing)
            return False
        return True

    def analyze_price(self):
        required_columns = ["Price"]
        if not self.check_columns(required_columns, "Analyze Price"):
            return

        print("\n===== PRICE ANALYSIS =====")

        # Lấy dữ liệu Price
        price = pd.to_numeric(
            self.df["Price"], errors="coerce"
        ).dropna()

        if price.empty:
            print("No valid price data!")
            return

        # Thống kê mô tả
        print("\n1. Descriptive Statistics")
        print(price.describe())

        # Số liệu quan trọng
        print("\n2. Important Metrics")
        print("Mean:", price.mean())
        print("Median:", price.median())
        print("Mode:", price.mode().tolist())
        print("Standard Deviation:", price.std())

        # Sử dụng khoảng tứ phân vị để kiếm tra giá trị ngoại lệ (IQR)
        Q1 = price.quantile(0.25)
        Q3 = price.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = price[
            (price < lower_bound) |
            (price > upper_bound)
        ]

        print("\n3. Outlier Detection")
        print("Q1:", Q1)
        print("Q3:", Q3)
        print("IQR:", IQR)
        print("Lower Bound:", lower_bound)
        print("Upper Bound:", upper_bound)
        print("Number of Outliers:", len(outliers))
        print("Outlier Percentage:", 
            round(len(outliers) / len(price) * 100, 2), "%")

        # 4. Check maximum price frequency ???!!!!!!!!!!!!!!!!
        print("\n4. Maximum Price Check")
        print("Maximum Price:", price.max())
        print("Number of records with Price = 10:",
            (price == 10).sum())

        # 5. Histogram
        plt.figure(figsize=(10, 5))
        plt.hist(price, bins=30, edgecolor="black")
        plt.title("Distribution of Property Prices")
        plt.xlabel("Price (Dataset Unit)")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()

        # 6. Boxplot
        plt.figure(figsize=(10, 3))
        plt.boxplot(price, vert=False)
        plt.title("Boxplot of Property Prices")
        plt.xlabel("Price (Dataset Unit)")
        plt.tight_layout()
        plt.show()

    def analyze_area(self):
        required_columns = ["Area"]
        if not self.check_columns(required_columns, "Analyze Area"):
            return

        print("\n===== AREA ANALYSIS =====")

        # Lấy dữ liệu Area
        area = pd.to_numeric(
            self.df["Area"], errors="coerce"
        ).dropna()

        if area.empty:
            print("No valid area data!")
            return

        # 1. Thống kê mô tả
        print("\n1. Descriptive Statistics")
        print(area.describe())

        # 2. Số liệu quan trọng
        print("\n2. Important Metrics")
        print("Mean:", area.mean())
        print("Median:", area.median())
        print("Mode:", area.mode().tolist())
        print("Standard Deviation:", area.std())

        # 3. Kiểm tra vùng (area) lỗi
        invalid_area = area[area <= 0]
        print("\n3. Invalid Values")
        print("Number of invalid areas:", len(invalid_area))

        # 4. Outlier Detection using IQR
        Q1 = area.quantile(0.25)
        Q3 = area.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = area[
            (area < lower_bound) |
            (area > upper_bound)
        ]
        print("\n4. Outlier Detection")
        print("Q1:", Q1)
        print("Q3:", Q3)
        print("IQR:", IQR)
        print("Lower Bound:", lower_bound)
        print("Upper Bound:", upper_bound)
        print("Number of Outliers:", len(outliers))
        print(
            "Outlier Percentage:",
            round(len(outliers) / len(area) * 100, 2),
            "%"
        )

        # 5. Histogram
        plt.figure(figsize=(10, 5))
        plt.hist(area, bins=30, edgecolor="black")
        plt.title("Distribution of Property Areas")
        plt.xlabel("Area (m²)")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()

        # 6. Boxplot
        plt.figure(figsize=(10, 3))
        plt.boxplot(area, vert=False)
        plt.title("Boxplot of Property Areas")
        plt.xlabel("Area (m²)")
        plt.tight_layout()
        plt.show()

    def analyze_relationship(self):
        required_columns = [
        "Price", "Area", "Bedrooms",
        "Floors", "Legal status", "Furniture state"
    ]

        if not self.check_columns(required_columns, "Analyze Relationship"):
            return

        print("\n===== RELATIONSHIP ANALYSIS =====")

        # 1. Prepare data
        data = self.df.copy()

        numeric_columns = [
            "Price", "Area", "Bedrooms", "Floors"
        ]

        for col in numeric_columns:
            data[col] = pd.to_numeric(
                data[col], errors="coerce"
            )

        # Loại bỏ dữ liệu không hợp lệ
        data = data.dropna(subset=numeric_columns)

        data = data[
            (data["Price"] > 0) &
            (data["Area"] > 0) &
            (data["Bedrooms"] > 0) &
            (data["Floors"] > 0)
        ]

        print("Valid records:", len(data))

        if data.empty:
            print("No valid data!")
            return

        # 2. Price vs Area
        print("\n1. PRICE VS AREA")

        pearson = data["Price"].corr(
            data["Area"], method="pearson"
        )

        spearman = data["Price"].corr(
            data["Area"], method="spearman"
        )

        print("Pearson:", round(pearson, 3))
        print("Spearman:", round(spearman, 3))

        plt.figure(figsize=(10, 6))

        plt.scatter(
            data["Area"],
            data["Price"],
            alpha=0.4,
            s=20
        )

        plt.title("Relationship between Price and Area")
        plt.xlabel("Area (m²)")
        plt.ylabel("Price (Dataset Unit)")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

        # 3. Price vs Bedrooms
        print("\n2. PRICE VS BEDROOMS")

        self._analyze_price_by_group(
            data,
            "Bedrooms",
            "Number of Bedrooms"
        )

        # 4. Price vs Floors
        print("\n3. PRICE VS FLOORS")

        self._analyze_price_by_group(
            data,
            "Floors",
            "Number of Floors"
        )

        # 5. Price vs Legal Status
        print("\n4. PRICE VS LEGAL STATUS")

        legal_data = self.df[["Price", "Legal status"]].copy()

        legal_data["Price"] = pd.to_numeric(
            legal_data["Price"], errors="coerce"
        )

        legal_data = legal_data.dropna()

        legal_data = legal_data[
            legal_data["Price"] > 0
        ]

        legal_data["Legal status"] = (
            legal_data["Legal status"].astype(str).str.strip()
        )

        self._analyze_price_by_group(
            legal_data,
            "Legal status",
            "Legal Status"
        )

        # 6. Price vs Furniture State
        print("\n5. PRICE VS FURNITURE STATE")

        furniture_data = self.df[
            ["Price", "Furniture state"]
        ].copy()

        furniture_data["Price"] = pd.to_numeric(
            furniture_data["Price"], errors="coerce"
        )

        furniture_data = furniture_data.dropna()

        furniture_data = furniture_data[
            furniture_data["Price"] > 0
        ]

        furniture_data["Furniture state"] = (
            furniture_data["Furniture state"].astype(str).str.strip()
        )

        self._analyze_price_by_group(
            furniture_data,
            "Furniture state",
            "Furniture State"
        )

    def analyze_location(self):
        required_columns = [
            "Price", "Price_per_m2", "City_Province"
        ]
        if not self.check_columns(required_columns, "Analyze Location"):
            return

        print("\n===== LOCATION ANALYSIS =====")

        data = self.df.copy()

        # Chuyển đổi dữ liệu giá về dạng số
        data["Price"] = pd.to_numeric(data["Price"], errors="coerce")
        data["Price_per_m2"] = pd.to_numeric(
            data["Price_per_m2"], errors="coerce"
        )

        # Loại bỏ dữ liệu không hợp lệ
        data = data.dropna(subset=["City_Province", "Price"])
        data = data[
            (data["Price"] > 0) &
            (data["City_Province"].astype(str).str.strip() != "")
        ]

        # Chuẩn hóa tên tỉnh/thành phố
        data["City_Province"] = (
            data["City_Province"].astype(str).str.strip()
        )

        if data.empty:
            print("No valid location data!")
            return

        # 1. Thống kê số lượng tin đăng theo khu vực
        print("\n--- Listing Count by City/Province ---")

        location_count = (
            data["City_Province"]
            .value_counts()
            .rename("Listing Count")
        )

        print(location_count)

        # 2. Thống kê giá theo khu vực
        print("\n--- Price Statistics by City/Province ---")

        price_summary = data.groupby("City_Province")["Price"].agg(
            Count="count",
            Mean="mean",
            Median="median",
            Min="min",
            Max="max"
        ).sort_values(by="Median", ascending=False)

        print(price_summary.round(2))

        # 3. Thống kê giá/m2 theo khu vực
        print("\n--- Price per m2 by City/Province ---")

        price_m2_data = data.dropna(subset=["Price_per_m2"])
        price_m2_data = price_m2_data[
            price_m2_data["Price_per_m2"] > 0
        ]
        if price_m2_data.empty:
            print("No valid price per m2 data!")
            price_m2_summary = pd.DataFrame(
                columns = ["Count", "Mean", "Median"]
            )
        else:
            price_m2_summary = (
            price_m2_data.groupby("City_Province")["Price_per_m2"]
            .agg(
                Count="count",
                Mean="mean",
                Median="median"
            )
            .sort_values(by="Median", ascending=False)
        )
        print(price_m2_summary.round(2))

        # 4. Biểu đồ số lượng tin đăng theo khu vực
        plt.figure(figsize=(12, 6))

        location_count.sort_values().plot(
            kind="barh"
        )

        plt.title("Number of Real Estate Listings by City/Province")
        plt.xlabel("Number of Listings")
        plt.ylabel("City/Province")
        plt.tight_layout()
        plt.show()

        # 5. Biểu đồ giá trung vị theo khu vực
        plt.figure(figsize=(12, 6))

        price_summary["Median"].sort_values().plot(
            kind="barh"
        )

        plt.title("Median Property Price by City/Province")
        plt.xlabel("Median Price (Dataset Unit)")
        plt.ylabel("City/Province")
        plt.tight_layout()
        plt.show()

        # 6. Biểu đồ giá/m2 trung vị theo khu vực
        if not price_m2_summary.empty:
            plt.figure(figsize=(12, 6))
            price_m2_summary["Median"].sort_values().plot(kind="barh")
            plt.title("Median Price per m2 by City/Province")
            plt.xlabel("Median Price per m2 (Dataset Unit)")
            plt.ylabel("City/Province")
            plt.tight_layout()
            plt.show()
        else:
            print("Skip price per m2 chart due to no valid data.")


        return {
            "location_count": location_count,
            "price_summary": price_summary,
            "price_m2_summary": price_m2_summary
        }

    def correlation_analysis(self):
        print("\n===== CORRELATION ANALYSIS =====")

        # Các thuộc tính số được sử dụng
        numeric_columns = [
            "Price",
            "Area",
            "Frontage",
            "Access Road",
            "Floors",
            "Bedrooms",
            "Bathrooms"
        ]

        if not self.check_columns(numeric_columns, "Correlation Analysis"):
            return

        data = self.df[numeric_columns].copy()

        # Chuyển đổi dữ liệu sang dạng số
        for col in numeric_columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

        # Loại bỏ các dòng không có dữ liệu hợp lệ
        data = data.dropna()

        if data.empty:
            print("No valid numerical data!")
            return

        # 1. Pearson Correlation
        print("\n--- Pearson Correlation ---")

        pearson_corr = data.corr(method="pearson")

        print(pearson_corr.round(3))

        # 2. Spearman Correlation
        print("\n--- Spearman Correlation ---")

        spearman_corr = data.corr(method="spearman")

        print(spearman_corr.round(3))

        # 3. Correlation Heatmap - Pearson
        plt.figure(figsize=(10, 8))

        plt.imshow(
            pearson_corr,
            cmap="coolwarm",
            interpolation="nearest",
            vmin=-1,
            vmax=1
        )

        plt.colorbar(label="Correlation Coefficient")

        plt.xticks(
            range(len(numeric_columns)),
            numeric_columns,
            rotation=45,
            ha="right"
        )

        plt.yticks(
            range(len(numeric_columns)),
            numeric_columns
        )

        # Hiển thị hệ số tương quan trên từng ô
        for i in range(len(numeric_columns)):
            for j in range(len(numeric_columns)):
                plt.text(
                    j, i,
                    f"{pearson_corr.iloc[i, j]:.2f}",
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=8
                )

        plt.title("Pearson Correlation Heatmap")
        plt.tight_layout()
        plt.show()

        # 4. Các thuộc tính có tương quan với Price
        print("\n--- Correlation with Property Price ---")

        price_correlation = pearson_corr["Price"].drop("Price")

        price_correlation = price_correlation.sort_values(
            key=abs,
            ascending=False
        )

        print(price_correlation.round(3))

        return {
            "pearson": pearson_corr,
            "spearman": spearman_corr,
            "price_correlation": price_correlation
        }

    def _analyze_price_by_group(self, data, feature, title):
        print(f"\n===== PRICE BY {title.upper()} =====")

        summary = data.groupby(feature)["Price"].agg(
            Count="count",
            Median="median",
            Mean="mean"
        ).sort_values(by="Median", ascending=False)

        print(summary.round(2))

        labels = summary.index.astype(str).tolist()

        values = [
            data.loc[data[feature] == category, "Price"].values
            for category in summary.index
        ]

        plt.figure(figsize=(10, 5))

        plt.boxplot(values, showfliers=False)

        plt.xticks(
            range(1, len(labels) + 1),
            labels
        )

        plt.title(f"Property Price by {title}")
        plt.xlabel(title)
        plt.ylabel("Price (Dataset Unit)")

        plt.tight_layout()
        plt.show()