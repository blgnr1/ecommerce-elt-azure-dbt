# ==============================================================================
# 1. KÜTÜPHANELERİN İÇE AKTARILMASI (IMPORT)
# ==============================================================================
import os  # Bilgisayardaki dosya yollarını birleştirmek ve .env değişkenlerini okumak için
import shutil  # Kaggle'dan inen geçici klasörü işimiz bitince tamamen silmek için
from urllib.parse import quote_plus  # Şifredeki özel karakterlerin (@, !, #) bağlantı linkini bozmasını engellemek için

from azure.storage.blob import BlobServiceClient  # Azure Data Lake / Blob Storage ile konuşmak için Microsoft'un kütüphanesi
from dotenv import load_dotenv  # Proje klasöründeki gizli .env dosyasını okuyup şifreleri hafızaya yüklemek için
import kagglehub  # Kaggle veri setlerini indirmek için
import pandas as pd  # CSV dosyalarını satır ve sütunlardan oluşan tablolara (DataFrame) çevirmek için
from sqlalchemy import create_engine  # Pandas tablolarını veritabanına (Azure SQL) yazmak için ortak motor arayüzü


# ==============================================================================
# 2. GÜVENLİK: ŞİFRELERİ .ENV DOSYASINDAN OKUMA
# ==============================================================================
load_dotenv()  # Klasördeki .env dosyasını bulur ve içindeki değişkenleri sistem ortamına yükler

# os.getenv("ANAHTAR_ADI") komutu, kodu GitHub'a attığımızda şifrelerimizin görünmemesini sağlar
storage_conn_str = os.getenv("AZURE_STORAGE_CONN_STR")  # Azure Storage erişim anahtarı
server = os.getenv("AZURE_SQL_SERVER")  # Azure SQL sunucu adresi (örn: sunucu.database.windows.net)
database = os.getenv("AZURE_SQL_DATABASE")  # Veritabanı adı (örn: db-finans)
username = os.getenv("AZURE_SQL_USER")  # Veritabanı kullanıcı adı
password = os.getenv("AZURE_SQL_PASSWORD")  # Veritabanı şifresi


# ==============================================================================
# 3. EXTRACT (VERİYİ KAGGLE'DAN ÇEKME VE RAM'E ALMA)
# ==============================================================================
# Veri setini internetten indirir ve bilgisayarda kaydettiği geçici klasörün yolunu döndürür
klasor_yolu = kagglehub.dataset_download(
    "usmohamed/250k-e-commer-fraud-detection-and-customer-analytics"
)

# Tüm CSV tablolarını isimleriyle birlikte saklayacağımız boş bir Python sözlüğü (dictionary) açıyoruz
tablolar = {}

# os.listdir(klasor_yolu), indirilen klasörün içindeki tüm dosya isimlerini bir liste olarak verir
for dosya in os.listdir(klasor_yolu):
    # Klasörde .txt veya .json gibi başka dosyalar varsa atla, sadece .csv dosyalarını al
    if dosya.endswith(".csv"):
        # Dosya adının sonundaki ".csv" uzantısını silerek temiz bir tablo adı elde et (Örn: "customers.csv" -> "customers")
        tablo_adi = dosya.replace(".csv", "")
        
        # Klasör yolu ile dosya adını işletim sistemine uygun şekilde birleştir (Örn: "C:/.../.cache/customers.csv")
        tam_dosya_yolu = os.path.join(klasor_yolu, dosya)
        
        # CSV dosyasını oku, Pandas DataFrame'e çevir ve sözlüğün içine kendi tablo adıyla kaydet
        tablolar[tablo_adi] = pd.read_csv(tam_dosya_yolu)

# Tüm veriler artık bilgisayarın RAM'inde ('tablolar' sözlüğünde) durduğu için diske inen geçici klasörü siliyoruz
shutil.rmtree(klasor_yolu)
print("Geçici dosyalar bilgisayardan silindi. RAM'deki tablolar:", list(tablolar.keys()))


# ==============================================================================
# 4. AZURE BAĞLANTILARINI (DATA LAKE VE SQL) HAZIRLAMA
# ==============================================================================
# --- A) Azure Data Lake (Storage) Bağlantısı ---
# Connection String kullanarak Azure Storage hesabımıza bağlanan ana istemciyi oluşturuyoruz
blob_service = BlobServiceClient.from_connection_string(storage_conn_str)

# Storage içinde "ecommerce-ham" adında bir klasör (container) hedefliyoruz
container_client = blob_service.get_container_client("ecommerce-ham")

# Eğer bulutta henüz "ecommerce-ham" adında bir klasör yoksa, hata vermemesi için otomatik oluşturuyoruz
if not container_client.exists():
    container_client.create_container()

# --- B) Azure SQL Database Bağlantısı ---
# Veritabanı sürücüsüne (ODBC) vereceğimiz bağlantı kimlik kartını metin olarak hazırlıyoruz
odbc_str = (
    "Driver={ODBC Driver 18 for SQL Server};"  # Windows'taki Microsoft SQL Server tercüman sürücüsü
    f"Server=tcp:{server},1433;"  # Sunucu adresi ve standart SQL Server iletişim kapısı (port 1433)
    f"Database={database};"  # Bağlanılacak hedef veritabanı
    f"Uid={username};"  # Kullanıcı adı (User ID)
    f"Pwd={password};"  # Şifre (Password)
    "Encrypt=yes;"  # Verinin internet üzerinden şifreli gitmesini zorunlu kılar (Azure şartı)
    "TrustServerCertificate=no;"  # Sunucunun güvenlik sertifikasını doğrular
    "Connection Timeout=60;"  # Ücretsiz veritabanı uyku modundaysa uyanması için 60 saniye bekler
)

# SQLAlchemy'ye Microsoft SQL Server (mssql) ve pyodbc kullanarak bu kimlik kartıyla motoru başlatmasını söylüyoruz
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}")


# ==============================================================================
# 5. LOAD (DÖNGÜ İLE HEM DATA LAKE'E HEM AZURE SQL'E YÜKLEME)
# ==============================================================================
# tablolar.items() bize her turda tablonun adını (tablo_adi) ve kendisini (df) ikili olarak verir
for tablo_adi, df in tablolar.items():
    print(f"\nİşleniyor: {tablo_adi} ({len(df)} satır)...")

    # --- ADIM 5.1: Azure Data Lake'e Ham Yedek (Bronze Layer) Atma ---
    # df.to_csv(index=False): Tabloyu diske kaydetmeden RAM'de düz metne (CSV formatına) çevirir.
    # index=False: Pandas'ın kendi verdiği 0, 1, 2... satır numaralarını fazladan sütun olarak eklemesini engeller.
    csv_metni = df.to_csv(index=False)
    
    # Buluttaki "ecommerce-ham" klasörünün içinde oluşturulacak hedef dosyayı işaretliyoruz
    blob_client = container_client.get_blob_client(f"{tablo_adi}.csv")
    
    # RAM'deki CSV metnini buluta yüklüyoruz. overwrite=True: Aynı isimde dosya varsa üzerine yazar.
    blob_client.upload_blob(csv_metni, overwrite=True, max_concurrency=4, timeout=300)
    print(f"  -> Azure Data Lake'e '{tablo_adi}.csv' olarak yüklendi.")

    # --- ADIM 5.2: Azure SQL'e Ham Tablo Olarak Yazma (dbt Buradan Okuyacak) ---
    # dbt ile dönüştüreceğimiz ham tablolara standart olarak "raw_" ön eki veririz (örn: raw_customers)
    hedef_tablo_adi = f"raw_{tablo_adi}"
    
    df.to_sql(
        name=hedef_tablo_adi,   # Veritabanında oluşacak tablonun adı
        con=engine,             # Yukarıda kurduğumuz SQLAlchemy veritabanı motoru
        if_exists="replace",    # Tablo veritabanında zaten varsa eskisini silip güncel halini yazar
        index=False,            # Pandas satır indeksini veritabanına sütun olarak yazma
        chunksize=5000          # Büyük verilerde bağlantının kopmaması için veriyi 5.000'er satırlık paketler halinde gönderir
    )
    print(f"  -> Azure SQL'e '{hedef_tablo_adi}' tablosu olarak yazıldı.")

print("\nBitti! Tüm tablolar hem Data Lake'e arşivlendi hem de Azure SQL'e yüklendi.")