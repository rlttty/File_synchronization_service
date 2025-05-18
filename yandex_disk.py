import requests
from pathlib import Path
from typing import Dict
from urllib.parse import unquote, quote
from datetime import datetime


class YandexDiskError(Exception):
    """Custom exception for Yandex Disk operations."""
    pass


class YandexDisk:
    BASE_URL = "https://cloud-api.yandex.net/v1/disk/resources"
    REQUEST_TIMEOUT = 30  # seconds

    def __init__(self, token: str, cloud_folder: str):
        """Initializes with token and cloud folder."""
        self.headers = {"Authorization": f"OAuth {token}"}
        self.cloud_folder = cloud_folder.lstrip("/")
        self._ensure_cloud_folder()

    def _ensure_cloud_folder(self) -> None:
        """Creates cloud folder if it doesn't exist."""
        try:
            response = requests.get(
                f"{self.BASE_URL}?path=/{self.cloud_folder}",
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT
            )
            if response.status_code == 404:
                response = requests.put(
                    f"{self.BASE_URL}?path=/{self.cloud_folder}",
                    headers=self.headers,
                    timeout=self.REQUEST_TIMEOUT
                )
                if response.status_code != 201:
                    raise YandexDiskError(f"Failed to create cloud folder: {response.text}")
        except (requests.Timeout, requests.ConnectionError) as e:
            error_msg = f"Network error initializing cloud folder: {str(e)}"
            print(error_msg)
            raise YandexDiskError(error_msg)
        except requests.RequestException as e:
            error_msg = f"Failed to initialize cloud folder: {str(e)}"
            print(error_msg)
            raise YandexDiskError(error_msg)

    def load(self, local_path: str) -> bool:
        """Uploads a new file to the cloud."""
        try:
            file_name = Path(local_path).name
            encoded_file_name = quote(file_name)
            upload_response = requests.get(
                f"{self.BASE_URL}/upload?path=/{self.cloud_folder}/{encoded_file_name}&overwrite=true",
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT
            )
            if upload_response.status_code != 200:
                raise YandexDiskError(f"Failed to get upload URL: {upload_response.text}")

            upload_href = upload_response.json().get("href")
            with open(local_path, "rb") as file:
                response = requests.put(
                    upload_href,
                    files={"file": file},
                    timeout=self.REQUEST_TIMEOUT
                )
            if response.status_code != 201:
                raise YandexDiskError(f"Upload failed: {response.text}")
            return True
        except (requests.Timeout, requests.ConnectionError) as e:
            error_msg = f"Network error uploading {file_name}: {str(e)}"
            print(error_msg)
            return False
        except (requests.RequestException, IOError, YandexDiskError) as e:
            error_msg = f"Load error for {file_name}: {str(e)}"
            print(error_msg)
            return False

    def reload(self, local_path: str) -> bool:
        """Overwrites a file in the cloud."""
        return self.load(local_path)

    def delete(self, filename: str) -> bool:
        """Deletes a file from the cloud."""
        try:
            encoded_filename = quote(filename)
            response = requests.delete(
                f"{self.BASE_URL}?path=/{self.cloud_folder}/{encoded_filename}",
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT
            )
            return response.status_code in (204, 202)
        except (requests.Timeout, requests.ConnectionError) as e:
            error_msg = f"Network error deleting {filename}: {str(e)}"
            print(error_msg)
            return False
        except requests.RequestException as e:
            error_msg = f"Failed to delete {filename}: {str(e)}"
            print(error_msg)
            return False

    def get_info(self) -> Dict[str, float]:
        """Returns dictionary of {filename: last_modified_time}."""
        try:
            response = requests.get(
                f"{self.BASE_URL}?path=/{self.cloud_folder}&fields=_embedded.items.name,_embedded.items.modified",
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            items = response.json().get("_embedded", {}).get("items", [])
            result = {}
            for item in items:
                name = unquote(item["name"])
                modified_str = item["modified"]
                modified = datetime.strptime(modified_str[:19], "%Y-%m-%dT%H:%M:%S").timestamp()
                result[name] = modified
            return result
        except (requests.Timeout, requests.ConnectionError) as e:
            error_msg = f"Network error getting cloud info: {str(e)}"
            print(error_msg)
            return {}
        except (requests.RequestException, KeyError, ValueError) as e:
            error_msg = f"Failed to get cloud info: {str(e)}"
            print(error_msg)
            return {}
