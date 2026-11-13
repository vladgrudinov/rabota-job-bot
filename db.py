"""
Модуль работы с базой данных SQLite для учета вакансий, откликов и переписок.
"""
import sqlite3
from datetime import datetime, date
from pathlib import Path
from bot_config import PATHS

class Database:
    def __init__(self, db_path: Path = PATHS["db"]):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица вакансий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    employer TEXT,
                    salary_raw TEXT,
                    url TEXT,
                    match_score INTEGER,
                    match_reason TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица отправленных откликов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vacancy_id TEXT UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cover_letter TEXT,
                    status TEXT DEFAULT 'sent',
                    FOREIGN KEY(vacancy_id) REFERENCES vacancies(id)
                )
            """)

            # Таблица диалогов и приглашений от HR
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    negotiation_id TEXT PRIMARY KEY,
                    employer_name TEXT,
                    vacancy_title TEXT,
                    has_invitation INTEGER DEFAULT 0,
                    last_hr_message TEXT,
                    bot_replied INTEGER DEFAULT 0,
                    bot_reply_text TEXT,
                    replied_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_vacancy_processed(self, vacancy_id: str) -> bool:
        """Проверяет, сохранялась ли вакансия уже в базе (была ли проверена или обработана)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM vacancies WHERE id = ?", (str(vacancy_id),))
            return cursor.fetchone() is not None

    def has_applied(self, vacancy_id: str) -> bool:
        """Проверяет, был ли уже отправлен отклик на эту вакансию."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM applications WHERE vacancy_id = ?", (str(vacancy_id),))
            return cursor.fetchone() is not None

    def save_vacancy(self, vacancy_id: str, title: str, employer: str, salary_raw: str,
                     url: str, match_score: int, match_reason: str, status: str):
        """Сохраняет найденную вакансию и результат её скоринга."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO vacancies 
                (id, title, employer, salary_raw, url, match_score, match_reason, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(vacancy_id), title, employer, salary_raw, url, match_score, match_reason, status))
            conn.commit()

    def record_application(self, vacancy_id: str, cover_letter: str, status: str = "sent"):
        """Фиксирует факт успешного отклика."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO applications (vacancy_id, cover_letter, status, applied_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (str(vacancy_id), cover_letter, status))
            cursor.execute("""
                UPDATE vacancies SET status = 'applied' WHERE id = ?
            """, (str(vacancy_id),))
            conn.commit()

    def get_today_application_count(self) -> int:
        """Возвращает количество откликов, отправленных сегодня (для контроля лимитов)."""
        today_str = date.today().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM applications 
                WHERE date(applied_at) = date(?)
            """, (today_str,))
            return cursor.fetchone()[0]

    def has_replied_to_chat(self, negotiation_id: str) -> bool:
        """Проверяет, отвечал ли бот уже на это приглашение."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bot_replied FROM chats WHERE negotiation_id = ?", (str(negotiation_id),))
            row = cursor.fetchone()
            return bool(row and row["bot_replied"])

    def record_chat(self, negotiation_id: str, employer_name: str, vacancy_title: str,
                    has_invitation: bool, last_hr_message: str):
        """Сохраняет или обновляет информацию о диалоге с работодателем."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chats (negotiation_id, employer_name, vacancy_title, has_invitation, last_hr_message)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(negotiation_id) DO UPDATE SET
                    employer_name=excluded.employer_name,
                    vacancy_title=excluded.vacancy_title,
                    has_invitation=excluded.has_invitation,
                    last_hr_message=excluded.last_hr_message,
                    updated_at=CURRENT_TIMESTAMP
            """, (str(negotiation_id), employer_name, vacancy_title, int(has_invitation), last_hr_message))
            conn.commit()

    def mark_chat_replied(self, negotiation_id: str, reply_text: str):
        """Отмечает, что бот ответил на приглашение/сообщение HR."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE chats 
                SET bot_replied = 1, bot_reply_text = ?, replied_at = CURRENT_TIMESTAMP
                WHERE negotiation_id = ?
            """, (reply_text, str(negotiation_id)))
            conn.commit()

    def get_stats(self) -> dict:
        """Возвращает общую статистику работы бота."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vacancies")
            total_vacancies = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM applications")
            total_applied = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM chats WHERE has_invitation = 1")
            total_invitations = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM chats WHERE bot_replied = 1")
            total_replied = cursor.fetchone()[0]

            return {
                "total_vacancies_seen": total_vacancies,
                "total_applied": total_applied,
                "today_applied": self.get_today_application_count(),
                "total_invitations": total_invitations,
                "total_replies_sent": total_replied,
            }
