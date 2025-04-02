import socketio

sio = socketio.Client()
sio.connect("http://127.0.0.1:5000")

@sio.on("location_update")
def on_location_update(data):
    print("New Location Update:", data)

sio.wait()
