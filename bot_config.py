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

# --- Поисковые параметры (максимальный охват под все навыки резюме) ---
SEARCH_SETTINGS = {
    "search_queries": [
        # 1. Technical Support & IT Systems (L2, Helpdesk, SysAdmin)
        "Техническая поддержка",
        "Technical Support",
        "L2 Support",
        "IT Support",
        "Системный администратор",
        "System Administrator",
        "Service Desk",
        "Helpdesk",
        "Инженер технической поддержки",
        "Инженер сопровождения",
        "Специалист по внедрению",
        "Дежурный инженер",
        
        # 2. Management, Operations, Coordination & Administrative
        "Менеджер проектов",
        "Project Manager",
        "Операционный менеджер",
        "Operations Manager",
        "Менеджер продукта",
        "Product Manager",
        "Координатор проектов",
        "Координатор",
        "Руководитель проектов",
        "Бизнес ассистент",
        "Помощник руководителя",
        "Account Manager",
        "Customer Success",
        "Управляющий",
        "Менеджер по логистике",
        "Менеджер по закупкам",
        "Офис менеджер",
        
        # 3. IT Development, QA, Data & Analytics
        "Python Developer",
        "Backend Developer",
        "Data Engineer",
        "Аналитик данных",
        "Data Analyst",
        "Системный аналитик",
        "Бизнес аналитик",
        "QA Engineer",
        "Тестировщик",
        
        # 4. Fitness, Sports & Health
        "Фитнес тренер",
        "Персональный тренер",
        "Инструктор тренажерного зала",
        "Инструктор",
    ],
    "area": 16,            # 16 = вся Беларусь (включая Минск)
    "experience": None,     # Любой опыт
    "schedule": None,       # Любой график
    "only_with_salary": False,
    # Умная зарплата: от 2400-2500 BYN (а с премиями/бонусами от 2700+ идет в зачет)
    "min_salary_byn": 2400,
    "max_search_pages": 4,
}

# --- Фильтрация вакансий и стоп-слова ---
FILTER_SETTINGS = {
    # Порог совпадения: 10% (максимально активный охват всех смежных ролей)
    "min_match_score": 10,

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

# --- Настройки имитации человека (защита от капчи и банов) ---
HUMAN_BEHAVIOR = {
    # Задержка между просмотром вакансий (в секундах) - естественный темп человека
    "min_delay_seconds": 4,
    "max_delay_seconds": 9,
    # Задержка между отправкой откликов
    "delay_between_applications_min": 12,
    "delay_between_applications_max": 24,
    # Суточный лимит откликов
    "max_daily_applications": 150,
    # Максимум откликов за один сеанс
    "max_session_applications": 25,
    # Рабочие часы бота
    "work_hours_start": 8,
    "work_hours_end": 23,
    "simulate_reading": True,
    "typing_delay_ms_range": (15, 35),
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
