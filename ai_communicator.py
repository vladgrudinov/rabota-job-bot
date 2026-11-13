"""
Модуль генерации персональных сопроводительных писем и ответов HR
под все направления портфолио: Technical Support L2, Менеджмент, Фитнес, IT.
"""
import random
import json
from pathlib import Path
from bot_config import PATHS

class AICommunicator:
    def __init__(self, profile_path: Path = PATHS["profile"]):
        self.profile = self._load_profile(profile_path)
        self.name = self.profile.get("name", "Владислав")
        self.contacts = self.profile.get("contacts", {})
        self.skills_dict = self.profile.get("skills", {})

    def _load_profile(self, path: Path) -> dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _detect_category(self, title: str, description: str) -> str:
        """Определяет сферу вакансии для подбора идеального стиля письма."""
        text = f"{title.lower()} {description.lower()}"
        
        if any(w in text for w in ["support", "поддержк", "helpdesk", "l2", "инцидент", "service desk"]):
            return "tech_support"
        elif any(w in text for w in ["тренер", "фитнес", "инструктор", "спорт", "тренажерн"]):
            return "fitness"
        elif any(w in text for w in ["python", "developer", "разработчик", "backend", "data engineer", "программист"]):
            return "it_dev"
        else:
            return "management"

    def generate_cover_letter(self, vacancy_title: str, employer: str,
                              matched_skills: list[str] = None, description: str = "") -> str:
        """Генерирует индивидуальное сопроводительное письмо под конкретное направление."""
        category = self._detect_category(vacancy_title, description)
        
        greetings = [
            f"Здравствуйте, команда {employer}!",
            f"Добрый день!",
            f"Здравствуйте!",
            f"Добрый день, команда {employer}!"
        ]

        if category == "tech_support":
            openings = [
                f"Заинтересовала ваша вакансия «{vacancy_title}». Имею практический опыт в технической поддержке уровня L2, решении сложных инцидентов и сопровождении систем.",
                f"Пишу вам по поводу позиции «{vacancy_title}» в {employer}. Мой бэкграунд в техподдержке и траблшутинге отлично подходит под заявленные задачи."
            ]
            body = (
                "Умею быстро локализовать неисправности, работать по SLA, корректно маршрутизировать задачи и поддерживать высокий стандарт коммуникации с пользователями. "
                "Ориентируюсь на стабильную работу сервисов и качественное решение инцидентов."
            )
            cta = "Буду рад пообщаться на интервью и подробнее обсудить стек сервисов вашей команды."

        elif category == "fitness":
            openings = [
                f"Добрый день! С интересом ознакомился с вакансией «{vacancy_title}» в {employer}. Хочу предложить свой опыт в сфере фитнеса и персонального тренинга.",
                f"Меня привлекла вакансия «{vacancy_title}». Имею опыт ведения клиентов, составления индивидуальных тренировочных планов и рекомендаций по питанию."
            ]
            body = (
                "В работе делаю упор на безопасность, правильную технику выполнения упражнений и поддержание долгосрочной мотивации подопечных. "
                "Умею находить общий язык с клиентами разного уровня подготовки и выстраивать доверительные отношения."
            )
            cta = "Готов встретиться лично или созвониться, чтобы обсудить возможности сотрудничества."

        elif category == "it_dev":
            openings = [
                f"Меня заинтересовала вакансия «{vacancy_title}» в {employer}. Мой технический опыт разработки и работы с данными отлично соотносится с требованиями роли.",
                f"Увидел вакансию «{vacancy_title}» и хочу предложить свою кандидатуру."
            ]
            body = (
                "В работе фокусируюсь на создании производительных и надежных сервисов, проектировании чистого кода и быстрой интеграции с базами данных и внешними API."
            )
            cta = "Буду рад обсудить задачи на техническом интервью или выполнить тестовое задание."

        else: # management / coordination / operations
            openings = [
                f"С интересом ознакомился с вакансией «{vacancy_title}» в компании {employer}. Мой опыт в координации процессов и решении комплексных организационных задач соответствует вашим требованиям.",
                f"Пишу по поводу вакансии «{vacancy_title}». Уверен, что мои навыки управления и структурирования процессов принесут пользу вашей компании."
            ]
            body = (
                "Ответственно подхожу к контролю сроков, выстраиванию взаимодействия между отделами и соблюдению регламентов. "
                "Всегда ориентирован на прозрачность процессов и достижение измеримого результата."
            )
            cta = "Буду рад ответить на вопросы на онлайн-созвоне в удобное для вас время."

        tg = self.contacts.get("telegram", "@vlad_marshmallow (https://t.me/vlad_marshmallow)")
        phone = self.contacts.get("phone", "")
        contacts_str = f" (Telegram: {tg}, тел.: {phone})" if phone else f" (Telegram: {tg})"

        letter = (
            f"{random.choice(greetings)}\n\n"
            f"{random.choice(openings)}\n\n"
            f"{body}\n\n"
            f"{cta}\n\n"
            f"С уважением,\n{self.name}{contacts_str}"
        )
        return letter

    def generate_invitation_reply(self, employer: str, vacancy_title: str, hr_message: str = "") -> str:
        """Вежливый, четкий ответ на приглашение HR."""
        tg = self.contacts.get("telegram", "@vlad_marshmallow (https://t.me/vlad_marshmallow)")
        phone = self.contacts.get("phone", "")
        contacts_str = f"Telegram: {tg}, телефон: {phone}" if phone else f"Telegram: {tg}"

        templates = [
            f"Добрый день! Благодарю за приглашение на вакансию «{vacancy_title}». Предложение мне интересно. Подскажите, пожалуйста, в какие дни и время вам удобно организовать созвон? Мои контакты для оперативной связи: {contacts_str}.",
            f"Здравствуйте! Спасибо за обратную связь. Вакансия «{vacancy_title}» привлекательна для меня, готов пообщаться и обсудить детали. В какое время вам удобно провести встречу? Контакты: {contacts_str}.",
            f"Добрый день! Большое спасибо за приглашение. С удовольствием отвечу на все вопросы по опыту. Жду информации по удобному времени для звонка. Связь со мной: {contacts_str}."
        ]
        return random.choice(templates)
