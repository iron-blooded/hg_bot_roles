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

# Устанавливаем Node.js и npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Команда для запуска вашего скрипта
CMD ["python", "main.py"]

