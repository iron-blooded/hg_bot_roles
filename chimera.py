import requests, random

prompt_consultant = open("prompt_consultant.txt").read()

def consultant(text: str) -> str:
    text = prompt_consultant+text
    def rnd(i:int):
        return str(random.randint(int('1'+('0'*i)), int('9'*(i+1))))
    headers = {
        'authority': 'chimera.dead228inside.repl.co',
        'accept': 'text/event-stream',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://chimera.dead228inside.repl.co',
        'referer': 'https://chimera.dead228inside.repl.co/chat/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    json_data = {
        'conversation_id': f'ccb084b1-c{rnd(3)}-86c0-{rnd(3)}d-{rnd(5)}ad{rnd(4)}',
        'action': '_ask',
        'model': 'claude-2-100k',
        'jailbreak': 'default',
        'meta': {
            'id': f'725776{rnd(13)}',
            'content': {
                'conversation': [],
                'internet_access': False,
                'content_type': 'text',
                'parts': [
                    {
                        'content': text,
                        'role': 'user',
                    },
                ],
            },
        },
    }
    response = "Unable To Wake Up"
    while "Unable To Wake Up" in response:
        response = requests.post('https://chimera.dead228inside.repl.co/backend-api/v2/conversation', headers=headers, json=json_data, timeout=60*4).text
    if 'http' in response:
        response = "Что то пошло не так!"
    return response
