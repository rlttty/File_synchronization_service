from config import config_dict, token, cloud_folder
import requests
import os
from urllib.parse import quote


# Параметры
YANDEX_DISK_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"
OAUTH_TOKEN = token
BACKUP_FOLDER = cloud_folder  # Путь к папке backup из .env, по умолчанию /backup

# Функция для удаления файла
def delete_file(filename, permanently=False, force_async=False):
    # Формирование полного пути к файлу
    file_path = f"{BACKUP_FOLDER}/{filename}".strip("/")
    encoded_path = quote(file_path)  # Кодирование пути в URL-формат

    # Формирование заголовков
    headers = {
        "Authorization": f"OAuth {OAUTH_TOKEN}"
    }

    # Формирование параметров запроса
    params = {
        "path": encoded_path,
        "permanently": permanently,
        "force_async": force_async
    }

    # Выполнение DELETE-запроса
    response = requests.delete(YANDEX_DISK_API_URL, headers=headers, params=params)

    # Обработка ответа
    if response.status_code == 204:
        print(f"Файл {filename} успешно удален.")
    elif response.status_code == 202:
        print(f"Удаление файла {filename} начато (асинхронная операция).")
        operation_link = response.json().get("href")
        print(f"Ссылка для проверки статуса операции: {operation_link}")
        return operation_link
    else:
        print(f"Ошибка при удалении файла {filename}: {response.status_code}")
        print(response.json())
        return None


# Пример использования: удаление файла example.txt
filename = "mrderr.txt"
delete_file(filename, permanently=False, force_async=False)
