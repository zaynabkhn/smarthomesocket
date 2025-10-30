# udp_server.py
import socket
from datetime import datetime

HOST = "127.0.0.1"
PORT = 6060
LOG_FILE = "sensor_data_log.txt"

CYCLE_SIZE = 10  # number of packets per cycle required for a status ack

# Per-device state: device_id -> {"addr": (ip,port), "seqs": set[int]}
device_state = {}

def log(msg: str):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_packet(raw: str):
    """
    Expected format:
      Sensor01,2025-10-22 18:20:15,temperature,24.8,SEQ:5
    Returns: (device_id, timestamp_str, sensor_type, value_str, seq_int) or (None,...)
    """
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) < 5:
        return None, None, None, None, None
    device_id = parts[0]
    ts = parts[1]
    sensor_type = parts[2]
    value = parts[3]
    seq_part = parts[4]
    if not seq_part.upper().startswith("SEQ:"):
        return None, None, None, None, None
    try:
        seq = int(seq_part.split(":", 1)[1])
    except ValueError:
        return None, None, None, None, None
    return device_id, ts, sensor_type, value, seq

def send_status(sock, dev):
    st = device_state.get(dev)
    if not st:
        return
    expected = set(range(1, CYCLE_SIZE + 1))
    got = st["seqs"]
    missing = sorted(expected - got)
    count_ok = CYCLE_SIZE - len(missing)
    status = f"STATUS RECEIVED {count_ok}/{CYCLE_SIZE} PACKETS"
    sock.sendto(status.encode(), st["addr"])
    log(f"[UDP-Server] Sent to {dev}: {status}")
    if missing:
        log(f"[UDP-Server] Missing SEQ for {dev}: {missing}")
    # reset for next cycle
    st["seqs"] = set()

def main():
    # clear the log for a fresh run
    open(LOG_FILE, "w", encoding="utf-8").close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    log(f"[UDP-Server] Listening on {HOST}:{PORT}")

    try:
        while True:
            data, addr = sock.recvfrom(4096)  # blocking wait
            raw = data.decode(errors="replace").strip()

            dev, ts, typ, val, seq = parse_packet(raw)
            if dev is None:
                log(f"[UDP-Server] Invalid packet from {addr}: {raw!r}")
                continue

            st = device_state.setdefault(dev, {"addr": addr, "seqs": set()})
            st["addr"] = addr
            st["seqs"].add(seq)

            log(f"[UDP-Server] RX from {dev} @ {addr}: ts={ts}, type={typ}, value={val}, SEQ={seq}")

            # End-of-cycle conditions:
            # - Got 10 unique seqs (all arrived) OR
            # - received SEQ == 10 (cycle ended even if some are missing)
            if len(st["seqs"]) >= CYCLE_SIZE or seq == CYCLE_SIZE:
                send_status(sock, dev)

    except KeyboardInterrupt:
        log("[UDP-Server] Shutting down (KeyboardInterrupt).")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
