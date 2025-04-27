from config import token, cloud_folder
import requests


# Токен авторизации
TOKEN = token

# URL для запроса информации о ресурсах (файлах и папках)
url = "https://cloud-api.yandex.net/v1/disk/resources"

# Заголовки запроса
headers = {
    "Authorization": f"OAuth {TOKEN}"
}

# Параметры запроса
params = {
    "path": cloud_folder,  # Корневая папка, можно изменить на нужную, например, "/my_folder"
    "fields": "_embedded.items.name,_embedded.items.created,_embedded.items.modified,_embedded.items.type",
    # Запрашиваемые поля
    "limit": 100,  # Максимальное количество элементов в ответе
    "offset": 0  # Смещение для пагинации
}

# Функция для обработки пагинации и получения всех файлов
def get_all_files():
    files = []
    while True:
        # Выполнение GET-запроса
        response = requests.get(url, headers=headers, params=params)

        # Проверка статуса ответа
        if response.status_code == 200:
            data = response.json()
            # Получаем список элементов (файлов и папок)
            items = data.get("_embedded", {}).get("items", [])

            # Фильтруем только файлы (исключаем папки)
            for item in items:
                if item["type"] == "file":
                    files.append({
                        "name": item["name"],
                        "created": item["created"],
                        "modified": item["modified"]
                    })

            # Проверяем, есть ли еще элементы (пагинация)
            total_items = data.get("_embedded", {}).get("total", 0)
            params["offset"] += params["limit"]
            if params["offset"] >= total_items:
                break
        else:
            # Вывод ошибки
            print(f"Ошибка {response.status_code}: {response.json().get('message', 'Неизвестная ошибка')}")
            return None

    # Вывод информации о файлах для тестов
    if files:
        print("Файлы на Яндекс.Диске:")
        for file in files:
            print(f"Имя: {file['name']}")
            print(f"Дата создания: {file['created']}")
            print(f"Дата изменения: {file['modified']}")
            print("-" * 40)
    else:
        print("Не удалось получить информацию о файлах.")

    return files

# Получение списка файлов
files = get_all_files()
