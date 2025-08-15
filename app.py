from flask import Flask, render_template, url_for, request, jsonify, redirect
from flask_socketio import SocketIO, emit, join_room
import os
import shutil
import subprocess
import uuid

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret!')

# Use CORS="*" for initial testing. Tighten in production.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=False, engineio_logger=False)

@app.route('/healthz')
def healthz():
    return "OK", 200

@app.route('/')
def index():
    room_id = request.args.get('room_id', '')
    return render_template('home.html', room_id=room_id)

@app.route('/compile', methods=['POST','GET'])
def compile_route():
    if request.method == 'POST':
        body = request.get_json() or {}
        code = body.get('codeVal')
        inputVal = body.get('inputVal')
        langType = body.get('langType')
        output = code_exe(langType, code, inputVal)
        return jsonify({'result': output})
    else:
        return jsonify({'error': 'invalid access'})

@app.route('/editor/<string:room_id>', methods=['GET', 'POST'])
def editor(room_id):
    if request.method == 'POST':
        username = request.form.get('username')
        return render_template('editor.html', room_id=room_id, userName=username)
    else:
        return redirect(url_for("index", room_id=room_id))

@socketio.on('join')
def handle_join(data):
    print("join")
    room = data['room']
    userName = data['userName']
    join_room(room)
    emit('request_users', {'room': room, 'userName': userName}, to=room, skip_sid=True)
    emit('request_editors', {'room': room}, to=room, skip_sid=True)

@socketio.on('requested_users')
def requested_users(data):
    room = data['room']
    users = data['users']
    emit('create_users', {'room': room, 'users': users}, to=room, skip_sid=True)

@socketio.on('requested_editors')
def requested_editors(data):
    print("render_editors")
    room = data['room']
    currentEditors = data['currentEditors']
    fileCount = data['fileCount']
    print(currentEditors)
    emit('create_editors', {'room': room, 'currentEditors': currentEditors, 'fileCount': fileCount}, to=room, skip_sid=True)

@socketio.on('update_text')
def handle_update(data):
    # CHANGED: Now receiving 'patch' instead of 'text'
    room = data['room']
    patch = data['patch']
    currentTextEditorName = data['currentTextEditorName']
    userName = data['userName']
    cursor = data['cursor']
    # CHANGED: Broadcasting 'patch' instead of 'text'
    emit('update_text', {'patch': patch, 'currentTextEditorName': currentTextEditorName, 'userName': userName, 'cursor': cursor}, to=room, skip_sid=True)

@socketio.on('create_new_file')
def create_new_file(data):
    print("create_new_file in app.py")
    room = data['room']
    fileCount = data['fileCount']
    fileName = data['fileName']
    emit('create_new_file', {'room': room, 'fileCount': fileCount, 'fileName': fileName}, to=room, skip_sid=True)

@socketio.on('delete_file')
def delete_file(data):
    room = data['room']
    fileId = data['fileId']
    emit('delete_file', {'room': room, 'fileId': fileId}, to=room, skip_sid=True)

@socketio.on('rename_file')
def rename_file(data):
    room = data['room']
    fileId = data['fileId']
    newFileName = data['newFileName']
    emit('rename_file', {'room': room, 'fileId': fileId, 'newFileName': newFileName}, to=room, skip_sid=True)

def code_exe(language, code, inputVal):
    if language != "cpp" and language != "py":
        return "error: Invalid File Extension\nUse cpp or py File Extensions."

    fileName = language + "_code." + language
    sessionId = str(uuid.uuid4())

    folderPath = os.path.join("temp", sessionId)
    filePath = os.path.join(folderPath, fileName)

    os.makedirs(folderPath, exist_ok=True)

    with open(filePath, "w") as f:
        f.write(code)

    try:
        if language == "py":
            execute = subprocess.run(["python3", filePath], timeout=10, input=inputVal, capture_output=True, text=True)
            if execute.returncode != 0:
                if os.path.exists(folderPath):
                    shutil.rmtree(folderPath)
                return execute.stderr
            if os.path.exists(folderPath):
                shutil.rmtree(folderPath)
            return execute.stdout

        elif language == "cpp":
            command = ["g++", "-o", f"{folderPath}/{fileName}_out", filePath]
            compileCode = subprocess.run(command, capture_output=True, text=True)
            if compileCode.returncode != 0:
                if os.path.exists(folderPath):
                    shutil.rmtree(folderPath)
                return compileCode.stderr

            execute = subprocess.run([f"./{folderPath}/{fileName}_out"], timeout=10, input=inputVal, capture_output=True, text=True)
            if os.path.exists(folderPath):
                shutil.rmtree(folderPath)
            return execute.stderr if execute.returncode != 0 else execute.stdout

    except subprocess.TimeoutExpired:
        if os.path.exists(folderPath):
            shutil.rmtree(folderPath)
        return "Timeout expired. The code execution took too long."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
