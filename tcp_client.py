# tcp_client.py
import socket
import time
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5050

DEVICE_NAME = "Sensor01"     # change per client run
DEVICE_TYPE = "temperature"  # temperature / humidity / motion etc.

def simulate_execution(cmd: str):
    # simple simulation logic
    parts = cmd.strip().split()
    if not parts:
        return "No command"
    if parts[0].upper() == "SET_INTERVAL" and len(parts) >= 2:
        return f"{DEVICE_NAME}: interval set to {parts[1]}s"
    if parts[0].upper() == "ACTIVATE_ALARM":
        return f"{DEVICE_NAME}: Alarm activated"
    return f"{DEVICE_NAME}: Executed '{cmd}'"

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(None)

    print(f"[{DEVICE_NAME}] Connecting to {HOST}:{PORT} ...")
    client.connect((HOST, PORT))
    print(f"[{DEVICE_NAME}] Connected")

    # send registration
    reg = f"DEVICE {DEVICE_NAME} TYPE {DEVICE_TYPE}"
    client.sendall(reg.encode())
    print(f"[{DEVICE_NAME}] Sent registration: {reg}")

    # listen for commands forever
    try:
        while True:
            data = client.recv(1024)
            if not data:
                print(f"[{DEVICE_NAME}] Server closed connection.")
                break
            cmd = data.decode(errors="replace").strip()
            print(f"[{DEVICE_NAME}] Received command: {cmd!r}")

            result = simulate_execution(cmd)
            print(f"[{DEVICE_NAME}] {result}")

            ack = "ACK Command Executed"
            client.sendall(ack.encode())
            print(f"[{DEVICE_NAME}] Sent ACK")
    except (ConnectionResetError, ConnectionAbortedError, TimeoutError) as e:
        print(f"[{DEVICE_NAME}] Connection error: {e}")
    finally:
        client.close()
        print(f"[{DEVICE_NAME}] Closed")

if __name__ == "__main__":
    main()
