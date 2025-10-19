import csv
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from firelink.config.settings import config

class LogService:
    def __init__(self):
        self.log_dir = Path(config.get('log_dir', '/home/jetson/firelink/logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)

        #  логгер телеметрії (CSV)
        self.telemetry_log_path = self.log_dir / "telemetry.csv"
        self._setup_telemetry_logger()

        # логгер подій (JSON)
        self.event_log_path = self.log_dir / "events.json"
        self.event_logger = self._setup_event_logger()

    def _setup_telemetry_logger(self):
        """Налаштовує логгер для телеметрії у форматі CSV."""
        file_exists = self.telemetry_log_path.is_file()
        self.telemetry_file = open(self.telemetry_log_path, 'a', newline='')
        self.telemetry_writer = csv.writer(self.telemetry_file)
        if not file_exists:
            self.telemetry_writer.writerow(['timestamp', 'lat', 'lon', 'alt', 'heading', 'yaw', 'pitch', 'roll'])

    def _setup_event_logger(self):
        """Налаштовує логгер для подій у форматі JSON."""
        handler = RotatingFileHandler(self.event_log_path, maxBytes=10*1024*1024, backupCount=10)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        logger = logging.getLogger('EventLogger')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    def log_telemetry(self, telemetry_data):
        """Записує дані телеметрії у CSV файл."""
        timestamp = datetime.utcnow().isoformat()
        row = [
            timestamp,
            telemetry_data.get('lat'),
            telemetry_data.get('lon'),
            telemetry_data.get('alt'),
            telemetry_data.get('heading'),
            telemetry_data.get('yaw'),
            telemetry_data.get('pitch'),
            telemetry_data.get('roll')
        ]
        self.telemetry_writer.writerow(row)
        self.telemetry_file.flush()

    def log_event(self, event_type, data):
        """Записує подію у JSON файл."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.event_logger.info(json.dumps(log_entry))

    def close(self):
        """Закриває файли логів."""
        if hasattr(self, 'telemetry_file') and not self.telemetry_file.closed:
            self.telemetry_file.close()
        #  логгери подій закриваються автоматично
