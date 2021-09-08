from flask import Flask, render_template, url_for, redirect, request
from flask_socketio import SocketIO, join_room


app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat")
def chat():
    username = request.args.get("username")
    room = request.args.get("room")
    
    if username and room:
        return render_template("chat.html", username=username, room=room)
    else:
        return redirect(url_for("home"))


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info(
        '{} has sent a message to the room {}: {}'.format(data['username'], data['room'], data['message'])
        )
    socketio.emit('receive_message', data, room=data['room'])

@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the roon{}".format(data['username'], data['room']))   # This prints the data, date and time
    join_room(data['room']) # This makes the SocketID when a client joins the room
    socketio.emit("join_room_announcement", data)

    
if __name__ == "__main__":
    socketio.run(app, debug=True)
    
