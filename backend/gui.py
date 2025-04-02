import sys
import requests
import folium
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, Qt

# Flask API URL (Backend)
API_URL = "https://vehicle-tracker-1-r7vo.onrender.com"

class LocationUpdater(QThread):
    location_updated = pyqtSignal(float, float)  # Signal to update UI

    def run(self):
        """Continuously fetch location and emit updates."""
        while True:
            try:
                response = requests.get(API_URL, timeout=5)
                response.raise_for_status()
                data = response.json()

                if "latitude" in data and "longitude" in data:
                    lat, lon = data["latitude"], data["longitude"]
                    self.location_updated.emit(lat, lon)  # Emit signal
                else:
                    print("⚠️ API returned unexpected data format:", data)
            except requests.exceptions.RequestException as e:
                print("🚨 Error fetching location:", e)
            
            time.sleep(3)  # Refresh every 3 seconds

class GPSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time GPS Tracker")
        self.setGeometry(100, 100, 800, 600)

        # Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Status Label
        self.status_label = QLabel("Fetching Location...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Web view for the map
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        # Refresh Button
        self.refresh_button = QPushButton("Refresh Map")
        self.refresh_button.clicked.connect(self.manual_refresh)
        self.layout.addWidget(self.refresh_button)

        # Path for saving the map
        self.map_path = os.path.abspath("map.html")

        # Generate an initial map
        self.generate_initial_map()

        # Start tracking thread
        self.tracker_thread = LocationUpdater()
        self.tracker_thread.location_updated.connect(self.update_map)  # Connect signal to slot
        self.tracker_thread.start()  # Start thread

    def generate_initial_map(self):
        """Generate an initial map to avoid a blank UI."""
        print("🗺️ Generating initial map...")
        default_location = [13.0827, 80.2707]  # Default to Chennai, India
        vehicle_map = folium.Map(location=default_location, zoom_start=12)
        folium.Marker(default_location, tooltip="Default Location", icon=folium.Icon(color="blue")).add_to(vehicle_map)
        vehicle_map.save(self.map_path)
        self.web_view.setUrl(QUrl.fromLocalFile(self.map_path))

    def update_map(self, lat, lon):
        """Update the map with the latest location."""
        print(f"📍 Updating Map: {lat}, {lon}")
        self.status_label.setText(f"Location: {lat:.6f}, {lon:.6f}")

        vehicle_map = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], tooltip="Live Location", icon=folium.Icon(color="red")).add_to(vehicle_map)
        vehicle_map.save(self.map_path)
        self.web_view.setUrl(QUrl.fromLocalFile(self.map_path))

    def manual_refresh(self):
        """Manual refresh for the map."""
        try:
            response = requests.get(API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "latitude" in data and "longitude" in data:
                self.update_map(data["latitude"], data["longitude"])
            else:
                print("⚠️ API returned unexpected data format:", data)
        except requests.exceptions.RequestException as e:
            print("🚨 Error fetching location:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GPSApp()
    window.show()
    sys.exit(app.exec_())
