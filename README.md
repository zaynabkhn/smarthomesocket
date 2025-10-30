# Smart Home Monitoring & Control System (Socket Programming)

### Overview
This project simulates a smart home environment where IoT devices communicate with a central Smart Hub using both TCP and UDP socket programming in Python.

- **TCP:** Used for reliable device registration and command exchange.
- **UDP:** Used for real-time sensor data streaming with sequence tracking and acknowledgment.

### Files
| File | Description |
|------|--------------|
| `tcp_server.py` | Smart Hub (TCP) — handles device registration, commands, ACKs |
| `tcp_client.py` | IoT Device (TCP) — registers and executes commands |
| `udp_server.py` | Smart Hub (UDP) — collects sensor data, detects missing packets |
| `udp_client.py` | IoT Device (UDP) — sends sequenced sensor data packets |
| `server_log.txt` | Sample log of TCP interactions |
| `sensor_data_log.txt` | Sample log of UDP packet transmissions |
| `report.pdf` | Full project documentation with screenshots |

### Features
- Reliable TCP command exchange
- Real-time UDP streaming
- Error handling and retry logic
- Logging and packet loss detection
- Demonstrates difference between reliability and speed in networking

### How to Run
```bash
# TCP Demo
python tcp_server.py
python tcp_client.py

# UDP Demo
python udp_server.py
python udp_client.py
