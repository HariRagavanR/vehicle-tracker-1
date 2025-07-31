Vehicle Tracking Application
This is a Flask-based backend application designed to simulate vehicle tracking, store location data in MongoDB, visualize the path on an interactive map using Folium, and provide real-time updates via WebSockets (SocketIO).

Note: The location fetching in this application is simulated to a fixed point (Chennai, India) using OpenStreetMap's Nominatim API. For real-world vehicle tracking, you would integrate with actual GPS data sources.

Features
Simulated Real-time Location Tracking: Fetches a static location (Chennai) to simulate a vehicle's current position.

Speed Calculation: Calculates the speed of the "vehicle" based on consecutive location updates.

Data Persistence: Stores all location data (latitude, longitude, timestamp, speed) in a MongoDB Atlas database.

Interactive Map Visualization: Generates and serves an HTML map using Folium, displaying the current location and the historical path of the vehicle. The map automatically refreshes to show the latest data.

Real-time Updates: Utilizes Flask-SocketIO to broadcast new location data to connected clients, enabling real-time dashboards or frontends.

API Endpoints: Provides RESTful endpoints for fetching simulated location, updating location (e.g., from a device), and retrieving the latest stored location.

Technologies Used
Backend Framework: Flask

Real-time Communication: Flask-SocketIO

CORS Management: Flask-CORS

Database: MongoDB Atlas (via PyMongo)

Geospatial Calculations: geopy (for geodesic distance)

Map Generation: folium

Environment Variables: python-dotenv

HTTP Requests: requests

Prerequisites
Before running this application, ensure you have the following installed:

Python 3.8+

pip (Python package installer)

Setup
1. Clone the Repository (or save the code)
Save the provided Python code into a file named app.py.

2. Install Dependencies
Navigate to your project directory in the terminal and install the required Python packages:

pip install Flask Flask-SocketIO Flask-Cors requests pymongo geopy python-dotenv folium

3. Set up MongoDB Atlas
Go to MongoDB Atlas and create a free tier account (if you don't have one).

Create a new cluster.

Set up a database user with read and write access.

Configure network access to allow connections from your IP address (or 0.0.0.0/0 for development, but be cautious in production).

Get your connection string (URI). It will look something like:
mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority

4. Configure Environment Variables
Create a file named .env in the same directory as your app.py file. Add your MongoDB Atlas connection URI to it:

MONGO_URI="mongodb+srv://<your_username>:<your_password>@cluster0.abcde.mongodb.net/vehicle_tracking?retryWrites=true&w=majority"

Replace <your_username> and <your_password> with your actual MongoDB Atlas database user credentials.

Running the Application
Ensure all prerequisites are met and environment variables are set.

Open your terminal or command prompt.

Navigate to the directory where app.py is located.

Run the application using:

python app.py

The application will start on http://0.0.0.0:5000 (or http://127.0.0.1:5000).

API Endpoints
The application exposes the following API endpoints:

GET /
Description: Returns a welcome message.

Response:

{"message": "Welcome to the Vehicle Tracking API!"}

GET /map
Description: Renders an HTML page displaying the generated Folium map with the vehicle's current location and historical path. This map automatically refreshes every 5 seconds.

Access: Open http://127.0.0.1:5000/map in your web browser.

GET /location
Description: Simulates fetching a real-time location (hardcoded to Chennai), calculates the speed based on the previous update, stores the data in MongoDB, updates the Folium map, and emits the new location via SocketIO.

Response:

{
    "latitude": 13.0826802,
    "longitude": 80.2707184,
    "timestamp": "2023-10-27T10:30:00.000000",
    "speed": 0.0,
    "_id": "653b6a..."
}

(Note: speed will be 0 for the first call, then calculated based on subsequent calls.)

POST /update_location
Description: Allows manual updating of the vehicle's location. This endpoint is useful for integrating with external devices or testing custom location data. It calculates speed, stores data, updates the map, and emits via SocketIO.

Request Body (JSON):

{
    "latitude": 13.0,
    "longitude": 80.0
}

Response:

{
    "success": true,
    "data": {
        "latitude": 13.0,
        "longitude": 80.0,
        "timestamp": "2023-10-27T10:35:00.000000",
        "speed": 12.34,
        "_id": "653b6b..."
    }
}

GET /latest-location
Description: Retrieves the most recently stored location data from the MongoDB database.

Response:

{
    "latitude": 13.0826802,
    "longitude": 80.2707184,
    "timestamp": "2023-10-27T10:30:00.000000",
    "speed": 0.0,
    "_id": "653b6a..."
}

Or, if no data is available:

{"error": "No data available"}

Real-time Updates (SocketIO)
The application emits location updates through SocketIO on the location_update event. You can connect to this event from a frontend application to receive real-time data.

Event Name: location_update

Data Emitted: The location_data dictionary (same as the /location and /update_location responses).

Example Frontend (JavaScript) to listen for updates:

// Assuming you have Socket.IO client library loaded
const socket = io('http://127.0.0.1:5000'); // Connect to your Flask app

socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
});

socket.on('location_update', (data) => {
    console.log('Received real-time location update:', data);
    // Update your UI here with the new location data
});

socket.on('disconnect', () => {
    console.log('Disconnected from Socket.IO server');
});

socket.on('error', (error) => {
    console.error('Socket.IO error:', error);
});

Directory Structure
.
├── app.py
├── .env
└── templates/
    └── map.html  (This file is generated by Folium)

Troubleshooting
ValueError: ❌ MongoDB URI is missing!: Ensure you have created a .env file in the same directory as app.py and that the MONGO_URI variable is correctly set within it.

MongoDB Connection Issues:

Double-check your MONGO_URI for typos, especially username and password.

Verify your MongoDB Atlas network access settings (IP whitelist).

Ensure your MongoDB Atlas cluster is running.

Map Not Displaying / Old Map: The map.html file is generated and overwritten each time a location update occurs. Ensure your browser is refreshing the page (the meta http-equiv="refresh" tag is added for this). If you're manually refreshing, clear your browser cache.

requests.exceptions.RequestException: This indicates an issue when app.py tries to fetch the simulated location from OpenStreetMap. Check your internet connection or if Nominatim's service is temporarily unavailable.
