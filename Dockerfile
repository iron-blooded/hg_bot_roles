# Используем базовый образ Python
FROM python:3.11.11

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* requirements.txt

# Создание директории приложения
WORKDIR /hg_bot_roles

# Копирование файлов в директорию приложения
COPY . .

# Установка переменных окружения
ENV http_proxy=http://localhost:2080

# Команда для запуска вашего скрипта
CMD ["python", "main.py"]
