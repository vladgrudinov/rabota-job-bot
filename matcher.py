"""
Умный модуль оценки вакансий:
- Не пропускает нормальные вакансии, где зарплата "по договоренности" / не указана.
- Если зарплата указана: проходит от 2300-2500 BYN (а с премиями/бонусами/KPI идет в зачет).
- Богатый словарь синонимов под все 4 сферы портфолио.
- Строгий отсев только реального мусора (продажи, склады, строители).
"""
import re
import json
from pathlib import Path
from bot_config import FILTER_SETTINGS, SEARCH_SETTINGS, PATHS

class VacancyMatcher:
    def __init__(self, profile_path: Path = PATHS["profile"]):
        self.profile = self._load_profile(profile_path)
        
        # Синонимы ролей для гибкого и широкого охвата
        self.role_keywords = [
            # Technical Support & IT Ops
            "support", "поддержк", "helpdesk", "service desk", "l1", "l2", "l3",
            "системный администратор", "сисадмин", "дежурный инженер", "технический специалист",
            "инженер-программист", "сопровождени", "траблшутинг",
            
            # Management & Operations
            "менеджер проектов", "project manager", "операционный менеджер",
            "координатор", "администратор", "управляющий", "руководитель",
            "заместитель", "менеджер по работе с клиентами", "account manager",
            "клиентский менеджер", "бизнес-ассистент", "помощник руководителя",
            
            # Fitness & Sport
            "тренер", "фитнес", "инструктор", "спорт", "персональный тренер",
            "тренажерн", "лфк", "оздоровительн",
            
            # IT Development & Data
            "python", "developer", "разработчик", "backend", "data engineer",
            "аналитик данных", "программист"
        ]

        # Базовые навыки
        raw_skills = self.profile.get("skills", {})
        self.all_skills = []
        if isinstance(raw_skills, dict):
            for cat, s_list in raw_skills.items():
                self.all_skills.extend([s.lower() for s in s_list])
        elif isinstance(raw_skills, list):
            self.all_skills = [s.lower() for s in raw_skills]

        self.min_salary = SEARCH_SETTINGS.get("min_salary_byn", 2500)
        self.title_stops = [w.lower() for w in FILTER_SETTINGS.get("title_stop_words", [])]
        self.desc_stops = [w.lower() for w in FILTER_SETTINGS.get("description_stop_words", [])]
        self.employer_stops = [e.lower() for e in FILTER_SETTINGS.get("employer_blacklist", [])]
        self.min_score = FILTER_SETTINGS.get("min_match_score", 15)

    def _load_profile(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def parse_salary_to_byn(self, salary_str: str) -> int | None:
        if not salary_str:
            return None

        cleaned = salary_str.replace(" ", "").replace("\xa0", "").lower()
        numbers = [int(n) for n in re.findall(r"\d+", cleaned)]
        if not numbers:
            return None

        amount = numbers[0]

        if "usd" in cleaned or "$" in cleaned:
            return int(amount * 3.3)
        elif "eur" in cleaned or "€" in cleaned:
            return int(amount * 3.6)
        elif "rub" in cleaned or "₽" in cleaned:
            return int(amount * 0.035)
        else:
            return amount

    def evaluate_vacancy(self, title: str, employer: str, salary_str: str,
                         description: str = "", tags: list = None) -> tuple[bool, int, str]:
        title_lower = title.lower()
        employer_lower = (employer or "").lower()
        desc_lower = (description or "").lower()
        tags_lower = [t.lower() for t in (tags or [])]
        full_text = f"{title_lower} {desc_lower} {' '.join(tags_lower)}"

        # 1. Черный список компаний
        for bad_emp in self.employer_stops:
            if bad_emp in employer_lower:
                return False, 0, f"Компания '{employer}' в черном списке"

        # 2. СТРОГИЕ СТОП-СЛОВА (только реальные продажи, склады, строители)
        for stop_word in self.title_stops:
            if stop_word in title_lower:
                return False, 0, f"Стоп-слово: '{stop_word}'"

        # Строительные, физические и заводские специальности
        industrial_stops = [
            "механик", "конструктор", "проектировщик", "теплогаз", "водоснабжен",
            "канализац", "сметчик", "чпу", "станк", "технолог", "электронщик",
            "овик", "электрик", "сантехник", "монтажник", "бурильщик", "наладчик",
            "геодезист", "архитектор", "агроном", "зоотехник"
        ]
        for ind_stop in industrial_stops:
            if ind_stop in title_lower:
                return False, 0, f"Непрофильный инженер: '{ind_stop}'"

        # Стоп-слова в описании
        for stop_word in self.desc_stops:
            if stop_word in desc_lower:
                return False, 0, f"Стоп-слово в описании: '{stop_word}'"

        # 3. УМНАЯ ПРОВЕРКА ЗАРПЛАТЫ
        salary_byn = self.parse_salary_to_byn(salary_str)
        has_bonuses = any(b in full_text for b in [
            "бонус", "преми", "kpi", "кпи", "процент", "%", "+", 
            "надбавк", "мотиваци", "доплат", "годовой бонус", "квартальн"
        ])
        
        # Если зарплата указана явно:
        if salary_byn is not None:
            # Учитываем бонусы (+500 BYN к базе)
            effective_salary = salary_byn + (500 if has_bonuses else 0)
            
            # Отсекаем только откровенно низкие ставки (меньше 2200 BYN)
            if salary_byn < 2200 and effective_salary < self.min_salary:
                return False, 10, f"З/п (~{salary_byn} BYN) ниже минимальной"

        # 4. СКОРИНГ СООТВЕТСТВИЯ РОЛИ И НАВЫКАМ
        score = 0
        matched_roles = []
        matched_skills = []

        # Попадание в одну из ролей портфолио
        for rk in self.role_keywords:
            if rk in title_lower:
                score += 30
                matched_roles.append(rk)
                break

        # Проверка навыков в тексте
        for skill in self.all_skills:
            pattern = r'(?<![a-zA-Z0-9_а-яА-Я])' + re.escape(skill) + r'(?![a-zA-Z0-9_а-яА-Я])'
            if re.search(pattern, full_text):
                matched_skills.append(skill)
                score += 5

        # Бонус за указанную достойную вилку
        if salary_byn and salary_byn >= 2500:
            score += 15

        # Если зарплата "по договоренности", но роль профильная - даем зеленый свет
        if salary_byn is None and matched_roles:
            score += 20

        score = min(100, score)

        # Решение: проходит, если набрало минимальный порог
        is_worthy = score >= self.min_score

        reason_parts = []
        if matched_roles:
            reason_parts.append(f"Роль: {matched_roles[0]}")
        if matched_skills:
            reason_parts.append(f"Навыки: {', '.join(matched_skills[:4])}")
        if salary_byn:
            reason_parts.append(f"З/п ~{salary_byn} BYN" + (" (+бонусы)" if has_bonuses else ""))
        else:
            reason_parts.append("З/п по договоренности")

        reason = " | ".join(reason_parts) if reason_parts else "Общие требования"

        return is_worthy, score, reason
