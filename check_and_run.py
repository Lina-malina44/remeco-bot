import os
import requests
from fetch_and_send import run_full_export

BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]
LOGIN = os.environ["SITE_LOGIN"]
PASSWORD = os.environ["SITE_PASSWORD"]
TRIGGER_WORD = "остатки"
OFFSET_FILE = "last_update_id.txt"


def get_last_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            return int(f.read().strip() or 0)
    return 0


def save_last_offset(update_id):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(update_id))


def get_new_messages(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    resp = requests.get(url, params={"offset": offset + 1, "timeout": 0}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("result", [])


def send_text(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=30)


def main():
    last_offset = get_last_offset()
    updates = get_new_messages(last_offset)

    if not updates:
        print("Новых сообщений нет")
        return

    triggered = False
    max_update_id = last_offset

    for upd in updates:
        max_update_id = max(max_update_id, upd["update_id"])
        msg = upd.get("message") or upd.get("edited_message")
        if not msg:
            continue
        text = (msg.get("text") or "").strip().lower()
        chat_id = str(msg["chat"]["id"])
        if TRIGGER_WORD in text and chat_id == str(CHAT_ID):
            triggered = True

    save_last_offset(max_update_id)

    if triggered:
        print("Найдено кодовое слово, запускаю выгрузку")
        send_text(CHAT_ID, "Собираю свежий каталог, подождите пару минут...")
        run_full_export(LOGIN, PASSWORD, BOT_TOKEN, CHAT_ID)
    else:
        print("Кодовое слово не найдено")


if __name__ == "__main__":
    main()
