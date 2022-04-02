[![Bintray](https://img.shields.io/badge/micropython-v1.12-green)]() [![Bintray](https://img.shields.io/badge/code%20style-black-black)]()

*This project is automatisation system*
*for water loading system*

[Technical requirements](.docs/technical_requirements.md)

Перед использованием переименовать test_config.json в config.json


<h1>TO DO</h1>

[x] - выбрать и настроить WEB-server
[x] - Обработка карт другого формата
[x] - сделать инициализацию модуля NFC через конструкцию try
[x] - сделать запрос данных по средствам requests через конструкцию try


[x] - Работа модулей в режиме клиент-сервер
    [x] - настройка процедуры загрузки data.json в зависимости от режима клиент/сервер
    [x] - настройка процедуры сохранения в зависимости от режима клиент/сервер

Создать web-консоль
[x] - Авторизация
[x] - Главная страница с перечнем карт и установками
[ ] - Страница настроек
[ ] - списание, установка лимитов процедур
[x] - Сортировка карт по номеру
[x] - проверка вводимого значения на валидность
[ ] - day лимит
[x] - обновление страницы https://techtutorialsx.com/2017/09/29/esp32-micropython-getting-the-query-parameters-on-a-picoweb-app/


[ ] - Плановая запись остатков
[x] - Задержка при выдаче
[ ] - Логирование
[ ] - Восстановление соединения wifi
[ ] - Ресурс flash

Обработка параметров запроса Flask
https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request

# Установка picoweb необходимых библиотек
import upip
upip.install('picoweb')
upip.install('micropython-logging')
# Решение проблемы с библиотекой uasyncio
необходимо удалить все изкаталога "uasyncio" с модуля
взять core.py и __init__.py из каталога micropython-lib
ampy -p /dev/tty.usbserial-0001 put core.py /lib/uasyncio/core.py
ampy -p /dev/tty.usbserial-0001 put __init__.py /lib/uasyncio/__init__.py

# Доп. информация
У меня карты mifare classic 1k
С номерами идут EM-Marine

# Получение syslog
sudo tcpdump -lns 0 -w - udp and port 514 | strings
# Запуск контейнера с внешним конфигурационным файлом
sudo docker run -it -v "$PWD/syslog-ng.conf":/Users/denispismenny/Documents/Development/Docker/syslog-ng/syslog-ng.conf balabit/syslog-ng:latest

