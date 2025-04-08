import os
import threading
from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
from pymongo import MongoClient
from geopy.distance import geodesic
from datetime import datetime
from dotenv import load_dotenv
import folium

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder="backend/templates")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# MongoDB Atlas Connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("❌ MongoDB URI is missing! Set MONGO_URI in .env file.")

client = MongoClient(MONGO_URI)
db = client["vehicle_tracking"]
collection = db["locations"]

# Store last location for speed calculation
last_location = None
last_timestamp = None

def get_real_time_location():
    """Fetches real-time location using OpenStreetMap's Nominatim API."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": "Chennai, India",
        "format": "json",
    }
    headers = {"User-Agent": "VehicleTrackerApp"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except requests.exceptions.RequestException as e:
        print("⚠️ Error fetching location:", str(e))
        return None, None

def generate_map(lat, lon, path_points):
    """Generates and saves a folium map with the current location and path."""
    m = folium.Map(location=[lat, lon], zoom_start=17)
    folium.Marker([lat, lon], tooltip="Live Location", icon=folium.Icon(color="red")).add_to(m)

    if path_points:
        folium.PolyLine(path_points, color="blue", weight=5, opacity=0.7).add_to(m)

    map_path = os.path.join("templates", "map.html")
    m.save(map_path)

    with open(map_path, "r") as file:
        content = file.read()
    refresh_tag = '<meta http-equiv="refresh" content="5">'
    content = content.replace("<head>", f"<head>{refresh_tag}")
    with open(map_path, "w") as file:
        file.write(content)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Vehicle Tracking API!"})

@app.route("/map")
def map_view():
    return render_template("map.html")

@app.route("/location", methods=["GET"])
def get_location():
    global last_location, last_timestamp
    lat, lon = get_real_time_location()

    if lat is None or lon is None:
        return jsonify({"error": "Could not fetch location"}), 500

    timestamp = datetime.utcnow()
    speed = 0

    if last_location and last_timestamp:
        distance = geodesic(last_location, (lat, lon)).meters
        time_diff = (timestamp - last_timestamp).total_seconds()
        if time_diff > 0:
            speed = distance / time_diff

    last_location = (lat, lon)
    last_timestamp = timestamp

    location_data = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp.isoformat(),
        "speed": round(speed, 2)
    }

    inserted_data = collection.insert_one(location_data)
    location_data["_id"] = str(inserted_data.inserted_id)

    # Generate map
    path_points = [(doc["latitude"], doc["longitude"]) for doc in collection.find().sort("timestamp", 1)]
    generate_map(lat, lon, path_points)

    threading.Thread(target=lambda: socketio.emit("location_update", location_data)).start()
    return jsonify(location_data)

@app.route("/update_location", methods=["POST"])
def update_location():
    global last_location, last_timestamp
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "Invalid data"}), 400

    timestamp = datetime.utcnow()
    speed = 0

    if last_location and last_timestamp:
        distance = geodesic(last_location, (lat, lon)).meters
        time_diff = (timestamp - last_timestamp).total_seconds()
        if time_diff > 0:
            speed = distance / time_diff

    last_location = (lat, lon)
    last_timestamp = timestamp

    location_data = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp.isoformat(),
        "speed": round(speed, 2)
    }

    inserted_data = collection.insert_one(location_data)
    location_data["_id"] = str(inserted_data.inserted_id)

    # Generate map
    path_points = [(doc["latitude"], doc["longitude"]) for doc in collection.find().sort("timestamp", 1)]
    generate_map(lat, lon, path_points)

    threading.Thread(target=lambda: socketio.emit("location_update", location_data)).start()
    return jsonify({"success": True, "data": location_data}), 200

@app.route("/latest-location", methods=["GET"])
def get_latest_location():
    latest = collection.find_one(sort=[("timestamp", -1)])
    if latest:
        latest["_id"] = str(latest["_id"])
        return jsonify(latest)
    else:
        return jsonify({"error": "No data available"}), 404

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
