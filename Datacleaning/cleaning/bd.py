import pandas as pd
import os
import matplotlib.pyplot as plt  
import seaborn as sns            

base_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.abspath(__file__))
raw_path = os.path.join(base_dir, "raw_dataset_tv3.csv")
clean_path = os.path.join(base_dir, "cleaned_dataset_tv3.csv")

df_raw = pd.read_excel(raw_path, engine="openpyxl") 
df_clean = pd.read_csv(clean_path)

missing_raw = df_raw.isnull().sum()
missing_raw = missing_raw[missing_raw > 0].sort_values(ascending=True)
missing_clean = df_clean.isnull().sum()
missing_clean_vals = [missing_clean.get(col, 0) for col in missing_raw.index]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].barh(missing_raw.index, missing_raw.values, color='#ff9999')
axes[0].set_title('Dữ liệu thiếu (Trước)')
axes[1].barh(missing_raw.index, missing_clean_vals, color='#99ff99')
axes[1].set_title('Dữ liệu thiếu (Sau)')
axes[1].set_xlim(0, max(missing_raw.values) * 1.1)

plt.tight_layout()
plt.savefig('sosanh_missing.png')

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(x=df_raw['Area'], ax=axes2[0], color='#ff9999')
axes2[0].set_title('Phân phối Diện tích (Trước)')
sns.boxplot(x=df_clean['Area'], ax=axes2[1], color='#99ff99')
axes2[1].set_title('Phân phối Diện tích (Sau)')

plt.tight_layout()
plt.savefig('sosanh_outlier.png')
print("Đã lưu ảnh biểu đồ thành công!")