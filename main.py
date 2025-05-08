import os
import time
import configparser
from pathlib import Path
from typing import Optional
from loguru import logger
from dotenv import dotenv_values
from yandex_disk import YandexDisk
import hashlib


def setup_config() -> Optional[dict]:
    """Читает конфигурацию из config.ini и .env."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    if not config.has_section("Settings"):
        print("Error: config.ini is missing [Settings] section")
        return None

    settings = config["Settings"]
    env = dotenv_values(".env")

    result = {
        "local_folder": settings.get("local_folder"),
        "cloud_folder": settings.get("cloud_folder"),
        "sync_interval": settings.getint("sync_interval", 60),
        "log_file": settings.get("log_file", "sync.log"),
        "token": env.get("YANDEX_TOKEN")
    }

    if not result["local_folder"] or not os.path.isdir(result["local_folder"]):
        print(f"Error: Invalid or missing local_folder: {result['local_folder']}")
        return None
    if not result["token"]:
        print("Error: Missing YANDEX_TOKEN in .env")
        return None

    return result


def setup_logger(log_file: str) -> None:
    """Настраивает логгер."""
    logger.remove()
    logger.add(log_file, format="{time} | {level} | {message}", level="INFO")


def get_file_hash(file_path: str) -> str:
    """Вычисляет MD5-хэш файла."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except IOError:
        return ""


def synchronize_files(disk: YandexDisk, local_folder: str, logger) -> None:
    """Синхронизирует файлы между локальной папкой и облаком."""
    try:
        cloud_files = disk.get_info()
        local_files = {
            f: os.path.getmtime(os.path.join(local_folder, f))
            for f in os.listdir(local_folder)
            if os.path.isfile(os.path.join(local_folder, f))
        }

        # Храним хэши файлов для проверки содержимого
        file_hashes = {}

        for cloud_file in cloud_files:
            if cloud_file not in local_files:
                if disk.delete(cloud_file):
                    logger.info(f"Deleted from cloud: {cloud_file}")
                else:
                    logger.error(f"Failed to delete from cloud: {cloud_file}")

        for local_file, local_mtime in local_files.items():
            local_path = os.path.join(local_folder, local_file)
            cloud_mtime = cloud_files.get(local_file, 0)

            if local_file not in cloud_files:
                if disk.load(local_path):
                    logger.info(f"Uploaded to cloud: {local_file}")
                else:
                    logger.error(f"Failed to upload: {local_file}")
            elif local_mtime > cloud_mtime + 5:  # Допуск 5 секунд
                # Проверяем хэш файла, чтобы избежать лишних обновлений
                current_hash = get_file_hash(local_path)
                if local_file not in file_hashes or file_hashes.get(local_file) != current_hash:
                    if disk.reload(local_path):
                        logger.info(f"Updated in cloud: {local_file}")
                        file_hashes[local_file] = current_hash
                    else:
                        logger.error(f"Failed to update: {local_file}")
                else:
                    logger.debug(f"Skipped update for {local_file}: content unchanged")

    except Exception as e:
        logger.error(f"Sync error: {str(e)}")


def main():
    """Основной метод программы."""
    config = setup_config()
    if not config:
        return

    setup_logger(config["log_file"])
    logger.info(f"Started syncing folder: {config['local_folder']}")

    try:
        disk = YandexDisk(config["token"], config["cloud_folder"])
    except ValueError as e:
        print(f"Error: {e}")
        return

    while True:
        synchronize_files(disk, config["local_folder"], logger)
        time.sleep(config["sync_interval"])


if __name__ == "__main__":
    main()
