"""
Конфигурация бота для rabota.by под все направления портфолио
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Поисковые параметры (все сферы портфолио) ---
SEARCH_SETTINGS = {
    "search_queries": [
        "Техническая поддержка",
        "Technical Support",
        "L2 Support",
        "IT Support",
        "Менеджер проектов",
        "Операционный менеджер",
        "Координатор",
        "Администратор",
        "Управляющий",
        "Фитнес тренер",
        "Персональный тренер",
        "Инструктор",
        "Python Developer",
        "Data Engineer",
    ],
    "area": 16,            # 16 = вся Беларусь (включая Минск)
    "experience": None,     # Любой опыт
    "schedule": None,       # Любой график
    "only_with_salary": False,
    # Умная зарплата: от 2500 BYN (а с премиями/бонусами от 2700+ идет в зачет)
    "min_salary_byn": 2500,
    "max_search_pages": 4,
}

# --- Фильтрация вакансий и стоп-слова ---
FILTER_SETTINGS = {
    # Порог совпадения: 20% (чтобы откликаться активнее на смежные и околопрофильные роли)
    "min_match_score": 20,

    # СТРОГИЕ СЛОВА-ИСКЛЮЧЕНИЯ В НАЗВАНИИ
    "title_stop_words": [
        "менеджер по продажам",
        "специалист по продажам",
        "продажи",
        "продажам",
        "продавец-консультант",
        "продавец консультант",
        "продавец",
        "комплектовщик",
        "сотрудник склада",
        "работник склада",
        "кладовщик",
        "грузчик",
        "стажер",
        "intern",
        "trainee",
        "кассир",
        "мерчендайзер",
        "курьер",
        "холодные звонки",
        "телемаркетинг",
        "оператор колл-центра",
        "оператор call",
        "агент по недвижимости",
        "риелтор",
    ],

    # СТОП-СЛОВА В ОПИСАНИИ ВАКАНСИИ
    "description_stop_words": [
        "холодные звонки",
        "холодная база",
        "активные продажи",
        "поиск новых клиентов",
        "план по продажам",
        "без оплаты",
        "бесплатная стажировка",
        "сетевой маркетинг",
        "разгрузка товара",
        "сборка заказов",
    ],

    # Черный список работодателей
    "employer_blacklist": [
        "Рога и Копыта",
    ],
}

# --- Ускоренные настройки имитации человека ---
HUMAN_BEHAVIOR = {
    # Задержка между действиями (в секундах)
    "min_delay_seconds": 2,
    "max_delay_seconds": 6,

    # Задержка между откликами (в секундах) - ускоренно
    "delay_between_applications_min": 10,
    "delay_between_applications_max": 20,

    # Суточный лимит откликов
    "max_daily_applications": 120,

    # Максимум откликов за один сеанс
    "max_session_applications": 40,

    # Рабочие часы бота
    "work_hours_start": 8,
    "work_hours_end": 23,

    "simulate_reading": True,
    "typing_delay_ms_range": (15, 40),
}

# --- Автоответчик на приглашения и сообщения HR ---
AUTO_RESPONDER = {
    "enabled": True,
    "respond_once_per_chat": True,
    "check_interval_seconds": 240, # Каждые 4 минуты
}

# --- Уведомления в Telegram ---
TELEGRAM_SETTINGS = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
}

# --- Пути ---
PATHS = {
    "profile": BASE_DIR / "candidate_profile.json",
    "db": BASE_DIR / "bot_data.db",
    "browser_storage": BASE_DIR / "browser_session",
}
