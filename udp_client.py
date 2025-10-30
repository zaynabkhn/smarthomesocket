# udp_client.py
import socket
import time
import random
from datetime import datetime

HOST = "127.0.0.1"
PORT = 6060

DEVICE_NAME = "Sensor01"        # change if running multiple
SENSOR_TYPE = "temperature"     # temperature | humidity | motion
INTERVAL_SEC = 1.0              # send period
CYCLE_SIZE = 10                 # packets per cycle (must match server)

# >>> Toggle to simulate a lost packet.
# Set to an integer 1..CYCLE_SIZE to skip that SEQ, or set to None for normal runs.
DROP_SEQ = None   # e.g., 7; set to None when done demonstrating loss

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_sensor_value():
    # simple simulation: temperature 22.0–28.0 C
    return f"{random.uniform(22.0, 28.0):.1f}"

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)  # wait up to 5s for the status ack after a cycle

    try:
        # ---- send one cycle of sequenced packets 1..CYCLE_SIZE ----
        for seq in range(1, CYCLE_SIZE + 1):
            if DROP_SEQ is not None and seq == DROP_SEQ:
                print(f"[{DEVICE_NAME}] (simulating loss) SKIP SEQ:{seq}")
                time.sleep(INTERVAL_SEC)
                continue

            ts = now_str()
            value = read_sensor_value()
            packet = f"{DEVICE_NAME},{ts},{SENSOR_TYPE},{value},SEQ:{seq}"
            sock.sendto(packet.encode(), (HOST, PORT))
            print(f"[{DEVICE_NAME}] Sending packet SEQ:{seq} — {SENSOR_TYPE}={value}")
            time.sleep(INTERVAL_SEC)

        # ---- wait for server status ack (with simple retry) ----
        MAX_RETRIES = 2
        attempt = 0
        status_ok = False
        while attempt <= MAX_RETRIES and not status_ok:
            try:
                status, addr = sock.recvfrom(4096)
                msg = status.decode(errors="replace").strip()
                print(f"[{DEVICE_NAME}] {msg}")
                status_ok = True
            except socket.timeout:
                attempt += 1
                if attempt <= MAX_RETRIES:
                    print(f"[{DEVICE_NAME}] No STATUS received, retrying request ({attempt}/{MAX_RETRIES}) ...")
                    # re-announce the last packet to poke the server (still marks end-of-cycle)
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    packet = f"{DEVICE_NAME},{ts},{SENSOR_TYPE},{read_sensor_value()},SEQ:{CYCLE_SIZE}"
                    sock.sendto(packet.encode(), (HOST, PORT))
                else:
                    print(f"[{DEVICE_NAME}] No STATUS received after retries.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
