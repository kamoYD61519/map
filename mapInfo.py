import sys
import folium
import tempfile
import requests
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QCheckBox, QHBoxLayout
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

        # チェックボックス（表示するデータの選択）
        self.checkboxes = {}
        check_layout = QHBoxLayout()

        self.data_sources = {
            "路線価": "route_value.geojson",
            "人口統計": "population.geojson",
            "災害リスク": "disaster.geojson"
        }

        for name in self.data_sources.keys():
            checkbox = QCheckBox(name)
            checkbox.setChecked(False)  # 初期状態は非表示
            checkbox.stateChanged.connect(self.update_map)
            check_layout.addWidget(checkbox)
            self.checkboxes[name] = checkbox

        layout.addLayout(check_layout)

        # 結果表示ラベル
        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        # QWebEngineView (地図表示用)
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)

        self.current_lat = 35.681236  # 初期緯度（東京駅）
        self.current_lon = 139.767125  # 初期経度

        # 初期地図の表示
        self.load_map()

    def get_style_function(self,name):
        """データごとに異なるスタイルを適用"""
        colors = {
            "路線価": "green",
            "人口統計": "blue",
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
            self.current_lat, self.current_lon = lat, lon
            self.result_label.setText(f"緯度: {lat}, 経度: {lon}")
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