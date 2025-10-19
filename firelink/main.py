import sys
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from firelink.core.mavlink_service import MavlinkService
from firelink.core.log_service import LogService
from firelink.gui.main_window import MainWindow
from firelink.config.settings import config

class FirelinkApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.mav_service = MavlinkService(simulation=config.get('debug', True))
        self.log_service = LogService()

        self._connect_signals()

        # Таймер для оновлення телеметрії
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self._update_telemetry)

    def _connect_signals(self):
        """Підключає сигнали до слотів."""
        self.window.simulate_fire_button.clicked.connect(self._simulate_fire)
        self.window.send_statustext_button.clicked.connect(self._send_statustext)

    def _update_telemetry(self):
        """Оновлює дані телеметрії в GUI та логує їх."""
        telemetry = self.mav_service.get_telemetry()
        self.window.update_telemetry(telemetry)
        # Не логуємо симульовану телеметрію
        if not self.mav_service.simulation:
            self.log_service.log_telemetry(telemetry)

    def _simulate_fire(self):
        """Обробник для кнопки симуляції пожежі."""
        message = "Fire simulation requested!"
        self.window.log_message(message)
        self.log_service.log_event("fire_simulation", {"source": "gui"})
        print(message)
        self._send_statustext()

    def _send_statustext(self):
        """Запускає відправку координат в окремому потоці."""
        thread = threading.Thread(target=self._send_fire_coords_thread, daemon=True)
        thread.start()

    def _send_fire_coords_thread(self):
        telemetry = self.mav_service.get_telemetry()
        lat = telemetry.get('lat')
        lon = telemetry.get('lon')

        if lat is None or lon is None:
            message = "Error: Cannot send coordinates. Telemetry data is missing."
            self.window.log_message(message)
            self.log_service.log_event("send_coords_error", {"reason": "missing_telemetry"})
            print(message)
            return

        alt = telemetry.get('alt', 150.0)
        confidence = config.get('fire_confidence_threshold', 0.7)
        success = self.mav_service.send_fire_coords(lat, lon, alt, confidence)

        log_data = {"lat": lat, "lon": lon, "alt": alt, "confidence": confidence}
        if success:
            log_data["status"] = "acknowledged"
            self.log_service.log_event("fire_coords_sent", log_data)
            self.window.log_message(f"Fire coords sent and ACKed: {log_data}")
        else:
            log_data["status"] = "not_acknowledged"
            self.log_service.log_event("fire_coords_failed", log_data)
            self.window.log_message(f"Failed to send fire coords: {log_data}")

    def run(self):
        """Запускає додаток."""
        self.mav_service.connect()
        self.window.update_connection_status(self.mav_service.is_connected)

        if self.mav_service.is_connected:
            self.telemetry_timer.start(1000)
        else:
            self.window.log_message("Connection to Pixhawk failed.")

        self.window.show()

        exit_code = self.app.exec_()

        self.mav_service.close()
        self.log_service.close()

        sys.exit(exit_code)

if __name__ == "__main__":
    firelink = FirelinkApp()
    firelink.run()
