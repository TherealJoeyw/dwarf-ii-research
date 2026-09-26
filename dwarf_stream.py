import websocket
import uuid
import time
import threading
import subprocess
import shutil
import glob
import sys

def find_ffplay():
    ffplay = shutil.which("ffplay")
    if ffplay:
        return ffplay
    patterns = [
        r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg*\bin\ffplay.exe",
        r"C:\Program Files\ffmpeg*\bin\ffplay.exe",
        r"C:\ffmpeg\bin\ffplay.exe",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None

def get_inputs():
    ip = input("Telescope IP address [192.168.7.126]: ").strip()
    if not ip:
        ip = "192.168.7.126"
    print("Camera options:")
    print("  1 = Telephoto (mainstream)")
    print("  2 = Wide (secondstream)")
    cam = input("Camera [1]: ").strip()
    if cam == "2":
        stream_path = "/secondstream"
        cam_type = 1
    else:
        stream_path = "/mainstream"
        cam_type = 0
    return ip, stream_path, cam_type

DEVICE_IP, STREAM_PATH, CAM_TYPE = get_inputs()
CLIENT_ID = str(uuid.uuid4())

def encode_varint(value):
    bits = []
    while value > 0x7F:
        bits.append((value & 0x7F) | 0x80)
        value >>= 7
    bits.append(value)
    return bytes(bits)

def encode_field(field_num, wire_type, data):
    tag = (field_num << 3) | wire_type
    return encode_varint(tag) + data

def make_packet(cmd, module_id, data=b""):
    major = encode_field(1, 0, encode_varint(1))
    minor = encode_field(2, 0, encode_varint(8))
    device_id = encode_field(3, 0, encode_varint(1))
    module_bytes = encode_field(4, 0, encode_varint(module_id))
    cmd_bytes = encode_field(5, 0, encode_varint(cmd))
    type_bytes = encode_field(6, 0, encode_varint(0))
    cid = CLIENT_ID.encode()
    cid_bytes = encode_field(8, 2, encode_varint(len(cid)) + cid)
    data_bytes = b""
    if data:
        data_bytes = encode_field(7, 2, encode_varint(len(data)) + data)
    return major + minor + device_id + module_bytes + cmd_bytes + type_bytes + cid_bytes + data_bytes

def decode_varint(data, pos):
    result = 0
    shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos

def decode_packet(data):
    pos = 0
    fields = {}
    while pos < len(data):
        tag, pos = decode_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x7
        if wire_type == 0:
            val, pos = decode_varint(data, pos)
            fields[field_num] = val
        elif wire_type == 2:
            length, pos = decode_varint(data, pos)
            val = data[pos:pos+length]
            fields[field_num] = val
            pos += length
        else:
            break
    return fields

def keep_alive(ws):
    while True:
        time.sleep(5)
        try:
            ws.send("ping")
        except:
            break

def on_message(ws, message):
    if isinstance(message, bytes):
        fields = decode_packet(message)
        cmd = fields.get(5, "?")
        print(f"RX cmd={cmd}")
    else:
        if message != "pong":
            print(f"RX: {message}")

def on_error(ws, error):
    print(f"ERROR: {error}")

def on_close(ws, code, msg):
    print("Disconnected.")

ffplay_proc = None

def on_open(ws):
    global ffplay_proc
    print(f"Connected ({CLIENT_ID[:8]}...)")
    threading.Thread(target=keep_alive, args=(ws,), daemon=True).start()
    time.sleep(0.5)

    # ENTER_CAMERA
    client_params = encode_field(1, 0, encode_varint(1))
    enter_payload = encode_field(3, 2, encode_varint(len(client_params)) + client_params)
    pkt = make_packet(16404, 14, enter_payload)
    print("Entering camera mode...")
    ws.send(pkt, websocket.ABNF.OPCODE_BINARY)
    time.sleep(0.5)

    # SET_RTSP_BITRATE_TYPE
    module = 1 if CAM_TYPE == 0 else 2
    rtsp_payload = encode_field(1, 0, encode_varint(1))
    cmd = 10042 if CAM_TYPE == 0 else 12032
    pkt = make_packet(cmd, module, rtsp_payload)
    ws.send(pkt, websocket.ABNF.OPCODE_BINARY)
    time.sleep(0.5)

    # GET_SYSTEM_WORKING_STATE
    cmd = 10039 if CAM_TYPE == 0 else 12003
    pkt = make_packet(cmd, module)
    ws.send(pkt, websocket.ABNF.OPCODE_BINARY)
    time.sleep(0.5)

    # SET_PREVIEW_QUALITY
    preview_payload = encode_field(1, 0, encode_varint(1))
    cmd = 10050 if CAM_TYPE == 0 else 12036
    pkt = make_packet(cmd, module, preview_payload)
    ws.send(pkt, websocket.ABNF.OPCODE_BINARY)
    time.sleep(2)

    # Find and launch ffplay
    ffplay_bin = find_ffplay()
    if not ffplay_bin:
        print("ERROR: ffplay not found. Install ffmpeg or add it to PATH.")
        ws.close()
        return

    stream_url = f"http://{DEVICE_IP}:8092{STREAM_PATH}"
    print(f"Opening stream: {stream_url}")
    ffplay_proc = subprocess.Popen([
        ffplay_bin,
        "-loglevel", "warning",
        "-window_title", f"Dwarf II - {'Telephoto' if CAM_TYPE == 0 else 'Wide'}",
        stream_url
    ], creationflags=subprocess.CREATE_NEW_CONSOLE)

    print("Stream open. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
            if ffplay_proc.poll() is not None:
                print("ffplay closed.")
                ws.close()
                break
    except KeyboardInterrupt:
        print("Stopping...")
        if ffplay_proc:
            ffplay_proc.terminate()
        ws.close()

ffplay_bin = find_ffplay()
if not ffplay_bin:
    print("ERROR: ffplay not found. Please install ffmpeg and add it to PATH, or install via winget.")
    sys.exit(1)

ws = websocket.WebSocketApp(
    f"ws://{DEVICE_IP}:9900/?client_id={CLIENT_ID}",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
    on_open=on_open
)

ws.run_forever(ping_interval=40, ping_timeout=10)
