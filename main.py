import os
import time
import configparser
from pathlib import Path
from typing import Optional
from logger import setup_logger, LoggerSetupError
from dotenv import dotenv_values
from yandex_disk import YandexDisk
import hashlib
import logging

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class FileHashError(Exception):
    """Custom exception for file hash calculation errors."""
    pass

class SyncError(Exception):
    """Custom exception for synchronization errors."""
    pass

def setup_config() -> dict:
    """Reads configuration from config.ini and .env."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    if not config.has_section("Settings"):
        raise ConfigError("Missing [Settings] section in config.ini")

    settings = config["Settings"]
    env = dotenv_values(".env")

    result = {
        "local_folder": settings.get("local_folder"),
        "cloud_folder": settings.get("cloud_folder"),
        "sync_interval": settings.getint("sync_interval", 60),
        "log_file": settings.get("log_file", "sync.log"),
        "token": env.get("YANDEX_TOKEN")
    }

    if not result["local_folder"]:
        raise ConfigError("The local_folder path is not specified in config.ini. Please specify a valid path.")
    if not os.path.isdir(result["local_folder"]):
        raise ConfigError(f"The folder '{result['local_folder']}' does not exist. Please create it.")
    if not result["token"]:
        raise ConfigError("The YANDEX_TOKEN is not set in the .env file. Please add a valid token.")

    return result


def get_file_hash(file_path: str) -> str:
    """Calculates MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, PermissionError) as e:
        raise FileHashError(f"Failed to calculate hash for {file_path}: {str(e)}")


def synchronize_files(disk: YandexDisk, local_folder: str, sync_logger: logging.Logger) -> None:
    """Synchronizes files between local folder and cloud."""
    try:
        cloud_files = disk.get_info()
        local_files = {
            filename: os.path.getmtime(os.path.join(local_folder, filename))
            for filename in os.listdir(local_folder)
            if os.path.isfile(os.path.join(local_folder, filename))
        }

        file_hashes = {}

        for cloud_file in cloud_files:
            if cloud_file not in local_files:
                if disk.delete(cloud_file):
                    sync_logger.info(f"Deleted from cloud: {cloud_file}")
                else:
                    sync_logger.error(f"Failed to delete from cloud: {cloud_file}")

        for local_file, local_mtime in local_files.items():
            local_path = os.path.join(local_folder, local_file)
            cloud_mtime = cloud_files.get(local_file, 0)

            if local_file not in cloud_files:
                if disk.load(local_path):
                    sync_logger.info(f"Uploaded to cloud: {local_file}")
                else:
                    sync_logger.error(f"Failed to upload: {local_file}")
            elif local_mtime > cloud_mtime + 5:
                try:
                    current_hash = get_file_hash(local_path)
                    if local_file not in file_hashes or file_hashes.get(local_file) != current_hash:
                        if disk.reload(local_path):
                            sync_logger.info(f"Updated in cloud: {local_file}")
                            file_hashes[local_file] = current_hash
                        else:
                            sync_logger.error(f"Failed to update: {local_file}")
                    else:
                        sync_logger.debug(f"Skipped update for {local_file}: content unchanged")
                except FileHashError as e:
                    sync_logger.error(str(e))
                    print(str(e))

    except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
        error_msg = f"Network error during sync: {str(e)}"
        sync_logger.error(error_msg)
        print(error_msg)
    except Exception as e:
        error_msg = f"Unexpected sync error: {str(e)}"
        sync_logger.error(error_msg)
        print(error_msg)


def main() -> None:
    """Main program method."""
    try:
        config = setup_config()
        # Reconfigure logger with the specified log file
        sync_logger = setup_logger(config["log_file"])
        sync_logger.info(f"Started syncing folder: {config['local_folder']}")

        disk = YandexDisk(config["token"], config["cloud_folder"])
        while True:
            synchronize_files(disk, config["local_folder"], sync_logger)
            time.sleep(config["sync_interval"])

    except (ConfigError, LoggerSetupError, ValueError) as e:
        error_msg = str(e)
        print(error_msg)
        raise

if __name__ == "__main__":
        main()
