# Используем базовый образ Python
FROM python:3.11

# Создание директории приложения
WORKDIR /hg_bot_roles

# Копирование файлов в директорию приложения
COPY . .

# Установка переменных окружения
ENV ENV_VARIABLE=value

# Установка зависимостей
RUN pip install -r requirements.txt

# Команда для запуска вашего скрипта
CMD ["python", "main.py"]

