import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Firelink Debug GUI")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout(self)

        # Секція телеметрії
        telemetry_group = QGroupBox("Telemetry")
        telemetry_layout = QVBoxLayout()
        self.telemetry_labels = {
            'lat': QLabel("Lat: N/A"), 'lon': QLabel("Lon: N/A"), 'alt': QLabel("Alt: N/A"),
            'heading': QLabel("Heading: N/A"), 'yaw': QLabel("Yaw: N/A")
        }
        for label in self.telemetry_labels.values():
            telemetry_layout.addWidget(label)
        telemetry_group.setLayout(telemetry_layout)
        self.layout.addWidget(telemetry_group)

        # Секція статусу
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.connection_status_label = QLabel("Connection Status: Disconnected")
        status_layout.addWidget(self.connection_status_label)
        status_group.setLayout(status_layout)
        self.layout.addWidget(status_group)

        # Секція управління
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()
        self.simulate_fire_button = QPushButton("Simulate Fire")
        self.send_statustext_button = QPushButton("Send STATUSTEXT")
        controls_layout.addWidget(self.simulate_fire_button)
        controls_layout.addWidget(self.send_statustext_button)
        controls_group.setLayout(controls_layout)
        self.layout.addWidget(controls_group)

        # Секція логів
        log_group = QGroupBox("MAVLink Log")
        log_layout = QVBoxLayout()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        log_group.setLayout(log_layout)
        self.layout.addWidget(log_group)

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
                color = "blue"
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
