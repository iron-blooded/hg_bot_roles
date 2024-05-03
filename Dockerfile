# Используем базовый образ Python
FROM python:3.12.2-slim

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* requirements.txt

# Устанавливаем Node.js и npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Создание директории приложения
WORKDIR /hg_bot_roles

# Копирование файлов в директорию приложения
COPY . .

# Установка переменных окружения
ENV ENV_VARIABLE=value

# Команда для запуска вашего скрипта
CMD ["python", "main.py"]
