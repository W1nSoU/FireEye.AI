import threading
import time
import math
import json
from pymavlink import mavutil
from firelink.config.settings import config

class MavlinkService:
    def __init__(self, simulation=False):
        self.port = config['pixhawk']['port']
        self.baud = config['pixhawk']['baud']
        self.recon_sysid = config['sys']['recon_sysid']
        self.recon_compid = config['sys']['recon_compid']
        self.operator_sysid = config['sys']['operator_sysid']
        self.conn = None
        self.is_connected = False
        self.simulation = simulation
        self.telemetry = {
            'lat': 50.4501, 'lon': 30.5234, 'alt': 150.0,
            'heading': 0, 'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0
        }
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.ack_received = threading.Event()

    def connect(self):
        """Встановлює з'єднання з Pixhawk або запускає симуляцію."""
        if self.simulation:
            self.is_connected = True
            print("Running in simulation mode.")
            self.thread.start()
            return
        try:
            self.conn = mavutil.mavlink_connection(self.port, baud=self.baud,
                                                   source_system=self.recon_sysid,
                                                   source_component=self.recon_compid)
            self.conn.wait_heartbeat()
            self.is_connected = True
            print("Pixhawk connected!")
            self.thread.start()
        except Exception as e:
            self.is_connected = False
            print(f"Failed to connect to Pixhawk: {e}")

    def _run(self):
        """Основний цикл для отримання MAVLink повідомлень або симуляції."""
        if self.simulation:
            while self.is_connected:
                self._simulate_telemetry()
                time.sleep(1)
        else:
            while self.is_connected:
                try:
                    msg = self.conn.recv_match(blocking=True, timeout=1)
                    if msg:
                        self._handle_message(msg)
                except Exception as e:
                    print(f"Error while receiving MAVLink message: {e}")
                    self.is_connected = False

    def _handle_message(self, msg):
        """Обробляє вхідні MAVLink повідомлення."""
        msg_type = msg.get_type()
        if msg_type == 'GLOBAL_POSITION_INT':
            self.telemetry['lat'] = msg.lat / 1e7
            self.telemetry['lon'] = msg.lon / 1e7
            self.telemetry['alt'] = msg.alt / 1000
        elif msg_type == 'VFR_HUD':
            self.telemetry['heading'] = msg.heading
        elif msg_type == 'ATTITUDE':
            self.telemetry['yaw'] = math.degrees(msg.yaw)
            self.telemetry['pitch'] = math.degrees(msg.pitch)
            self.telemetry['roll'] = math.degrees(msg.roll)
        elif msg_type == 'STATUSTEXT':
            if "FIRE_RECEIVED" in msg.text:
                print("ACK received from operator!")
                self.ack_received.set()

    def _simulate_telemetry(self):
        self.telemetry['lat'] += 0.00001
        self.telemetry['lon'] += 0.00001
        self.telemetry['alt'] = 150 + 10 * math.sin(time.time())
        self.telemetry['heading'] = (self.telemetry['heading'] + 1) % 360
        self.telemetry['yaw'] = 15 * math.sin(time.time())

    def get_telemetry(self):
        return self.telemetry

    def send_fire_coords(self, lat, lon, alt, confidence):
        """Формує та відправляє координати пожежі з логікою повторних спроб."""
        payload = {
            "type": "fire_coords", "lat": lat, "lon": lon, "alt": alt,
            "confidence": confidence, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        text = json.dumps(payload)

        retry_count = config['retry_count']
        backoff_intervals = config['retry_backoff']

        for i in range(retry_count):
            print(f"Sending fire coordinates (attempt {i+1}/{retry_count}): {text}")
            if not self.simulation:
                self.conn.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_WARNING, text.encode('utf-8'))
            else:
                print("STATUSTEXT not sent in simulation mode.")

            self.ack_received.clear()
            ack_was_set = self.ack_received.wait(timeout=backoff_intervals[i])

            if ack_was_set:
                print("Successfully sent fire coordinates and received ACK.")
                return True
            else:
                print(f"No ACK received. Retrying after {backoff_intervals[i]} seconds...")

        print("Failed to send fire coordinates after multiple retries.")
        return False

    def close(self):
        self.is_connected = False
        if self.thread.is_alive():
            self.thread.join()
        if self.conn:
            self.conn.close()
        print("Mavlink connection closed.")
