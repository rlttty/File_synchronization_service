import os
from dotenv import dotenv_values


# def load_config():
"""Загружает конфигурацию из файла .env и проверяет её."""
if not os.path.exists(".env"):
    raise ValueError("Файл .env не найден")

config = dotenv_values(".env")

local_folder = config.get("LOCAL_FOLDER")
cloud_folder = config.get("CLOUD_FOLDER")
token = config.get("YANDEX_TOKEN")
sync_interval = config.get("SYNC_INTERVAL")
log_file = config.get("LOG_FILE")

if not local_folder or not os.path.isdir(local_folder):
    raise ValueError("Invalid or missing LOCAL_FOLDER in .env")
if not cloud_folder:
    raise ValueError("Missing CLOUD_FOLDER in .env")
if not token:
    raise ValueError("Missing YANDEX_TOKEN in .env")
if not sync_interval or not sync_interval.isdigit():
    raise ValueError("Invalid or missing SYNC_INTERVAL in .env")
if not log_file:
    raise ValueError("Missing LOG_FILE in .env")

config_dict = {
    "local_folder": local_folder,
    "cloud_folder": cloud_folder,
    "token": token,
    "sync_interval": int(sync_interval),
    "log_file": log_file
}