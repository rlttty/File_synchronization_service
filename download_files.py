from config import token, local_folder, cloud_folder
import requests
import urllib.parse
import os


def get_upload_url(token, file_path, overwrite=False):
    """
    Запрашивает URL для загрузки файла на Яндекс.Диск.

    Args:
        token (str): OAuth-токен
        file_path (str): Путь для загрузки файла на Диске
        overwrite (bool): Перезаписывать существующий файл

    Returns:
        dict: Ответ API с URL для загрузки
    """
    encoded_path = urllib.parse.quote(file_path)
    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {
        "path": encoded_path,
        "overwrite": str(overwrite).lower()
    }
    headers = {
        "Authorization": f"OAuth {token}"
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def upload_file(file_path, upload_url):
    """
    Загружает файл по полученному URL.

    Args:
        file_path (str): Локальный путь к файлу
        upload_url (str): URL для загрузки файла

    Returns:
        bool: True если загрузка успешна
    """
    with open(file_path, 'rb') as file:
        response = requests.put(upload_url, data=file)
        response.raise_for_status()
        return response.status_code == 201


def upload_to_yandex_disk(token, local_file_path, disk_file_path, overwrite=False):
    """
    Полный процесс загрузки файла на Яндекс.Диск.

    Args:
        token (str): OAuth-токен
        local_file_path (str): Путь к локальному файлу
        disk_file_path (str): Путь для загрузки на Диске
        overwrite (bool): Перезаписывать существующий файл

    Returns:
        bool: True если загрузка успешна
    """
    try:
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"Файл {local_file_path} не найден")

        upload_data = get_upload_url(token, disk_file_path, overwrite)

        if 'href' not in upload_data:
            raise ValueError("Не получен URL для загрузки")

        return upload_file(local_file_path, upload_data['href'])

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 400:
            print(f"Ошибка при загрузке {local_file_path}: Некорректные данные")
        elif status_code == 401:
            print(f"Ошибка при загрузке {local_file_path}: Не авторизован")
        elif status_code == 403:
            print(f"Ошибка при загрузке {local_file_path}: API недоступно")
        elif status_code == 404:
            print(f"Ошибка при загрузке {local_file_path}: Папка на Диске не найдена")
        elif status_code == 409:
            print(f"Ошибка при загрузке {local_file_path}: Ресурс уже существует")
        elif status_code == 413:
            print(f"Ошибка при загрузке {local_file_path}: Файл слишком большой")
        elif status_code == 507:
            print(f"Ошибка при загрузке {local_file_path}: Недостаточно места")
        else:
            print(f"HTTP ошибка при загрузке {local_file_path}: {status_code}")
        return False
    except Exception as e:
        print(f"Ошибка при загрузке {local_file_path}: {str(e)}")
        return False


def scan_and_upload_files():
    """
    Сканирует локальную папку и загружает все файлы в указанную папку на Яндекс.Диске.
    """
    try:
        # # Получаем список файлов в папке
        files = [f for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))]

        if not files:
            print("В папке нет файлов для загрузки")
            return

        # Обрабатываем каждый файл
        for filename in files:
            local_file_path = os.path.join(local_folder, filename)
            # Формируем путь на Яндекс.Диске, добавляя имя файла
            disk_file_path = f"{cloud_folder}/{filename}"

            print(f"Попытка загрузки файла: {filename}")
            success = upload_to_yandex_disk(token, local_file_path, disk_file_path, overwrite=True)

            if success:
                print(f"Файл {filename} успешно загружен")
                # Опционально: удаляем файл после успешной загрузки
                # os.remove(local_file_path)
                # print(f"Локальный файл {filename} удален")
            else:
                print(f"Не удалось загрузить файл {filename}")

    except Exception as e:
        print(f"Ошибка при обработке папки: {str(e)}")


if __name__ == "__main__":
    scan_and_upload_files()
