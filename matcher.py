"""
Модуль интеллектуального сопоставления и скоринга вакансий по всем сферам портфолио.
"""
import re
import json
from pathlib import Path
from bot_config import FILTER_SETTINGS, SEARCH_SETTINGS, PATHS

class VacancyMatcher:
    def __init__(self, profile_path: Path = PATHS["profile"]):
        self.profile = self._load_profile(profile_path)
        self.target_roles = [r.lower() for r in self.profile.get("target_roles", [])]
        
        # Собираем все навыки из разных направлений (tech_support, management, fitness, it_dev)
        raw_skills = self.profile.get("skills", {})
        self.all_skills = []
        if isinstance(raw_skills, dict):
            for cat, s_list in raw_skills.items():
                self.all_skills.extend([s.lower() for s in s_list])
        elif isinstance(raw_skills, list):
            self.all_skills = [s.lower() for s in raw_skills]

        self.min_salary = SEARCH_SETTINGS.get("min_salary_byn", 2700)
        self.title_stops = [w.lower() for w in FILTER_SETTINGS.get("title_stop_words", [])]
        self.desc_stops = [w.lower() for w in FILTER_SETTINGS.get("description_stop_words", [])]
        self.employer_stops = [e.lower() for e in FILTER_SETTINGS.get("employer_blacklist", [])]
        self.min_score = FILTER_SETTINGS.get("min_match_score", 30)

    def _load_profile(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def parse_salary_to_byn(self, salary_str: str) -> int | None:
        """
        Парсит зарплату и переводит в BYN.
        """
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
        """
        Оценивает вакансию на соответствие портфолио и проверяет исключения.
        """
        title_lower = title.lower()
        employer_lower = (employer or "").lower()
        desc_lower = (description or "").lower()
        tags_lower = [t.lower() for t in (tags or [])]
        full_text = f"{title_lower} {desc_lower} {' '.join(tags_lower)}"

        # 1. Проверка черного списка компаний
        for bad_emp in self.employer_stops:
            if bad_emp in employer_lower:
                return False, 0, f"Компания '{employer}' в черном списке"

        # 2. СТРОГАЯ ПРОВЕРКА СТОП-СЛОВ В НАЗВАНИИ (продажи, склад, комплектовщик и т.д.)
        for stop_word in self.title_stops:
            if stop_word in title_lower:
                return False, 0, f"Стоп-слово: '{stop_word}'"

        # 3. СТОП-СЛОВА В ОПИСАНИИ (холодные звонки, активные продажи)
        for stop_word in self.desc_stops:
            if stop_word in desc_lower:
                return False, 0, f"Стоп-слово в описании: '{stop_word}'"

        # 4. ЖЕСТКИЙ ФИЛЬТР ЗАРПЛАТЫ (ОТ 2700 BYN)
        salary_byn = self.parse_salary_to_byn(salary_str)
        if salary_byn is not None:
            if salary_byn < self.min_salary:
                return False, 10, f"З/п (~{salary_byn} BYN) ниже минимальной ({self.min_salary} BYN)"

        # 5. Оценка соответствия портфолио
        score = 0
        matched_roles = []
        matched_skills = []

        # Проверка соответствия роли (Support, Менеджер, Тренер, Dev)
        for role in self.target_roles:
            if role in title_lower:
                score += 35
                matched_roles.append(role)
                break

        # Проверка ключевых навыков
        for skill in self.all_skills:
            pattern = r'(?<![a-zA-Z0-9_а-яА-Я])' + re.escape(skill) + r'(?![a-zA-Z0-9_а-яА-Я])'
            if re.search(pattern, full_text):
                matched_skills.append(skill)
                score += 6

        # Если зарплата явно указана и выше 2700 BYN - добавляем бонус
        if salary_byn and salary_byn >= self.min_salary:
            score += 20

        score = min(100, score)

        # Решение
        is_worthy = score >= self.min_score

        reason_parts = []
        if matched_roles:
            reason_parts.append(f"Роль: {matched_roles[0]}")
        if matched_skills:
            reason_parts.append(f"Навыки: {', '.join(matched_skills[:4])}")
        if salary_byn:
            reason_parts.append(f"З/п ~{salary_byn} BYN")

        reason = " | ".join(reason_parts) if reason_parts else "Общие требования"

        return is_worthy, score, reason
