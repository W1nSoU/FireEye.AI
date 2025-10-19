import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QStackedLayout
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QCamera, QCameraInfo, QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QCameraViewfinder, QVideoWidget

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firelink Ground Control")
        self.setGeometry(100, 100, 1280, 720)

        self.init_style()
        self.init_camera()

        self.central_layout = QStackedLayout(self)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        # Віджет для камери
        self.viewfinder = QCameraViewfinder()
        self.central_layout.addWidget(self.viewfinder)

        # Основний віджет з інтерфейсом
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: transparent;")
        self.layout = QHBoxLayout(main_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.central_layout.addWidget(main_widget)


        # Ліва панель
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        left_layout = QVBoxLayout(left_panel)
        self.layout.addWidget(left_panel, 1) # 1/3 ширини

        # Права панель
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        right_layout = QVBoxLayout(right_panel)
        self.layout.addWidget(right_panel, 2) # 2/3 ширини

        # Віджет для тепловізійної камери
        self.thermal_viewfinder = QCameraViewfinder()
        right_layout.addWidget(self.thermal_viewfinder, 1)

        # Секція телеметрії
        telemetry_group = QGroupBox("Telemetry")
        telemetry_group.setStyleSheet("color: white; font-weight: bold;")
        telemetry_layout = QVBoxLayout()
        self.telemetry_labels = {
            'lat': QLabel("Lat: N/A"), 'lon': QLabel("Lon: N/A"), 'alt': QLabel("Alt: N/A"),
            'heading': QLabel("Heading: N/A"), 'yaw': QLabel("Yaw: N/A")
        }
        for label in self.telemetry_labels.values():
            label.setStyleSheet("color: white;")
            telemetry_layout.addWidget(label)
        telemetry_group.setLayout(telemetry_layout)
        left_layout.addWidget(telemetry_group)

        # Секція статусу
        status_group = QGroupBox("Status")
        status_group.setStyleSheet("color: white; font-weight: bold;")
        status_layout = QVBoxLayout()
        self.connection_status_label = QLabel("Connection Status: Disconnected")
        self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.connection_status_label)
        status_group.setLayout(status_layout)
        left_layout.addWidget(status_group)
        left_layout.addStretch(1)


        # Секція управління
        controls_group = QGroupBox("Controls")
        controls_group.setStyleSheet("color: white; font-weight: bold;")
        controls_layout = QHBoxLayout()
        self.simulate_fire_button = QPushButton("Simulate Fire")
        self.send_statustext_button = QPushButton("Send STATUSTEXT")
        controls_layout.addWidget(self.simulate_fire_button)
        controls_layout.addWidget(self.send_statustext_button)
        controls_group.setLayout(controls_layout)
        right_layout.addWidget(controls_group)

        # Секція логів
        log_group = QGroupBox("MAVLink Log")
        log_group.setStyleSheet("color: white; font-weight: bold;")
        log_layout = QVBoxLayout()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("background-color: #2E2E2E; color: white;")
        log_layout.addWidget(self.log_text_edit)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

    def update_telemetry(self, telemetry):
        """Оновлює відображення телеметрії."""
        for key, label in self.telemetry_labels.items():
            value = telemetry.get(key)
            if value is not None:
                # Форматуємо координати з більшою точністю
                if key in ['lat', 'lon']:
                    label.setText(f"{key.capitalize()}: {value:.7f}")
                else:
                    label.setText(f"{key.capitalize()}: {value:.2f}")

    def update_connection_status(self, is_connected, is_simulation=False):
        """Оновлює статус з'єднання."""
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

        self.connection_status_label.setText(f"Connection Status: {status}")
        self.connection_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def log_message(self, message):
        """Додає повідомлення до логу GUI."""
        self.log_text_edit.append(message)

    def init_style(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(palette)

        # Встановлюємо глобальний шрифт
        font = QFont("Arial", 10)
        QApplication.setFont(font)

    def init_camera(self):
        cameras = QCameraInfo.availableCameras()
        if not cameras:
            print("No cameras found. Starting video emulation.")
            self.emulate_video()
            return

        # Основна камера
        self.camera = QCamera(cameras[0])
        self.camera.setViewfinder(self.viewfinder)
        self.camera.start()

        # Тепловізійна камера (якщо доступна)
        if len(cameras) > 1:
            self.thermal_camera = QCamera(cameras[1])
            self.thermal_camera.setViewfinder(self.thermal_viewfinder)
            self.thermal_camera.start()
        else:
            self.emulate_thermal_video()

    def emulate_video(self):
        self.central_layout.removeWidget(self.viewfinder)
        self.viewfinder.deleteLater()
        self.viewfinder = None

        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        video_widget = QVideoWidget()
        self.central_layout.insertWidget(0, video_widget)
        self.player.setVideoOutput(video_widget)

        video_path = os.path.join("video", "cam")
        if os.path.exists(video_path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(video_path))))
            self.player.play()
        else:
            print(f"Video file not found: {video_path}")

        self.emulate_thermal_video()

    def emulate_thermal_video(self):
        right_layout = self.layout.itemAt(1).widget().layout()
        right_layout.removeWidget(self.thermal_viewfinder)
        self.thermal_viewfinder.deleteLater()
        self.thermal_viewfinder = None

        self.thermal_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        thermal_video_widget = QVideoWidget()
        right_layout.insertWidget(0, thermal_video_widget)
        self.thermal_player.setVideoOutput(thermal_video_widget)

        video_path = os.path.join("video", "teplo")
        if os.path.exists(video_path):
            self.thermal_player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(video_path))))
            self.thermal_player.play()
        else:
            print(f"Video file not found: {video_path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
