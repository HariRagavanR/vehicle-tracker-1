import os
import threading
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
from pymongo import MongoClient
from geopy.distance import geodesic
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# MongoDB Atlas Connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("\u274c MongoDB URI is missing! Set MONGO_URI in .env file.")

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
        "q": "Chennai, India",  # Modify to dynamically fetch location if needed
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

@app.route("/location", methods=["GET"])
def get_location():
    """Fetches, stores, and broadcasts the real-time location."""
    global last_location, last_timestamp
    lat, lon = get_real_time_location()

    if lat is None or lon is None:
        return jsonify({"error": "Could not fetch location"}), 500

    timestamp = datetime.utcnow()
    speed = 0  # Default speed

    if last_location and last_timestamp:
        distance = geodesic(last_location, (lat, lon)).meters
        time_diff = (timestamp - last_timestamp).total_seconds()
        
        if time_diff > 0:  # Avoid division by zero
            speed = distance / time_diff  # meters per second

    last_location = (lat, lon)
    last_timestamp = timestamp

    location_data = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": timestamp.isoformat(),
        "speed": round(speed, 2)  # Round speed for clarity
    }

    # Store in MongoDB and convert ObjectId to string
    inserted_data = collection.insert_one(location_data)
    location_data["_id"] = str(inserted_data.inserted_id)

    # Emit real-time location update in a separate thread
    threading.Thread(target=lambda: socketio.emit("location_update", location_data)).start()

    return jsonify(location_data)

@app.route("/update_location", methods=["POST"])
def update_location():
    """Receive live location updates from an external source (e.g., mobile device)."""
    global last_location, last_timestamp
    data = request.json
    lat = data.get("latitude")
    lon = data.get("longitude")

    if lat is None or lon is None:
        return jsonify({"error": "Invalid data"}), 400

    timestamp = datetime.utcnow()
    speed = 0  # Default speed

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

    threading.Thread(target=lambda: socketio.emit("location_update", location_data)).start()

    return jsonify({"success": True, "data": location_data}), 200

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)