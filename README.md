# File_synchronization_service.

## description:

File_synchronization_service, это программа, позволяющая делать синхронизацию на своём компьютере пользователя с облачным хранилищем. 
этот сервис позволяет автоматически обновлять и согласовывать файлы между персональным компьютером и облаком.

## Program capabilities:
1. программа синхронизируя локальную папку, находит там файлы и загружает на диск;
2. если программа обнаруживает измененный файл, она в перезаписывает его в облако;
3. программа также позволяет удалять файлы с облачного хранилища;
4. можно получать информацию о всех файлах, их последнее изменение и дата создание.

## How to start the program:
1. клонируйте проект с GitHub на свой локальный компьютер;
2. в папке проекта найдите файл .env.template и переименуйте на файл .env;
3. данном файле заполните токен к вашему API;
3.1. в конфигурационном файле config.ini, вам нужно заполнить те переменные нужными данными: путь к локальной папке, путь к папке от вашего облачного хранилище;
4. распакуйте, установите зависимости содержимое файла requirements.txt;
5. после того, как вы установили все значения, запустите программу. для этого можете запустить файл main.py.


# File_Synchronization_Service.

## Description:

FILE_SYNCHRONISATION_SERVICE, this is a program that allows you to do synchronization on your user's computer with cloud storage. 
This service allows you to automatically update and coordinate files between a personal computer and a cloud.

## Program Capabilites:
1. The program synchronizing the local folder, finds files there and uploads to the disk;
2. If the program detects a changed file, it rewrites it into a cloud;
3. The program also allows you to delete files from the cloud storage;
4. You can receive information about all files, their last change and date creation.

## How to Start the Program:
1. Clon the project with GitHub to your local computer;
2. In the project folder, find the .env.template file and rename to the .env file;
3. This file fill out the token to your API;
3.1. In the configuration file config.ini, you need to fill out those variables with the necessary data: the path to the local folder, the path to the folder from your cloud storage;
4. Put, set dependencies to the contents of the REQUREMENTS.TXT file;
5. After you have set all values, run the program. To do this, you can start the Main.py file.