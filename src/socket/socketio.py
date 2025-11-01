import socketio

def setup_socket(sio):
    try:
        sio.emit('MachineConnect', {'data': 'Hello from the client!'})
        sio.wait()
    finally:
        sio.disconnect()
    
    @sio.on('connected')
    def on_connect():
        print("Socket connected")
        
    @sio.on('disconnected')
    def on_disconnected():
        print("Socket connected")
        
    @sio.event()
    def on_disconnected():
        print("Socket connected")