import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import datetime
import json, re

# Формируем credentials из переменных окружения
creds_info = json.loads(os.environ.get("creds_info"))

# ID вашей таблицы и название листа
SPREADSHEET_ID = creds_info["SPREADSHEET_ID"]  # Укажите ID в .env
SHEET_NAME = "1"

creds_info.pop("SPREADSHEET_ID")

creds = Credentials.from_service_account_info(creds_info)
service = build("sheets", "v4", credentials=creds)


def column_letter_to_index(letter):
    """Конвертирует буквенное обозначение столбца (например, 'A', 'BC') в числовой индекс (начиная с 0)"""
    letter = letter.upper()
    match = re.match(r"^([A-Z]+)$", letter)
    if not match:
        raise ValueError(f"Некорректное обозначение столбца: {letter}")

    index = 0
    for i, c in enumerate(reversed(match.group(1))):
        char_value = ord(c) - ord("A") + 1
        index += char_value * (26**i)
    return index - 1


def insert_column(
    spreadsheet_id,
    sheet_name,
    base_column,
    side="right",
):
    """
    Вставляет новый столбец в указанный Google Sheets документ

    Параметры:
    - spreadsheet_id: ID документа
    - sheet_name: Название листа
    - base_column: Буква столбца, относительно которого вставляем (например, 'C')
    - side: 'left' или 'right' (с какой стороны вставлять)
    - credentials_file: Путь к файлу учетных данных

    Возвращает результат выполнения операции
    """
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    # Находим ID листа
    sheet_id = None
    for sheet in spreadsheet["sheets"]:
        if sheet["properties"]["title"] == sheet_name:
            sheet_id = sheet["properties"]["sheetId"]
            break
    if not sheet_id:
        raise ValueError(f"Лист '{sheet_name}' не найден")

    # Конвертируем букву столбца в индекс
    try:
        column_index = column_letter_to_index(base_column)
    except ValueError as e:
        raise ValueError(f"Ошибка в параметре base_column: {e}")

    # Определяем позицию для вставки
    insert_position = column_index + 1 if side == "right" else column_index

    # Формируем запрос
    request = {
        "requests": [
            {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": insert_position,
                        "endIndex": insert_position + 1,
                    },
                    "inheritFromBefore": False,
                }
            }
        ]
    }

    # Выполняем запрос
    return (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=request)
        .execute()
    )


def format_date(dt: datetime.datetime) -> str:
    # Форматируем в ISO 8601 с временной зоной
    return dt.isoformat(timespec="seconds").replace("T", " ").split("+")[0]


def append_online_status(timestamp: datetime.datetime, online_nicks: list[str]):
    """Добавляет новую строку с онлайн-статусами"""
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A:Z")
        .execute()
    )
    values = result.get("values", [])
    headers = values[0] if values else ["Дата"]
    existing_nicks = set(headers[1:])
    new_nicks = sorted(
        list(set([i.strip() for i in online_nicks]) - existing_nicks)
    )  # Сортируем для порядка

    if new_nicks:
        # Вставляем новые колонки перед первой колонкой игроков
        for nick in new_nicks:
            insert_column(SPREADSHEET_ID, SHEET_NAME, base_column="B", side="left")

        # Обновляем заголовки
        updated_headers = headers.copy()
        for nick in reversed(
            new_nicks
        ):  # Вставляем в обратном порядке для сохранения последовательности
            updated_headers.insert(1, nick)

        # Обновляем заголовки в таблице
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body={"values": [updated_headers]},
        ).execute()

        # Обновляем локальные заголовки
        headers = updated_headers

    # Формируем новую строку
    formatted_time = format_date(timestamp)
    new_row = [formatted_time]
    for nick in headers[1:]:
        new_row.append(1 if nick in online_nicks else 0)

    # Добавляем строку с интерпретацией формата
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A{len(values)+1}",
        valueInputOption="USER_ENTERED",
        body={"values": [new_row]},
    ).execute()
