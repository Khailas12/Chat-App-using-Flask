from flask import Flask, render_template, url_for, redirect, request
from bson.json_util import dumps
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from pymongo.errors import DuplicateKeyError

from db import get_user, save_user, save_room, add_room_members, get_rooms_for_user, get_room, get_room_members, is_room_member


app = Flask(__name__)
app.secret_key = "SECRET_KEY"
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route("/")
def home():
    rooms = []
    
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
    return render_template("home.html", rooms=rooms)


@app.route("/login", methods=["GET", "POST"])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    
    message = ""
    if request.method == "POST":
        username = request.form.get('username')
        password_input = request.form.get("password")
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for("home"))
        else:
            message = "Failed to login"

    return render_template("login.html", message=message)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
         
        try:
            save_user(username, email, password)
            return redirect(url_for("login"))
        except DuplicateKeyError:
            message = "User already exists!"
            
    return render_template("signup.html", message=message)


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/create-room/", methods=["GET", "POST"])
@login_required
def create_room():
    message = ''
    if request.method == "POST":
        room_name = request.form.get("room_name")
        usernames = [
            username.strip() for username in request.form.get("members").split(',')
            ]
        
        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
                
            add_room_members(room_id, room_name, usernames, current_user.username)
            return redirect(url_for("view_room", room_id=room_id))
        else:
            message = "Failed to create room"
            
    return render_template("create_room.html", message=message)


@app.route("/rooms/<room_id>/")
@login_required
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        return render_template("view_room.html", room=room, room_members=room_members)
    else:
        return 'Room not found', 404


@login_manager.user_loader
def load_user(username):
    return get_user(username)


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info(
        '{} has sent a message to the room {}: {}'.format(
            data['username'], data['room'], data['message'])
    )
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the roon{}".format(
        data['username'], data['room']))   # This prints the data, date and time
    # This makes the SocketID when a client joins the room
    join_room(data['room'])
    socketio.emit("join_room_announcement", data)


if __name__ == "__main__":
    socketio.run(app, debug=True)
