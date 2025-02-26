# 住所から緯度経度情報を取得する
from geopy.geocoders import Nominatim
import pandas as pd
import time

# 住所から緯度経度を取得
def get_lat_lon(area_name):
    geolocator = Nominatim(user_agent="geo_app")
    try:
        location = geolocator.geocode(area_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except:
        return None, None

# 人口データ（CSVファイルを読み込む）
df = pd.read_csv("/Users/user/training2412/my_app/map/population/FEH_00200521_250226170039/京都.csv", dtype={"area_code": str})

# 自治体ごとの緯度経度を取得
location_dict = {}
for area in df["都道府県市区町村"].unique():
    lat, lon = get_lat_lon(area)
    if lat and lon:
        location_dict[area] = (lat, lon)
    time.sleep(1)  # API制限を回避

# 結果を表示
print(location_dict)