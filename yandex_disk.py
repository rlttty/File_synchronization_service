import requests
import os
from loguru import logger
import urllib.parse
import time


class YandexDiskConnector:
    def __init__(self, token, cloud_folder):
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {"Authorization": f"OAuth {token}"}
        # Проверяем валидность токена
        if not self.verify_token():
            raise ValueError("Недействительный или неподходящий токен")
        # Очищаем cloud_folder от префикса disk:/ и лишних слэшей
        # cleaned_folder = cloud_folder.strip('/').replace('disk:/', '')
        # # Формируем корректный путь
        # self.cloud_folder = f"disk:/{cleaned_folder}" if cleaned_folder else "disk:/"
        # # Проверяем существование папки при инициализации
        # self._ensure_folder_exists()

    def verify_token(self):
        """Проверяет валидность токена."""
        try:
            response = requests.get(f"{self.base_url}/", headers=self.headers)
            response.raise_for_status()
            logger.debug("Токен валиден.")
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ошибка проверки токена: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса при проверке токена: {e}")
            return False

    def _encode_path(self, path):
        """Кодирует путь для использования в API, избегая двойного кодирования."""
        if '%3A' in path or '%2F' in path:
            return path  # Путь уже закодирован
        return urllib.parse.quote(path, safe='')

    def _ensure_folder_exists(self):
        """Проверяет существование папки, не создавая новую."""
        encoded_path = self._encode_path(self.cloud_folder)
        params = {"path": encoded_path}
        try:
            logger.debug(f"Проверка папки {self.cloud_folder}, закодированный путь: {encoded_path}")
            response = requests.get(f"{self.base_url}/resources", headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Ответ API при проверке папки: {data}")
            if data.get("type") != "dir":
                logger.error(f"По пути {self.cloud_folder} находится не папка, а другой ресурс.")
                raise ValueError(f"Путь {self.cloud_folder} не является папкой")
            logger.debug(f"Папка {self.cloud_folder} существует и готова к использованию.")
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                logger.error(f"Папка {self.cloud_folder} не существует на Яндекс.Диске.")
                raise ValueError(f"Папка {self.cloud_folder} не найдена")
            else:
                logger.error(f"Ошибка при проверке папки {self.cloud_folder}: {http_err}")
                raise
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка запроса при проверке папки: {err}")
            raise

    def load(self, local_path):
        """Загружает файл на Яндекс.Диск."""
        try:
            upload_url = f"{self.base_url}/resources/upload"
            filename = os.path.basename(local_path)
            cloud_path = f"{self.cloud_folder}/{filename}"
            params = {"path": self._encode_path(cloud_path), "overwrite": False}
            response = requests.get(upload_url, headers=self.headers, params=params)
            response.raise_for_status()
            upload_data = response.json()
            if "href" not in upload_data:
                logger.error(f"Не получен URL для загрузки файла {local_path}")
                raise ValueError("Не получен URL для загрузки")
            upload_link = upload_data["href"]

            with open(local_path, "rb") as f:
                response = requests.put(upload_link, files={"file": f})
                response.raise_for_status()
                if response.status_code != 201:
                    logger.error(f"Неожиданный статус ответа при загрузке {local_path}: {response.status_code}")
                    raise ValueError(f"Ожидался статус 201, получен {response.status_code}")
            logger.info(f"Файл {local_path} успешно загружен в {cloud_path}.")
            return True
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            error_msg = f"Ошибка при загрузке {local_path}: "
            if status_code == 400:
                logger.error(error_msg + "Некорректные данные")
            elif status_code == 401:
                logger.error(error_msg + "Не авторизован")
            elif status_code == 403:
                logger.error(error_msg + "API недоступно")
            elif status_code == 404:
                logger.error(error_msg + "Папка на Диске не найдена")
            elif status_code == 409:
                logger.warning(error_msg + "Файл уже существует")
            elif status_code == 413:
                logger.error(error_msg + "Файл слишком большой")
            elif status_code == 507:
                logger.error(error_msg + "Недостаточно места")
            else:
                logger.error(error_msg + f"HTTP ошибка: {status_code}")
            raise
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка запроса при загрузке {local_path}: {err}")
            raise
        except FileNotFoundError:
            logger.error(f"Локальный файл {local_path} не найден.")
            raise

    def reload(self, local_path):
        """Перезагружает файл (с перезаписью)."""
        try:
            upload_url = f"{self.base_url}/resources/upload"
            filename = os.path.basename(local_path)
            cloud_path = f"{self.cloud_folder}/{filename}"
            params = {"path": self._encode_path(cloud_path), "overwrite": True}
            response = requests.get(upload_url, headers=self.headers, params=params)
            response.raise_for_status()
            upload_data = response.json()
            if "href" not in upload_data:
                logger.error(f"Не получен URL для загрузки файла {local_path}")
                raise ValueError("Не получен URL для загрузки")
            upload_link = upload_data["href"]

            with open(local_path, "rb") as f:
                response = requests.put(upload_link, files={"file": f})
                response.raise_for_status()
                if response.status_code != 201:
                    logger.error(f"Неожиданный статус ответа при перезагрузке {local_path}: {response.status_code}")
                    raise ValueError(f"Ожидался статус 201, получен {response.status_code}")
            logger.info(f"Файл {local_path} успешно перезагружен в {cloud_path}.")
            return True
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            error_msg = f"Ошибка при перезагрузке {local_path}: "
            if status_code == 400:
                logger.error(error_msg + "Некорректные данные")
            elif status_code == 401:
                logger.error(error_msg + "Не авторизован")
            elif status_code == 403:
                logger.error(error_msg + "API недоступно")
            elif status_code == 404:
                logger.error(error_msg + "Папка на Диске не найдена")
            elif status_code == 413:
                logger.error(error_msg + "Файл слишком большой")
            elif status_code == 507:
                logger.error(error_msg + "Недостаточно места")
            else:
                logger.error(error_msg + f"HTTP ошибка: {status_code}")
            raise
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка запроса при перезагрузке {local_path}: {err}")
            raise
        except FileNotFoundError:
            logger.error(f"Локальный файл {local_path} не найден.")
            raise

    def delete(self, filename):
        """Удаляет файл из облачной папки."""
        try:
            delete_url = f"{self.base_url}/resources"
            cloud_path = f"{self.cloud_folder}/{filename}"
            params = {"path": self._encode_path(cloud_path)}
            response = requests.delete(delete_url, headers=self.headers, params=params)
            response.raise_for_status()
            logger.info(f"Файл {cloud_path} успешно удалён.")
            return True
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 404:
                logger.warning(f"Файл {cloud_path} не существует.")
                return False
            logger.error(f"Ошибка при удалении {filename}: {http_err}")
            raise
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка запроса при удалении {filename}: {err}")
            raise

    def get_info(self, verbose=False):
        """
        Получает информацию о файлах в облачной папке с поддержкой пагинации.

        Args:
            verbose (bool): Если True, выводит информацию о файлах в консоль.

        Returns:
            list: Список словарей с информацией о файлах ({name, created, modified}).
        """
        try:
            info_url = f"{self.base_url}/resources"
            params = {
                "path": self._encode_path(self.cloud_folder),
                "fields": "_embedded.items.name,_embedded.items.created,_embedded.items.modified,_embedded.items.type",
                "limit": 100,
                "offset": 0
            }
            files = []

            while True:
                logger.debug(f"Запрос к API: {info_url}, параметры: {params}")
                response = requests.get(info_url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Ответ API для {self.cloud_folder}: {data}")

                if "_embedded" not in data or "items" not in data["_embedded"]:
                    logger.warning(
                        f"Неожиданная структура ответа для папки {self.cloud_folder}: отсутствуют ключи _embedded или items")
                    return []

                items = data["_embedded"].get("items", [])
                for item in items:
                    if item.get("type") == "file":
                        files.append({
                            "name": item["name"],
                            "created": item["created"],
                            "modified": item["modified"]
                        })

                total_items = data.get("_embedded", {}).get("total", 0)
                params["offset"] += params["limit"]
                if params["offset"] >= total_items:
                    break

            if not files:
                logger.info(f"Папка {self.cloud_folder} пуста или не содержит файлов.")

            logger.debug(f"Получена информация о {len(files)} файлах в {self.cloud_folder}.")

            if verbose:
                if files:
                    print("Файлы на Яндекс.Диске:")
                    for file in files:
                        print(f"Имя: {file['name']}")
                        print(f"Дата создания: {file['created']}")
                        print(f"Дата изменения: {file['modified']}")
                        print("-" * 40)
                else:
                    print("Файлы в папке не найдены.")

            return files

        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            try:
                message = http_err.response.json().get("message", "Неизвестная ошибка")
            except ValueError:
                message = str(http_err)
            logger.error(f"Ошибка при получении информации о папке {self.cloud_folder}: {status_code} - {message}")
            return []
        except requests.exceptions.RequestException as err:
            logger.error(f"Ошибка запроса при получении информации: {err}")
            return []

    def scan_and_upload_files(self, local_folder, overwrite=False):
        """Сканирует локальную папку и загружает все файлы в облачную папку."""
        try:
            files = [f for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))]
            if not files:
                logger.info(f"В папке {local_folder} нет файлов для загрузки")
                return

            for filename in files:
                local_file_path = os.path.join(local_folder, filename)
                logger.info(f"Попытка загрузки файла: {filename}")
                try:
                    if overwrite:
                        success = self.reload(local_file_path)
                    else:
                        success = self.load(local_file_path)
                    if success:
                        logger.info(f"Файл {filename} успешно загружен")
                except Exception as e:
                    logger.error(f"Не удалось загрузить файл {filename}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке папки {local_folder}: {e}")