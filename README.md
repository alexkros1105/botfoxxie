# BotHelp → Telegram Уведомления

Принимает вебхуки от BotHelp и отправляет красивые уведомления в Telegram.

## Что делает

1. BotHelp отправляет данные подписчика (имя, телефон, email, username)
2. Бот форматирует красивое сообщение с иконками
3. Отправляет в Telegram с кнопками:
   - 💬 Открыть диалог в BotHelp
   - 👤 Написать в Telegram
   - 📱 Написать в WhatsApp (если есть телефон)

## Как добавить бота в ГРУППУ

Чтобы бот писал в группу вместо личных сообщений:

1. Создайте группу в Telegram (или используйте существующую)
2. Добавьте бота в группу:
   - Откройте группу → Настройки → Добавить участника → найдите бота
3. Дайте боту права администратора (чтобы он мог отправлять сообщения)
4. Узнайте chat_id группы:
   - Отправьте любое сообщение в группу
   - Откройте: `https://api.telegram.org/botВАШ_ТОКЕН/getUpdates`
   - Найдите `"chat": {"id": -100...}` — это ID группы (начинается с -100)
5. Обновите CHAT_ID в настройках сервера

## Настройка BotHelp

1. В конструкторе бота BotHelp выберите действие **"Отправить данные подписчика через Webhook"**
2. В поле URL введите: `https://ВАШ_СЕРВЕР.ondigitalocean.app/webhook/bothelp`
3. Сохраните и опубликуйте бота

## Развёртывание

### На Render.com (бесплатно)

1. Создайте аккаунт на [render.com](https://render.com)
2. New → Web Service
3. Подключите GitHub репозиторий (или используйте Blueprint)
4. Настройте:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Добавьте Environment Variables:
   - `BOT_TOKEN` = ваш токен от @BotFather
   - `CHAT_ID` = ID чата/группы
6. Нажмите Deploy

### На DigitalOcean App Platform (бесплатно)

```bash
doctl apps create --spec render.yaml
```

## Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram бота от @BotFather | `7583211249:AAH...` |
| `CHAT_ID` | ID чата или группы | `1191653357` или `-1001234567890` |
| `PORT` | Порт сервера | `8000` |

## Тестирование

Отправьте тестовый запрос:

```bash
curl -X POST https://ВАШ_СЕРВЕР/webhook/bothelp \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван",
    "phone": "+79991234567",
    "email": "ivan@test.com",
    "messenger_username": "ivanuser",
    "messenger_id": "123456789",
    "bot_id": "bot123",
    "subscriber_id": "sub456",
    "source": "Бот "Английский""
  }'
```

## Формат данных от BotHelp

BotHelp может отправлять данные в разных форматах. Бот поддерживает следующие поля:

- `name` / `first_name` — Имя
- `last_name` — Фамилия
- `phone` / `phone_number` — Телефон
- `email` — Email
- `messenger_username` / `username` / `tg_username` — Username в Telegram
- `messenger_id` / `telegram_id` / `user_id` — ID пользователя
- `bot_id` / `bothelp_bot_id` — ID бота в BotHelp (для ссылки на диалог)
- `subscriber_id` / `id` — ID подписчика
- `source` / `bot_name` / `channel` — Источник лида
- `bothelp_chat_link` / `dialog_url` — Прямая ссылка на диалог
- `utm_source` — UTM-метка