import sys
import folium
import tempfile
import requests
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QCheckBox, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from main import *

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self) 
        # window title
        self.setWindowTitle("地図情報アプリ")
        # 住所入力用のウィジェット
        self.ui.address_input.setPlaceholderText("住所を入力（例: 東京駅）")
        # 検索ボタン
        self.ui.search_button.clicked.connect(self.search_location)
        # チェックボックス（表示するデータの選択）の準備 =>　表示情報を増やす場合はここを修正
        self.checkboxes = {}
        self.data_sources = {
            "路線価": "route_value.geojson",
            "人口統計": "population.geojson",
            "災害リスク": "disaster.geojson"
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
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        temp_path = temp_file.name

        # Foliumで地図を作成
        m = folium.Map(location=[self.current_lat, self.current_lon], zoom_start=15)

        # マーカーを追加
        folium.Marker([self.current_lat, self.current_lon], popup="現在地").add_to(m)

        # 選択されたGeoJSONデータをオーバーレイ
        for name, filepath in self.data_sources.items():
            if self.checkboxes[name].isChecked():  # 選択されているデータのみ表示
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        geojson_data = json.load(f)
                        folium.GeoJson(
                            geojson_data,
                            name=name,
                            style_function=self.get_style_function(name),
                            tooltip=folium.GeoJsonTooltip(fields=["name", "value"], aliases=["エリア", "情報"])
                        ).add_to(m)
                except Exception as e:
                    print(f"GeoJSON 読み込みエラー ({name}):", e)

        legend_html = '''
            <div style="position: fixed; bottom: 50px; left: 50px; width: 160px; height: 100px;
                background-color: white; z-index:9999; font-size:14px; padding:10px;
                border-radius: 8px; box-shadow: 2px 2px 5px gray;">
                <b>凡例</b><br>
                <i style="background:green;width:10px;height:10px;display:inline-block;"></i> 路線価<br>
                <i style="background:blue;width:10px;height:10px;display:inline-block;"></i> 人口統計<br>
                <i style="background:red;width:10px;height:10px;display:inline-block;"></i> 災害リスク
            </div>
            '''

        m.get_root().html.add_child(folium.Element(legend_html))

        # HTMLとして保存
        m.save(temp_path)

        # QWebEngineView で地図を表示
        self.browser.setUrl(QUrl.fromLocalFile(temp_path))

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
        self.load_map()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())