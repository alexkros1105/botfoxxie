"""
BotHelp Webhook → Telegram Notification Bot
Принимает данные подписчика от BotHelp и отправляет уведомление в Telegram.
"""

import os
import logging
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse

# ═══════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════
BOT_TOKEN = os.getenv("BOT_TOKEN", "7583211249:AAHm140INsdByKAsU-kk63ElWO_s6GLOMwk")
CHAT_ID = os.getenv("CHAT_ID", "1191653357")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="BotHelp Webhook Bot", docs_url=None, redoc_url=None)

# ═══════════════════════════════════════════
# ОТПРАВКА СООБЩЕНИЙ В TELEGRAM
# ═══════════════════════════════════════════

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def escape_html(text: str) -> str:
    if not text:
        return "—"
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_bothelp_chat_link(data: dict) -> Optional[str]:
    """Собираем ссылку на диалог в BotHelp, если есть нужные поля."""
    bot_id = data.get("bot_id") or data.get("bothelp_bot_id")
    subscriber_id = data.get("subscriber_id") or data.get("id")
    
    if bot_id and subscriber_id:
        return f"https://my.bothelp.io/chat/{bot_id}/{subscriber_id}"
    
    chat_link = data.get("bothelp_chat_link") or data.get("dialog_url")
    if chat_link:
        return str(chat_link)
    
    return None


def build_user_link(data: dict) -> Optional[str]:
    """Собираем ссылку на пользователя в Telegram."""
    tg_username = data.get("telegram_username") or data.get("tg_username") or data.get("username")
    messenger_id = data.get("messenger_id") or data.get("telegram_id") or data.get("user_id")
    
    if tg_username and str(tg_username).strip():
        username = str(tg_username).lstrip("@").strip()
        return f"https://t.me/{username}"
    
    if messenger_id and str(messenger_id).strip():
        return f"tg://user?id={messenger_id}"
    
    return None


def detect_source(data: dict) -> str:
    """Определяем источник лида."""
    source = data.get("source", "")
    bot_name = data.get("bot_name", "")
    channel = data.get("channel", "")
    utm_source = data.get("utm_source", "")
    
    if bot_name:
        return str(bot_name)
    if source:
        return str(source)
    if channel:
        return str(channel)
    if utm_source:
        return f"UTM: {utm_source}"
    return "BotHelp"


async def send_telegram_notification(data: dict):
    """Формирует и отправляет уведомление в Telegram."""
    
    # ── Извлекаем данные ──
    name = data.get("name") or data.get("first_name") or "—"
    last_name = data.get("last_name") or ""
    full_name = f"{name} {last_name}".strip()
    
    phone = data.get("phone") or data.get("phone_number") or "—"
    email = data.get("email") or "—"
    messenger_username = data.get("messenger_username") or data.get("username") or "—"
    messenger_id = data.get("messenger_id") or data.get("telegram_id") or data.get("user_id") or "—"
    
    source = detect_source(data)
    bothelp_chat_link = build_bothelp_chat_link(data)
    user_link = build_user_link(data)
    
    # ── Формируем текст сообщения ──
    text = (
        f"🎯 <b>Новый лид из BotHelp!</b>\n\n"
        f"👤 <b>Имя:</b> {escape_html(full_name)}\n"
    )
    
    if phone != "—":
        text += f"📱 <b>Телефон:</b> <code>{escape_html(phone)}</code>\n"
    
    if email != "—":
        text += f"📧 <b>Email:</b> {escape_html(email)}\n"
    
    if str(messenger_username) != "—":
        text += f"💬 <b>Username:</b> @{escape_html(str(messenger_username).lstrip('@'))}\n"
    
    text += f"🆔 <b>ID:</b> <code>{escape_html(str(messenger_id))}</code>\n"
    text += f"📌 <b>Источник:</b> {escape_html(source)}\n"
    text += f"🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    
    # ── Кнопки ──
    buttons = []
    
    if bothelp_chat_link:
        buttons.append({
            "text": "💬 Открыть диалог в BotHelp",
            "url": bothelp_chat_link
        })
    
    if user_link:
        buttons.append({
            "text": "👤 Написать в Telegram",
            "url": user_link
        })
    
    if phone != "—":
        clean_phone = str(phone).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean_phone.startswith("+"):
            wa_phone = clean_phone[1:]
        else:
            wa_phone = clean_phone
        buttons.append({
            "text": "📱 WhatsApp",
            "url": f"https://wa.me/{wa_phone}"
        })
    
    reply_markup = None
    if buttons:
        # Располагаем кнопки по одной в ряд
        reply_markup = {"inline_keyboard": [[btn] for btn in buttons]}
    
    # ── Отправляем ──
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
        result = resp.json()
        
        if not result.get("ok"):
            logger.error(f"Telegram API error: {result}")
            raise Exception(f"Telegram API: {result.get('description', 'Unknown error')}")
        
        logger.info(f"Notification sent, message_id={result['result']['message_id']}")
        return result


# ═══════════════════════════════════════════
# ENDPOINT'Ы
# ═══════════════════════════════════════════

@app.get("/")
async def root():
    return {"status": "BotHelp Webhook Bot is running ✅"}


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/webhook/bothelp")
async def bothelp_webhook(request: Request):
    """
    Основной endpoint для приёма вебхуков от BotHelp.
    BotHelp отправляет данные подписчика — мы отправляем уведомление в Telegram.
    """
    try:
        data = await request.json()
        logger.info(f"Received webhook: {str(data)[:500]}")
        
        await send_telegram_notification(data)
        return {"status": "ok", "message": "Notification sent"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Возвращаем 200 даже при ошибке, чтобы BotHelp не ретраил бесконечно
        return {"status": "error", "message": str(e)}


# Поддержка разных форматов BotHelp
@app.post("/webhook")
async def bothelp_webhook_alt(request: Request):
    """Альтернативный endpoint."""
    return await bothelp_webhook(request)


@app.post("/webhook/lead")
async def lead_webhook(request: Request):
    """Endpoint для лида."""
    return await bothelp_webhook(request)


# ═══════════════════════════════════════════
# ТОЧКА ВХОДА
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)