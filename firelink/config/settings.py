import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    """Завантажує конфігурацію з файлу YAML."""
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Файл конфігурації не знайдено: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

# Завантажуємо конфігурацію при імпорті модуля
config = load_config()
