from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Replace with your actual API key
GOOGLE_GEOLOCATION_API_KEY = "YAIzaSyDi7TUcsXygV5YXPAEkEQZmTZm1sB107No"
GOOGLE_GEOLOCATION_URL = "https://www.googleapis.com/geolocation/v1/geolocate"

@app.route('/get_location', methods=['POST'])
def get_location():
    try:
        # Get WiFi or cell tower data from request (if available)
        data = request.json

        # Send request to Google Geolocation API
        response = requests.post(
            GOOGLE_GEOLOCATION_URL,
            json=data,
            params={'key': GOOGLE_GEOLOCATION_API_KEY}
        )

        # Return the response from Google API
        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
