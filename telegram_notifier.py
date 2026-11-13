"""
Модуль отправки уведомлений в Telegram пользователю.
"""
import requests
import logging
from bot_config import TELEGRAM_SETTINGS

logger = logging.getLogger("JobBot.Telegram")

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_SETTINGS.get("bot_token", "").strip()
        self.chat_id = TELEGRAM_SETTINGS.get("chat_id", "").strip()
        self.enabled = bool(self.token and self.chat_id)
        if not self.enabled:
            logger.info("Telegram-уведомления отключены (токен или chat_id не указаны в настройках).")

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.enabled:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        try:
            r = requests.post(url, json=payload, timeout=8)
            if r.status_code == 200:
                return True
            else:
                logger.warning(f"Ошибка отправки в Telegram: {r.status_code} - {r.text}")
                return False
        except Exception as e:
            logger.warning(f"Исключение при отправке в Telegram: {e}")
            return False

    def notify_application_sent(self, title: str, employer: str, url: str, score: int):
        text = (
            f"🚀 <b>Новый отклик отправлен!</b>\n\n"
            f"💼 <b>Позиция:</b> {title}\n"
            f"🏢 <b>Компания:</b> {employer}\n"
            f"🎯 <b>Совпадение:</b> {score}%\n"
            f"🔗 <a href='{url}'>Открыть вакансию на rabota.by</a>"
        )
        self.send_message(text)

    def notify_invitation(self, employer: str, vacancy: str, message: str, reply_sent: str = None):
        text = (
            f"🎉 <b>ПРИГЛАШЕНИЕ ОТ HR!</b> 🎉\n\n"
            f"🏢 <b>Компания:</b> {employer}\n"
            f"💼 <b>Вакансия:</b> {vacancy}\n\n"
            f"💬 <b>Сообщение от HR:</b>\n<i>{message}</i>\n"
        )
        if reply_sent:
            text += f"\n🤖 <b>Бот уже ответил:</b>\n<i>{reply_sent}</i>"
        self.send_message(text)
