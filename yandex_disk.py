import requests
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import unquote, quote
from datetime import datetime

class YandexDisk:
    BASE_URL = "https://cloud-api.yandex.net/v1/disk/resources"

    def __init__(self, token: str, cloud_folder: str):
        """Инициализация с токеном и папкой в облаке."""
        self.headers = {"Authorization": f"OAuth {token}"}
        self.cloud_folder = cloud_folder.lstrip("/")
        self._ensure_cloud_folder()

    def _ensure_cloud_folder(self) -> None:
        """Создает папку в облаке, если она не существует."""
        try:
            response = requests.get(
                f"{self.BASE_URL}?path=/{self.cloud_folder}",
                headers=self.headers
            )
            if response.status_code == 404:
                requests.put(
                    f"{self.BASE_URL}?path=/{self.cloud_folder}",
                    headers=self.headers
                )
        except requests.RequestException as e:
            raise ValueError(f"Failed to initialize cloud folder: {e}")

    def load(self, local_path: str) -> bool:
        """Загружает новый файл в облако."""
        try:
            file_name = Path(local_path).name
            encoded_file_name = quote(file_name)
            upload_url = requests.get(
                f"{self.BASE_URL}/upload?path=/{self.cloud_folder}/{encoded_file_name}&overwrite=true",
                headers=self.headers
            )
            if upload_url.status_code != 200:
                raise ValueError(f"Failed to get upload URL: {upload_url.text}")
            upload_href = upload_url.json().get("href")
            with open(local_path, "rb") as f:
                response = requests.put(upload_href, files={"file": f})
            if response.status_code != 201:
                raise ValueError(f"Upload failed: {response.text}")
            return True
        except (requests.RequestException, IOError, ValueError) as e:
            print(f"Load error for {file_name}: {str(e)}")  # Временное логирование
            return False

    def reload(self, local_path: str) -> bool:
        """Перезаписывает файл в облаке."""
        return self.load(local_path)

    def delete(self, filename: str) -> bool:
        """Удаляет файл из облака."""
        try:
            encoded_filename = quote(filename)
            response = requests.delete(
                f"{self.BASE_URL}?path=/{self.cloud_folder}/{encoded_filename}",
                headers=self.headers
            )
            return response.status_code in (204, 202)
        except requests.RequestException:
            return False

    def get_info(self) -> Dict[str, float]:
        """Возвращает словарь {имя_файла: время_последнего_изменения}."""
        try:
            response = requests.get(
                f"{self.BASE_URL}?path=/{self.cloud_folder}&fields=_embedded.items.name,_embedded.items.modified",
                headers=self.headers
            )
            files = response.json().get("_embedded", {}).get("items", [])
            result = {}
            for f in files:
                name = unquote(f["name"])
                modified_str = f["modified"]
                # Парсим время без временной зоны, предполагая UTC
                modified = datetime.strptime(modified_str[:19], "%Y-%m-%dT%H:%M:%S").timestamp()
                result[name] = modified
            return result
        except (requests.RequestException, KeyError, ValueError):
            return {}
