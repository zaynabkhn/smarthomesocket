# tcp_server.py
import socket
import threading
import time
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5050
LOG_FILE = "server_log.txt"

devices = {}  # name -> {"type": str, "addr": (ip,port), "conn": socket}
devices_lock = threading.Lock()

def log(msg: str):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_registration(line: str):
    # expects: "DEVICE Sensor01 TYPE temperature"
    parts = line.strip().split()
    if len(parts) >= 4 and parts[0].upper() == "DEVICE" and parts[2].upper() == "TYPE":
        name = parts[1]
        typ = " ".join(parts[3:])
        return name, typ
    return None, None

def handle_client(conn: socket.socket, addr):
    conn.settimeout(300)  # 5min idle timeout
    try:
        log(f"[Server] Connected to {addr}")
        reg = conn.recv(1024).decode(errors="replace")
        name, typ = parse_registration(reg)
        if not name:
            log(f"[Server] Invalid registration from {addr}: {reg!r}")
            conn.close()
            return

        with devices_lock:
            devices[name] = {"type": typ, "addr": addr, "conn": conn}

        log(f"[Server] Registered DEVICE={name} TYPE={typ}")

        # keep listening for ACKs or any messages from this device
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    log(f"[Server] {name} disconnected.")
                    break
                msg = data.decode(errors="replace").strip()
                log(f"[Server] From {name}: {msg}")
            except socket.timeout:
                # just loop to keep connection alive
                continue
            except ConnectionResetError:
                log(f"[Server] {name} connection reset.")
                break
    finally:
        with devices_lock:
            # remove if still present
            for k, v in list(devices.items()):
                if v["conn"] is conn:
                    devices.pop(k, None)
        try:
            conn.close()
        except Exception:
            pass

def accept_loop():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    log(f"[Server] Listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    finally:
        server.close()

def command_loop():
    help_text = (
        "Commands:\n"
        "  list                         -> show connected devices\n"
        "  send <device> <text...>      -> send a command string to one device\n"
        "  broadcast <text...>          -> send to all devices\n"
        "  help                         -> show this help\n"
        "  quit                         -> stop server\n"
    )
    print(help_text)
    while True:
        try:
            line = input("hub> ").strip()
        except (EOFError, KeyboardInterrupt):
            line = "quit"
        if not line:
            continue
        if line == "help":
            print(help_text)
        elif line == "list":
            with devices_lock:
                if not devices:
                    print("(no devices)")
                else:
                    for name, info in devices.items():
                        print(f"- {name} (type={info['type']}, addr={info['addr']})")
        elif line.startswith("send "):
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                print("usage: send <device> <text...>")
                continue
            target, text = parts[1], parts[2]
            with devices_lock:
                info = devices.get(target)
            if not info:
                print(f"device {target!r} not found")
                continue
            try:
                info["conn"].sendall(text.encode())
                log(f"[Server] Sent to {target}: {text!r}")
            except Exception as e:
                log(f"[Server] Error sending to {target}: {e}")
        elif line.startswith("broadcast "):
            text = line[len("broadcast "):]
            with devices_lock:
                items = list(devices.items())
            for name, info in items:
                try:
                    info["conn"].sendall(text.encode())
                    log(f"[Server] Broadcast to {name}: {text!r}")
                except Exception as e:
                    log(f"[Server] Error sending to {name}: {e}")
        elif line in ("quit", "exit"):
            log("[Server] Shutting down on user request.")
            break
        else:
            print("unknown command. type 'help'.")

def main():
    # clear old log for a fresh run
    open(LOG_FILE, "w", encoding="utf-8").close()
    t = threading.Thread(target=accept_loop, daemon=True)
    t.start()
    # run the interactive command loop in the main thread
    command_loop()

if __name__ == "__main__":
    main()
