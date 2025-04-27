import os
import time
from loguru import logger
from yandex_disk import YandexDiskConnector
from config import config_dict

def configure_logger(log_file):
    """Настраивает логгер для записи в файл."""
    logger.remove()
    logger.add(log_file, format="{time} | {level} | {message}", level="DEBUG")  # DEBUG для диагностики

def synchronize_files(connector, local_folder, cloud_folder):
    """Синхронизирует файлы между локальной папкой и Яндекс.Диском."""
    try:
        logger.debug(f"Получение списка файлов из облака: {cloud_folder}")
        cloud_files_list = connector.get_info(verbose=False)
        cloud_files = {file["name"]: file["modified"] for file in cloud_files_list or []}
        logger.debug(f"Найдено {len(cloud_files)} файлов в облаке: {list(cloud_files.keys())}")

        local_files = {f for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))}
        logger.debug(f"Найдено {len(local_files)} локальных файлов: {local_files}")

        for cloud_file in cloud_files:
            if cloud_file not in local_files:
                connector.delete(cloud_file)
                logger.info(f"Deleted {cloud_file} from cloud storage")

        for local_file in local_files:
            local_path = os.path.join(local_folder, local_file)
            try:
                local_mtime = os.path.getmtime(local_path)
                cloud_mtime = 0
                if local_file in cloud_files:
                    try:
                        cloud_mtime = time.mktime(time.strptime(cloud_files[local_file], "%Y-%m-%dT%H:%M:%S%z"))
                    except ValueError as e:
                        logger.error(f"Ошибка парсинга времени для {local_file}: {e}")
                        continue

                if local_file not in cloud_files:
                    connector.load(local_path)
                    logger.info(f"Uploaded {local_file} to cloud storage")
                elif local_mtime > cloud_mtime:
                    connector.reload(local_path)
                    logger.info(f"Updated {local_file} in cloud storage")
            except (OSError, IOError) as e:
                logger.error(f"Error processing {local_file}: {e}")

    except Exception as e:
        logger.error(f"Synchronization error: {e}")
        raise  # Поднимаем исключение для диагностики

def main():
    """Основная функция для запуска синхронизации."""
    try:
        config = config_dict
        configure_logger(config["log_file"])
        logger.info(f"Starting synchronization for folder: {config['local_folder']}")
        logger.debug(f"Конфигурация: {config}")

        try:
            connector = YandexDiskConnector(config["token"], config["cloud_folder"])
        except ValueError as e:
            logger.error(f"Failed to initialize YandexDiskConnector: {e}")
            return

        synchronize_files(connector, config["local_folder"], config["cloud_folder"])

        while True:
            time.sleep(config["sync_interval"])
            synchronize_files(connector, config["local_folder"], config["cloud_folder"])

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()