import os
import xml.etree.ElementTree as ET
import pandas as pd
import requests

SITE_URL = "https://remecoclub.ru/personal/xml/siteremeco.xml"
OUT_FILE = "remeco_catalog.xlsx"


def download_xml(login, password):
    resp = requests.get(SITE_URL, auth=(login, password), timeout=60)
    resp.raise_for_status()
    with open("siteremeco.xml", "wb") as f:
        f.write(resp.content)


def convert_to_excel():
    tree = ET.parse("siteremeco.xml")
    root = tree.getroot()
    shop = root.find("shop")
    cat_names = {c.get("id"): c.text for c in shop.find("categories")}

    def get(offer, tag):
        el = offer.find(tag)
        return el.text if el is not None and el.text else ""

    rows = []
    for offer in shop.find("offers"):
        cat_id = get(offer, "categoryId")
        pics = offer.find("pictures")
        pic_list = [p.text for p in pics] if pics is not None else []
        rows.append({
            "ID товара": offer.get("id"),
            "Артикул": get(offer, "artikul"),
            "Штрихкод": get(offer, "barcode"),
            "Название": get(offer, "name"),
            "Категория ID": cat_id,
            "Категория": cat_names.get(cat_id, ""),
            "Цена": get(offer, "price"),
            "РРЦ": get(offer, "priceRrc"),
            "Валюта": get(offer, "currencyId"),
            "В наличии": offer.get("available"),
            "Наличие (кол-во)": get(offer, "availability"),
            "Кратность заказа (lot)": get(offer, "lot"),
            "Кол-во в коробе": get(offer, "quantbox"),
            "Материал": get(offer, "materials"),
            "Упаковка": get(offer, "pack"),
            "Тип скидки": get(offer, "discountType"),
            "Вес, кг": get(offer, "weight"),
            "Длина, см": get(offer, "length"),
            "Ширина, см": get(offer, "width"),
            "Высота, см": get(offer, "height"),
            "Вес упаковки, кг": get(offer, "pack_weight"),
            "Длина упаковки, см": get(offer, "pack_length"),
            "Ширина упаковки, см": get(offer, "pack_width"),
            "Высота упаковки, см": get(offer, "pack_height"),
            "Описание": get(offer, "description"),
            "Главное фото": get(offer, "picture"),
            "Доп. фото": ", ".join(pic_list),
        })

    df = pd.DataFrame(rows)
    numeric_cols = ["Цена", "РРЦ", "Кратность заказа (lot)", "Кол-во в коробе",
                     "Вес, кг", "Длина, см", "Ширина, см", "Высота, см",
                     "Вес упаковки, кг", "Длина упаковки, см", "Ширина упаковки, см",
                     "Высота упаковки, см"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Каталог")
        ws = writer.sheets["Каталог"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        from openpyxl.styles import Font
        for cell in ws[1]:
            cell.font = Font(bold=True)

    print(f"Готово: {len(df)} товаров")


def send_to_telegram(bot_token, chat_id, caption="Обновлённый каталог REMECOCLUB"):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(OUT_FILE, "rb") as f:
        resp = requests.post(
            url,
            data={"chat_id": chat_id, "caption": caption},
            files={"document": f},
            timeout=60,
        )
    resp.raise_for_status()
    print("Отправлено в Telegram")


def run_full_export(login, password, bot_token, chat_id, caption="Обновлённый каталог REMECOCLUB"):
    download_xml(login, password)
    convert_to_excel()
    send_to_telegram(bot_token, chat_id, caption)


if __name__ == "__main__":
    run_full_export(
        os.environ["SITE_LOGIN"],
        os.environ["SITE_PASSWORD"],
        os.environ["TG_BOT_TOKEN"],
        os.environ["TG_CHAT_ID"],
    )
