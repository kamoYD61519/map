import sys
import folium
import tempfile
import requests
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("地図情報アプリ")
        self.setGeometry(100, 100, 800, 600)

        # 中央ウィジェット設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 住所入力用のウィジェット
        self.address_input = QLineEdit(self)
        self.address_input.setPlaceholderText("住所を入力（例: 東京駅）")
        layout.addWidget(self.address_input)

        # 検索ボタン
        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self.search_location)
        layout.addWidget(self.search_button)

        # 結果表示ラベル
        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        # QWebEngineView (地図表示用)
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)

        # GeoJSONファイルのパス
        self.geojson_path = "sample.geojson"  # 自分のGeoJSONファイルに変更可能

        # 初期地図の表示
        self.load_map(35.681236, 139.767125)  # 初期位置: 東京駅

    def load_map(self, lat, lon, address=""):
        """指定した座標の地図を表示し、GeoJSONをオーバーレイ"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        temp_path = temp_file.name

        # Foliumで地図を作成
        m = folium.Map(location=[lat, lon], zoom_start=15)
        
        # マーカーを追加
        if address:
            folium.Marker([lat, lon], popup=address).add_to(m)

        # GeoJSONデータをオーバーレイ表示
        try:
            with open(self.geojson_path, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
                folium.GeoJson(
                    geojson_data,
                    name="GeoJSON Layer",
                    style_function=lambda feature: {
                        "fillColor": "blue",
                        "color": "black",
                        "weight": 2,
                        "fillOpacity": 0.5
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["name", "value"], aliases=["エリア", "地価"])
                ).add_to(m)
        except Exception as e:
            print("GeoJSON 読み込みエラー:", e)

        # HTMLとして保存
        m.save(temp_path)

        # QWebEngineView で地図を表示
        self.browser.setUrl(QUrl.fromLocalFile(temp_path))

    def search_location(self):
        """住所を座標に変換し、地図を更新"""
        address = self.address_input.text()
        if not address:
            self.result_label.setText("住所を入力してください。")
            return

        lat, lon = self.geocode_address(address)
        if lat is None or lon is None:
            self.result_label.setText("住所を特定できませんでした。")
        else:
            self.result_label.setText(f"緯度: {lat}, 経度: {lon}")
            self.load_map(lat, lon, address)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec_())