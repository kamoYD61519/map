import sys
import folium
import tempfile
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
from io import BytesIO
import base64
import geopandas as gpd
#
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QCheckBox, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from mapmain import *

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self) 
        # window title
        self.setWindowTitle("何処に住もうか!? (京都府版)")
        # 住所入力用のウィジェット
        self.ui.address_input.setPlaceholderText("住所を入力（例: 京都駅）")
        # 検索ボタン
        self.ui.search_button.clicked.connect(self.search_location)
        self.rivers={
            '鴨川': ['/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_26_8606040182_10.geojson',34.989743936089084, 135.71761888250657,13],
            '桂川(京都府南部)': ['/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_86_8606040167_10.geojson',34.97544965336611, 135.71980021900657,13], 
            '天神川': ['/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_26_8606040194_10.geojson',34.9858005506766, 135.76777496359688,13],
            '山科川': ['/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_26_8606040774_10.geojson',34.9813807787651, 135.81277047184923,13],
            '木津川': ['/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_86_8606040371_10.geojson',34.83450147151604, 135.7718001223155,13], 
            '宇治川・淀川': ['/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_86_8606040001_10.geojson',34.888877437172106, 135.684038506804,13]
        }
        self.ui.combB1.addItems(self.rivers.keys())
        self.ui.combB1.setVisible(False)
        self.ui.combB1.currentIndexChanged.connect(self.load_map)
        self.years={
            '2020年':['PTN_2020','2,578,087'],
            '2025年':['PTN_2025','2,518,390'],
            '2050年':['PTN_2050','2,075,975'],
            '2070年':['PTN_2070','1,667,139']
        }
        self.ui.combB2.addItems(self.years.keys())
        self.ui.combB2.setVisible(False)
        self.ui.combB2.currentIndexChanged.connect(self.load_map)
        
        # チェックボックス（表示するデータの選択）の準備 =>　表示情報を増やす場合はここを修正
        self.checkboxes = {}
        # 国土数値情報ダウンロードサイト https://nlftp.mlit.go.jp/ksj/index.html
        ksj_data_path='/Users/user/training2412/my_app/map/kjs_data/'
        self.data_sources = {
            "地価公示データ": "/Users/user/Downloads/L01-24_26_GML/L01-24_26.geojson",
            "人口年齢別構成": "/Users/user/training2412/my_app/map/population/京都.csv",
            "氾濫浸水": "/Users/user/training2412/my_app/map/kjs_data/30_浸水継続時間/A31a-30-23_26_8606040182_10.geojson",
            "人口予測": f"{ksj_data_path}500m_mesh_2024_26_GEOJSON/kyoto_pop.geojson"
        }
        for name in self.data_sources.keys():
            checkbox = QCheckBox(name)
            checkbox.setChecked(False)  # 初期状態はチェックなし
            checkbox.stateChanged.connect(self.update_map)
            self.ui.horizontalLayout.addWidget(checkbox) #レイアウト・エリアに設置
            self.checkboxes[name] = checkbox

        # QWebEngineView (地図表示用)
        self.browser = QWebEngineView()
        self.ui.verticalLayout.addWidget(self.browser) #レイアウト・エリアに設置
        self.current_lat = 34.98518642428514  # 初期緯度（京都駅）
        self.current_lon = 135.75854980278922 # 初期経度
        self.zoom = 13

        # 初期地図の表示
        self.load_map()

    def get_style_function(self,name):
        """データごとに異なるスタイルを適用"""
        colors = {
            "路線価": "green",
            "人口統計": "yellow",
            "災害リスク": "red"
        }
        return lambda feature: {
            "fillColor": colors.get(name, "gray"),
            "color": colors.get(name, "gray"),
            "weight": 2,
            "fillOpacity": 0.5
        }

    def load_map(self):
        """現在の位置と選択されたデータを表示"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        self.temp_path = self.temp_file.name

        # Foliumで地図を作成
        self.m = folium.Map(location=[self.current_lat, self.current_lon], zoom_start=self.zoom)

        # マーカーを追加
        folium.Marker([self.current_lat, self.current_lon], popup="検索住所").add_to(self.m)

        # 選択されたGeoJSONデータをオーバーレイ
        for name, filepath in self.data_sources.items():
            if self.checkboxes[name].isChecked():  # 選択されているデータのみ表示
                if name=='地価公示データ':
                    self.zoom = 13
                    with open(filepath, "r", encoding="utf-8") as f:
                        geojson_data = json.load(f)

                    # 価格帯に応じたマーカーの色設定
                    def get_price_color(price):
                        if price > 2000000:  # 高価格（200万円/m² 以上）
                            return "black"
                        elif price > 1000000:  # 中価格（100万円/m² 以上）
                            return "red"
                        elif price > 500000:  # 中価格（50万円/m² 以上）
                            return "orange"
                        elif price > 250000:  # 中価格（30万円/m² 以上）
                            return "blue"
                        elif price > 100000:  # 中価格（30万円/m² 以上）
                            return "lightblue"
                        else:  # 低価格（30万円/m² 未満）
                            return "lightgray"

                    # 各地点のマーカーを地図に追加
                    for feature in geojson_data["features"]:
                        coords = feature["geometry"]["coordinates"]
                        properties = feature["properties"]
                        price = properties["L01_008"]  # 価格情報
                        address = properties["L01_025"]  # 住所
                        land_use = properties["L01_028"]  # 用途
                        popup_text = f"""
                        <b>価格:</b> {price:,d} 円/m²<br>
                        <b>用途:</b> {land_use}
                        """
                        #<b>住所:</b> {address}<br>

                        folium.Marker(
                            location=[coords[1], coords[0]],
                            popup=popup_text,
                            icon=folium.Icon(color=get_price_color(price))
                        ).add_to(self.m)
                    
                    legend_html = '''
                        <div style="position: fixed; bottom: 20px; left: 20px; width: 140px; height: 155px;
                            background-color: white; z-index:9999; font-size:14px; padding:10px;
                            border-radius: 8px; box-shadow: 2px 2px 5px gray;">
                            <b>地価公示</b><br>
                            <i style="background:black;width:10px;height:10px;display:inline-block;"></i> 200万円/m² 以上 <br>
                            <i style="background:red;width:10px;height:10px;display:inline-block;"></i> 100万円/m² 以上<br>
                            <i style="background:orange;width:10px;height:10px;display:inline-block;"></i> 50万円/m² 以上<br>
                            <i style="background:cadetblue;width:10px;height:10px;display:inline-block;"></i> 25万円/m² 以上<br>
                            <i style="background:lightblue;width:10px;height:10px;display:inline-block;"></i> 10万円/m² 以上<br>
                            <i style="background:lightgray;width:10px;height:10px;display:inline-block;"></i> 10万円/m² 未満
                        </div>
                        '''
                    self.m.get_root().html.add_child(folium.Element(legend_html))

                elif name=='人口年齢別構成':
                    self.zoom = 13
                    # 人口データをロード
                    def str_to_tuple(s):
                        return tuple(map(float, s.strip("()").split(",")))
                    # CSVを読み込む際に変換を適用
                    df = pd.read_csv(filepath, converters={"locations": str_to_tuple})
                    population_summary = df.pivot(index="都道府県市区町村", columns="年齢３区分", values="人口").fillna(0)
                    area_name_list=df["都道府県市区町村"].unique()

                    # 円グラフの画像を作成し、地図に埋め込む
                    def create_pie_chart(data, labels):
                        fig, ax = plt.subplots(figsize=(2,2))
                        ax.pie(data, labels=labels, autopct="%1.1f%%", colors=["cyan", "orange", "red"], textprops={'fontsize': 15})
                        ax.axis("equal")

                        buffer = BytesIO()
                        plt.savefig(buffer, format="png", bbox_inches="tight", transparent=True)
                        buffer.seek(0)
                        img_str = base64.b64encode(buffer.read()).decode()
                        plt.close()
                        return f"data:image/png;base64,{img_str}"

                    # 各自治体のデータを処理
                    for area_name, row in population_summary.iterrows():
                        if area_name in area_name_list:
                            locs = df['locations'].loc[df['都道府県市区町村']==area_name]
                            loc,_,_=locs
                            lat, lon = loc
                            data = [row.get("15歳未満", 0), row.get("15～64歳", 0), row.get("65歳以上", 0)]
                            ttl = sum(data)
                            img_tag = create_pie_chart(data, ["15歳未満", "15～64歳", "65歳以上"])
                            popup_html = f"""
                            <b>{area_name}</b><br>
                            <b>人口 {ttl:,d}人</b><br>
                            <img src="{img_tag}" width="100">
                            """
                            folium.Marker(
                                location=[lat, lon],
                                popup=popup_html,
                                icon=folium.Icon(color="darkgreen")
                            ).add_to(self.m)
                            #marker_color_list=[‘red’, ‘blue’, ‘green’, ‘purple’, ‘orange’, ‘darkred’, ’lightred’, ‘beige’, ‘darkblue’, ‘darkgreen’, ‘cadetblue’, ‘darkpurple’, ‘white’, ‘pink’, ‘lightblue’, ‘lightgreen’, ‘gray’, ‘black’, ‘lightgray’]                            
                    
                elif name=='氾濫浸水':
                    def get_flood_color(rank):
                        color_map = {
                            1: "#DBDBFF",  # 12時間未満
                            2: "#8484FF",  # 1日間
                            3: "#4C4CFF",  # 3日間
                            4: "#1919FF",  # 1週間
                            5: "#FF00FF",  # 2週間
                            6: "#FF0000",  # 4週間
                            7: "#000000"   # 4週間以上
                        }
                        return color_map.get(rank, "#D3D3D3")  # 不明な場合はグレー
                    
                    self.ui.combB1.setVisible(True)
                    #self.ui.combB2.setVisible(False)
                    #self.checkboxes['人口予測'].setChecked(False)
                    river=self.ui.combB1.currentText()
                    datafile,_,_,self.zoom=self.rivers.get(river)
                    #datafile,self.current_lat,self.current_lon,self.zoom=self.rivers.get(river)
                    if filepath != datafile:
                        filepath = datafile
                    try:
                        folium.GeoJson(
                            filepath,
                            name='氾濫浸水エリア',
                            style_function=lambda feature: {
                                'fillColor': get_flood_color(feature["properties"].get("A31a_305", 1)),  # デフォルト0
                                'color': 'blue',
                                'weight': 1,
                                'fillOpacity': 0.4,
                            },
                            tooltip=folium.GeoJsonTooltip(fields=["A31a_305"], aliases=["浸水時間ランク"])                            
                        ).add_to(self.m)
                        # レイヤーコントロールの追加
                        folium.LayerControl().add_to(self.m)
                        legend_html = '''
                            <div style="position: fixed; bottom: 20px; right: 20px; width: 140px; height: 175px;
                                background-color: white; z-index:9999; font-size:14px; padding:10px;
                                border-radius: 8px; box-shadow: 2px 2px 5px gray;">
                                <b>浸水継続時間</b><br>
                                <i style="background:#DBDBFF;width:10px;height:10px;display:inline-block;"></i> 1: 12時間未満 <br>
                                <i style="background:#8484FF;width:10px;height:10px;display:inline-block;"></i> 2: 1日間<br>
                                <i style="background:#4C4CFF;width:10px;height:10px;display:inline-block;"></i> 3: 3日間<br>
                                <i style="background:#1919FF;width:10px;height:10px;display:inline-block;"></i> 4: 1週間<br>
                                <i style="background:#FF00FF;width:10px;height:10px;display:inline-block;"></i> 5: 2週間<br>
                                <i style="background:#FF0000;width:10px;height:10px;display:inline-block;"></i> 6: 4週間<br>
                                <i style="background:#000000;width:10px;height:10px;display:inline-block;"></i> 6: 4週間以上
                            </div>
                            '''
                        self.m.get_root().html.add_child(folium.Element(legend_html))

                    except Exception as e:
                        print(f"GeoJSON 読み込みエラー ({name}):", e)
                
                elif name=='人口予測':
                    self.zoom=12
                    def get_population_color(ttl):
                        if ttl > 5000:
                            rnk = 7
                        elif ttl > 3000:
                            rnk = 6
                        elif ttl > 2000:
                            rnk = 5
                        elif ttl > 1000:
                            rnk = 4
                        elif ttl > 500:
                            rnk = 3
                        elif ttl > 100:
                            rnk = 2
                        else:
                            rnk = 1
                        color_map = {
                            1: "#FFF4F4",  # 0m以上0.5m未満（薄い青）
                            2: "#FFFF7A",  # 0.5m以上3.0m未満（青）
                            3: "#FFFF14",  # 3.0m以上5.0m未満（緑）
                            4: "#FFAA56",  # 5.0m以上10.0m未満（黄色）
                            5: "#FF7F00",  # 10.0m以上20.0m未満（オレンジ）
                            6: "#FF00FF",  # 10.0m以上20.0m未満（オレンジ）
                            7: "#FF0000"   # 赤
                        }
                        return color_map.get(rnk, "#D3D3D3")  # 不明な場合はグレー
                    
                        # **GeoJSON を `geopandas` で読み込む**
                    self.ui.combB2.setVisible(True)
                    #self.ui.combB1.setVisible(False)
                    #self.checkboxes['氾濫浸水'].setChecked(False)
                    year=self.ui.combB2.currentText()
                    col,population_total=self.years.get(year)
                    try:
                        folium.GeoJson(
                            filepath,
                            name=f'人口予測({year})',
                            style_function=lambda feature: {
                                'fillColor': get_population_color(feature["properties"].get(col,0)),
                                'color': 'blue',
                                'weight': 0.5,
                                'fillOpacity': 0.6,
                            },
                            tooltip=folium.GeoJsonTooltip(fields=[col], aliases=[f"{year}人口予測"])
                        ).add_to(self.m)
                        # レイヤーコントロールの追加
                        folium.LayerControl().add_to(self.m)
                        legend_html = f'''
                            <div style="position: fixed; top: 50px; left: 50%; transform: translateX(-50%);
                                width: 270px; height: 40px; background-color: white; z-index:9999; font-size:15px;
                                padding:10px; border:2px solid darkgray; border-radius: 8px; 
                                box-shadow: 5px 5px 10px darkgray; 
                                display: flex; justify-content: center; align-items: center; text-align: center;">
                                <b>京都府 総人口予測 {population_total} 人 </b><br>
                            </div>
                            '''
                        self.m.get_root().html.add_child(folium.Element(legend_html))               
                    except Exception as e:
                        print(f"GeoJSON 読み込みエラー ({name}):", e)

                elif name=='都市計画':
                    try:
                        gdf = gpd.read_file(filepath)
                        # GeoJSON形式で保存
                        geojson_path = '/Users/user/training2412/my_app/map/temp_work/flood_inundation.geojson'
                        gdf.to_file(geojson_path, driver='GeoJSON')
                        folium.GeoJson(
                            geojson_path,
                            name='洪水浸水想定区域',
                            style_function=lambda feature: {
                                'fillColor': 'blue',
                                'color': 'blue',
                                'weight': 1,
                                'fillOpacity': 0.5,
                            }
                        ).add_to(self.m)
                        # レイヤーコントロールの追加
                        folium.LayerControl().add_to(self.m)
                        
                    except Exception as e:
                        print(f"GeoJSON 読み込みエラー ({name}):", e)

        # HTMLとして保存
        self.m.save(self.temp_path)

        # QWebEngineView で地図を表示
        self.browser.setUrl(QUrl.fromLocalFile(self.temp_path))

    def search_location(self):
        """住所を座標に変換し、地図を更新"""
        address = self.ui.address_input.text()
        if not address:
            self.ui.result_label.setText("住所を入力してください。")
            return

        lat, lon = self.geocode_address(address)
        if lat is None or lon is None:
            self.ui.result_label.setText("住所を特定できませんでした。")
        else:
            self.current_lat, self.current_lon = lat, lon
            self.ui.result_label.setText(f"緯度: {lat}, 経度: {lon}")
            self.load_map()

    def geocode_address(self, address):
        """住所を緯度経度に変換"""
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }

        try:
            response = requests.get(url, params=params, headers={"User-Agent": "geo-app"})
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return lat, lon
        except Exception as e:
            print("Geocodingエラー:", e)

        return None, None

    def update_map(self):
        """チェックボックスの状態に応じて地図を更新"""
        sender = self.sender()  # どのチェックボックスが変更されたか取得
        if sender == self.checkboxes['氾濫浸水']:
            self.ui.combB1.setVisible(False)
            if self.checkboxes['氾濫浸水'].isChecked():
                self.checkboxes['人口予測'].setChecked(False)  # B をチェック → A をオフ
                self.ui.combB2.setVisible(False)
        elif sender == self.checkboxes['人口予測']:
            self.ui.combB2.setVisible(False)
            if self.checkboxes['人口予測'].isChecked():
                self.checkboxes['氾濫浸水'].setChecked(False)  # A をチェック → B をオフ
                self.ui.combB1.setVisible(False)
        self.load_map()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())