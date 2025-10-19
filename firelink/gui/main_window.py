import sys
import os
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QScrollArea, QFrame
from PyQt5.QtGui import QPalette, QColor, QFont, QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, QSize
from firelink.config.settings import config

class VideoPlayer(QWidget):
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame_slot)
        self.timer.start(30)  # 30 ms ~ 33 FPS

    def next_frame_slot(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pix = QPixmap.fromImage(qt_image).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label.setPixmap(pix)
            else:
                # Loop video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def resizeEvent(self, event):
        self.label.resize(self.size())
        super().resizeEvent(event)

    def close(self):
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        super().close()

class DroneStatusCard(QFrame):
    def __init__(self, drone_id="N/A", parent=None):
        super().__init__(parent)
        self.setObjectName("droneCard")
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
        self.setStyleSheet("""
            QFrame#droneCard {
                background-color: rgba(30, 30, 30, 0.85);
                border-radius: 10px;
                border: 1px solid #444;
                color: white;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QLabel {
                color: #ddd;
            }
            QLabel.title {
                font-weight: bold;
                font-size: 14px;
                color: #00c8ff;
            }
            QLabel.status {
                font-weight: bold;
                color: #00ff94;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(6)

        self.id_label = QLabel(f"ID: {drone_id}")
        self.id_label.setObjectName("title")
        self.id_label.setProperty("class", "title")
        self.status_label = QLabel("Status: FIRE DETECTED")
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setProperty("class", "status")
        self.coords_label = QLabel("Coordinates: 50.45115" \
        ", -104.61719, 153.40201")
        self.altitude_label = QLabel("Altitude: 35.4 m")
        self.speed_label = QLabel("Speed: 5.4 km/h")
        self.battery_label = QLabel("Battery: 63 %")
        self.temperature_label = QLabel("Temperature: 23 °C")
        self.gps_signal_label = QLabel("GPS Signal: <font color='green'><b>Good</b></font>")

        layout.addWidget(self.id_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.coords_label)
        layout.addWidget(self.altitude_label)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.battery_label)
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.gps_signal_label)
        layout.addStretch(1)

    def update_status(self, data: dict):
        self.id_label.setText(f"ID: {data.get('id', 'N/A')}")
        self.status_label.setText(f"Status: {data.get('status', 'N/A')}")
        lat = data.get('lat')
        lon = data.get('lon')
        if lat is not None and lon is not None:
            self.coords_label.setText(f"Coordinates: {lat:.7f}, {lon:.7f}")
        else:
            self.coords_label.setText("Coordinates: N/A")
        alt = data.get('alt')
        if alt is not None:
            self.altitude_label.setText(f"Altitude: {alt:.2f} m")
        else:
            self.altitude_label.setText("Altitude: N/A")
        speed = data.get('speed')
        if speed is not None:
            self.speed_label.setText(f"Speed: {speed:.2f} m/s")
        else:
            self.speed_label.setText("Speed: N/A")
        battery = data.get('battery')
        if battery is not None:
            self.battery_label.setText(f"Battery: {battery:.1f} %")
        else:
            self.battery_label.setText("Battery: N/A")
        temp = data.get('temperature')
        if temp is not None:
            self.temperature_label.setText(f"Temperature: {temp:.1f} °C")
        else:
            self.temperature_label.setText("Temperature: N/A")
        gps_signal = data.get('gps_signal')
        if gps_signal is not None:
            self.gps_signal_label.setText(f"GPS Signal: {gps_signal}")
        else:
            self.gps_signal_label.setText("GPS Signal: N/A")

class InfoCard(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1.5px solid #888;
                border-radius: 8px;
                margin-top: 10px;
                background-color: #f5f5f5;
                color: #222;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
            }
            QLabel {
                color: #333;
                font-size: 13px;
            }
            QPushButton {
                background-color: #007ACC;
                border: none;
                color: white;
                padding: 6px 12px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-family: Consolas, monospace;
                font-size: 12px;
                color: #222;
            }
        """)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firelink Ground Control")
        self.setGeometry(100, 100, 1280, 720)
        self.init_style()

        # Main 
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel: Drone status vertical scroll area
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        self.left_panel.setStyleSheet("""
            QWidget#leftPanel {
                background-color: #121212;
            }
        """)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        self.scroll_content.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_content)
        left_layout.addWidget(self.scroll_area)

        # drone card 
        self.drone_cards = {}
        self.add_drone_card("FireScan-X1")

        # Right panel: Controls and info cards
        self.right_panel = QWidget()
        self.right_panel.setObjectName("rightPanel")
        self.right_panel.setStyleSheet("""
            QWidget#rightPanel {
                background-color: #f0f0f0;
                border-left: 1px solid #ccc;
            }
        """)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)

        # Camera Control card
        self.camera_control_card = InfoCard("Camera Control")
        camera_layout = QVBoxLayout()
        self.simulate_fire_button = QPushButton("Simulate Fire")
        camera_layout.addWidget(self.simulate_fire_button)
        self.camera_control_card.setLayout(camera_layout)
        right_layout.addWidget(self.camera_control_card)

        # Telemetry card
        self.telemetry_card = InfoCard("Telemetry")
        telemetry_layout = QVBoxLayout()
        self.telemetry_labels = {
            'lat': QLabel("Lat: N/A"),
            'lon': QLabel("Lon: N/A"),
            'alt': QLabel("Alt: N/A"),
            'heading': QLabel("Heading: N/A"),
            'yaw': QLabel("Yaw: N/A"),
        }
        for label in self.telemetry_labels.values():
            telemetry_layout.addWidget(label)
        self.telemetry_card.setLayout(telemetry_layout)
        right_layout.addWidget(self.telemetry_card)

        # Actions card
        self.actions_card = InfoCard("Actions")
        actions_layout = QHBoxLayout()
        self.send_statustext_button = QPushButton("Send STATUSTEXT")
        actions_layout.addWidget(self.send_statustext_button)
        self.actions_card.setLayout(actions_layout)
        right_layout.addWidget(self.actions_card)

        # Log card
        self.log_card = InfoCard("MAVLink Log")
        log_layout = QVBoxLayout()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        self.log_card.setLayout(log_layout)
        right_layout.addWidget(self.log_card)

        right_layout.addStretch(1)

        # Central widget: video background
        self.video_widget = QWidget()
        self.video_widget.setObjectName("videoWidget")
        self.video_widget.setStyleSheet("background-color: black;")
        video_layout = QVBoxLayout(self.video_widget)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)

        self.main_video_player = None
        main_video_path = self.find_video_file("cam")
        if main_video_path:
            self.main_video_player = VideoPlayer(main_video_path)
            video_layout.addWidget(self.main_video_player)
        else:
            # If no video found, just a black placeholder
            placeholder = QLabel("Main video not found")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: white; font-size: 18px;")
            video_layout.addWidget(placeholder)

        # Thermal video small window overlay
        self.thermal_video_player = None
        thermal_video_path = self.find_video_file("teplo")
        if thermal_video_path:
            self.thermal_video_player = VideoPlayer(thermal_video_path, self.video_widget)
            self.thermal_video_player.setFixedSize(320, 180)
            self.thermal_video_player.setStyleSheet("border: 2px solid #00c8ff; border-radius: 8px; background-color: black;")
            self.thermal_video_player.move(self.video_widget.width() - self.thermal_video_player.width() - 20, 20)
            self.thermal_video_player.raise_()
            self.thermal_video_player.show()
            self.video_widget.resizeEvent = self.on_video_widget_resize
        else:
            self.thermal_video_player = None

        # Add widgets to main layout
        main_layout.addWidget(self.left_panel, 3)
        main_layout.addWidget(self.video_widget, 7)
        main_layout.addWidget(self.right_panel, 3)

    def on_video_widget_resize(self, event):
        if self.thermal_video_player:
            self.thermal_video_player.move(self.video_widget.width() - self.thermal_video_player.width() - 20, 20)
        event.accept()

    def add_drone_card(self, drone_id):
        if drone_id not in self.drone_cards:
            card = DroneStatusCard(drone_id)
            self.scroll_layout.addWidget(card)
            self.drone_cards[drone_id] = card

    def update_drone_status(self, data: dict):
        # data should contain 'id' key to identify drone card
        drone_id = data.get('id')
        if not drone_id:
            return
        if drone_id not in self.drone_cards:
            self.add_drone_card(drone_id)
        self.drone_cards[drone_id].update_status(data)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.thermal_video_player:
            self.thermal_video_player.move(self.video_widget.width() - self.thermal_video_player.width() - 20, 20)

    def update_telemetry(self, telemetry):
        """Оновлює відображення телеметрії."""
        for key, label in self.telemetry_labels.items():
            value = telemetry.get(key)
            if value is not None:
                
                if key in ['lat', 'lon']:
                    label.setText(f"{key.capitalize()}: {value:.7f}")
                else:
                    label.setText(f"{key.capitalize()}: {value:.2f}")

    def update_connection_status(self, is_connected, is_simulation=False):
        """Оновлює статус з'єднання у логах."""
        if is_connected:
            if is_simulation:
                status = "Connected (Simulation)"
                color = "RoyalBlue"
            else:
                status = "Connected"
                color = "green"
        else:
            status = "Disconnected"
            color = "red"

        self.log_message(f"<b style='color:{color};'>Connection Status: {status}</b>")

    def log_message(self, message):
        """Додає повідомлення до логу GUI."""
        self.log_text_edit.append(message)

    def init_style(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(18, 18, 18))
        self.setPalette(palette)

        
        font = QFont("Segoe UI", 10)
        QApplication.setFont(font)

    def closeEvent(self, event):
        if self.main_video_player:
            self.main_video_player.close()
        if self.thermal_video_player:
            self.thermal_video_player.close()
        event.accept()

    @staticmethod
    def find_video_file(base_name):
        """Знаходить відеофайл у папці video, ігноруючи розширення."""
        video_dir = "video"
        if not os.path.isdir(video_dir):
            return None
        
        supported_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webp']
        for filename in os.listdir(video_dir):
            if filename.startswith(base_name):
                for ext in supported_extensions:
                    if filename.endswith(ext):
                        return os.path.join(video_dir, filename)
        return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
