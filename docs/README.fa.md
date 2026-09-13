Exit code: 0
Wall time: 0.7 seconds
Output:
# افزونهٔ Telegram برای Codex

این پروژه یک افزونهٔ محلی Codex برای مدیریت چندزبانهٔ Telegram، اتوماسیون
محتوا، سیاست مستقل هر مقصد، Telegram Web، Telegram Desktop، Bot API و MTProto
است.

## قابلیت‌ها

- خواندن، جست‌وجو، خلاصه‌سازی، نگارش، ترجمه، ارسال، ویرایش و فوروارد پیام
- کار با گفتگوهای خصوصی، گروه‌ها، کانال‌ها و رسانه‌ها
- ذخیرهٔ پیش‌نویس و مدیریت صف انتشار پایدار مبتنی بر SQLite
- سیاست‌های `draft-only`، `confirm-send` و `auto` برای هر مقصد
- استفاده از Chrome، مرورگر داخلی Codex، Telegram Desktop، Bot API و MTProto
- نگهداری credentialها خارج از مخزن

## امنیت اطلاعات

مقادیر واقعی زیر نباید در GitHub یا فایل‌های افزونه ثبت شوند:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_PHONE
```

فایل‌های session، پایگاه دادهٔ SQLite، `.env`، cache و log نیز توسط
`.gitignore` از انتشار حذف می‌شوند. دادهٔ محلی به‌طور پیش‌فرض در مسیر
`%LOCALAPPDATA%\Codex\telegram-plugin` ذخیره می‌شود.

## نصب وابستگی MTProto

```powershell
python -m pip install -r scripts/requirements-optional.txt
```

## وضعیت انتشار

این مخزن عمومی است، اما نرم‌افزار متن‌باز نیست. تمام حقوق محفوظ است و انتشار
عمومی سورس به‌معنای اعطای مجوز استفاده، کپی، تغییر یا توزیع نیست.

