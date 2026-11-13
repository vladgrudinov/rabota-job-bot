"""
Облачный скрипт для запуска в GitHub Actions (100% бесплатно 24/7).
Загружает сохраненную сессию auth_storage_state.json, откликается на вакансии
от 2700 BYN и отвечает на сообщения от HR.
"""
import sys
import os
import time
import logging
from pathlib import Path

# UTF-8 вывод
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("CloudHunter")

from playwright.sync_api import sync_playwright
from bot_config import SEARCH_SETTINGS, FILTER_SETTINGS, HUMAN_BEHAVIOR
from db import Database
from matcher import VacancyMatcher
from ai_communicator import AICommunicator
from telegram_notifier import TelegramNotifier

def run_cloud_session():
    logger.info("=" * 65)
    logger.info("  RABOTA.BY CLOUD HUNTER (GITHUB ACTIONS / 24/7 CLOUD)")
    logger.info("=" * 65)

    storage_state_file = BASE_DIR / "auth_storage_state.json"
    if not storage_state_file.exists():
        logger.error(f"Файл сессии {storage_state_file} не найден!")
        return

    db = Database(BASE_DIR / "bot_data.db")
    matcher = VacancyMatcher(BASE_DIR / "candidate_profile.json")
    ai = AICommunicator(BASE_DIR / "candidate_profile.json")
    telegram = TelegramNotifier()

    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    
    # Загружаем сохраненную авторизованную сессию
    context = browser.new_context(
        storage_state=str(storage_state_file),
        viewport={"width": 1366, "height": 768},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    try:
        # 1. Проверяем валидность сессии
        logger.info("[1/3] Проверка авторизации на rabota.by...")
        page.goto("https://rabota.by/applicant/resumes", wait_until="domcontentloaded")
        time.sleep(3)

        if "login" in page.url or "signup" in page.url:
            logger.error("Сессия устарела или требует повторной авторизации.")
            return

        logger.info(f"Авторизация активна! URL: {page.url}")

        # 2. Проверка сообщений и приглашений от HR
        logger.info("[2/3] Проверка новых сообщений и приглашений от работодателей в https://rabota.by/chat...")
        try:
            page.goto("https://rabota.by/chat", wait_until="domcontentloaded")
            time.sleep(3)

            # Закрываем баннер cookie
            c_btn = page.query_selector("button:has-text('Принять')") or page.query_selector("[data-qa*='cookie']")
            if c_btn:
                try:
                    c_btn.click(force=True)
                    time.sleep(0.5)
                except Exception:
                    pass

            chat_elements = page.query_selector_all("a[href*='/chat/']")
            chat_urls = []
            for cl in chat_elements:
                href = cl.get_attribute("href")
                if href and "/chat/" in href:
                    clean_url = href.split("?")[0]
                    if clean_url not in chat_urls:
                        chat_urls.append(clean_url)

            logger.info(f"Найдено диалогов в списке чатов: {len(chat_urls)}")

            for href in chat_urls[:10]:
                try:
                    full_url = f"https://rabota.by{href}" if href.startswith("/") else href
                    chat_id = href.split("/")[-1]

                    page.goto(full_url, wait_until="domcontentloaded")
                    time.sleep(2)

                    bubbles = page.query_selector_all("[data-qa='chat-bubble-message']")
                    if not bubbles:
                        continue

                    last_b = bubbles[-1]
                    box = last_b.bounding_box()
                    x_pos = box["x"] if box else 0
                    last_msg = last_b.inner_text().strip()

                    # Если X > 700 - последнее сообщение от нас
                    if x_pos > 700:
                        continue

                    msg_lower = last_msg.lower()
                    if "к сожалению" in msg_lower or msg_lower.startswith("отказ") or \
                       "спасибо за ответы" in msg_lower or "вынуждены отказать" in msg_lower:
                        continue

                    header_h1 = page.query_selector("h1") or page.query_selector("h2")
                    vac_title = header_h1.inner_text().strip() if header_h1 else "Вакансия"
                    emp_name = "Работодатель"

                    logger.info(f"[!] Неотвеченное сообщение от работодателя ({full_url}): «{last_msg[:80]}...»")

                    reply_text = ai.generate_invitation_reply(emp_name, vac_title, last_msg)

                    inp = page.locator("textarea[data-qa='text-input']")
                    if inp.is_visible():
                        inp.fill(reply_text)
                        time.sleep(1)

                        send_btn = page.locator("button[data-qa='record-complete']")
                        if send_btn.is_visible():
                            send_btn.click(force=True)
                        else:
                            page.keyboard.press("Enter")

                        time.sleep(2)
                        logger.info(f"[+] ОТВЕТ УСПЕШНО ОТПРАВЛЕН В ЧАТ {chat_id}!")
                        db.record_chat(chat_id, emp_name, vac_title, True, last_msg)
                        db.mark_chat_replied(chat_id, reply_text)
                        telegram.notify_invitation(emp_name, vac_title, last_msg, reply_text)

                except Exception as inner_e:
                    logger.debug(f"Ошибка диалога {href}: {inner_e}")
                    continue

        except Exception as e:
            logger.error(f"Ошибка проверки диалогов: {e}")

        # 3. Сканирование вакансий и отклики
        logger.info("[3/3] Сканирование вакансий (фильтр: от 2700 BYN, стоп-слова исключены)...")
        queries = SEARCH_SETTINGS.get("search_queries", ["Technical Support", "Менеджер", "Python"])
        
        session_applied = 0
        session_limit = 12  # До 12 откликов за один облачный запуск

        for query in queries:
            if session_applied >= session_limit:
                break

            logger.info(f"--- Поиск по направлению: '{query}' ---")
            search_url = f"https://rabota.by/search/vacancy?text={query}&area=16&page=0"
            page.goto(search_url, wait_until="domcontentloaded")
            time.sleep(3)

            # Сначала извлекаем все ссылки на странице поиска в чистый список строк
            links = page.query_selector_all("a[data-qa='serp-item__title']") or \
                    page.query_selector_all("a[href*='/vacancy/']")

            urls_to_visit = []
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    import re
                    m = re.search(r'/vacancy/(\d+)', href)
                    if m:
                        vac_id = m.group(1)
                        if vac_id not in seen_ids and not db.is_vacancy_processed(vac_id) and not db.has_applied(vac_id):
                            seen_ids.add(vac_id)
                            urls_to_visit.append((vac_id, f"https://rabota.by/vacancy/{vac_id}"))
                except Exception:
                    continue

            logger.info(f"Найдено новых вакансий для анализа: {len(urls_to_visit)}")

            # Теперь безопасно обходим каждую вакансию
            for vac_id, vac_url in urls_to_visit:
                if session_applied >= session_limit:
                    break
                page.goto(vac_url, wait_until="domcontentloaded")
                time.sleep(2)

                # Извлекаем параметры вакансии
                title_el = page.query_selector("h1")
                emp_el = page.query_selector("[data-qa='vacancy-company-name']")
                sal_el = page.query_selector("[data-qa='vacancy-salary']")
                desc_el = page.query_selector("[data-qa='vacancy-description']")

                title = title_el.inner_text().strip() if title_el else ""
                employer = emp_el.inner_text().strip() if emp_el else ""
                salary = sal_el.inner_text().strip() if sal_el else ""
                desc = desc_el.inner_text().strip() if desc_el else ""
                tags = [t.inner_text().strip() for t in page.query_selector_all("[data-qa='bloko-tag__text']")]

                # Оценка
                is_worthy, score, reason = matcher.evaluate_vacancy(
                    title=title, employer=employer, salary_str=salary,
                    description=desc, tags=tags
                )

                if not is_worthy:
                    logger.info(f"[-] Пропуск ({score}%): {title} [{reason}]")
                    db.save_vacancy(vac_id, title, employer, salary, vac_url, score, reason, "skipped_filter")
                    continue

                logger.info(f"[+] ДОСТОЙНАЯ ({score}%): {title} | {employer} [{reason}]")

                # Проверяем кнопку отклика
                apply_btn = page.query_selector("[data-qa='vacancy-response-link-top']")
                if not apply_btn or "откликнулись" in page.content().lower():
                    db.save_vacancy(vac_id, title, employer, salary, vac_url, score, reason, "already_applied")
                    continue

                cover_letter = ai.generate_cover_letter(title, employer, tags, desc)
                apply_btn.click()
                time.sleep(3)

                # Если есть textarea для сопроводительного
                txt_area = page.query_selector("textarea[data-qa='vacancy-response-popup-form-letter-input']") or \
                           page.query_selector("textarea")
                if txt_area and txt_area.is_visible():
                    txt_area.fill(cover_letter)
                    time.sleep(1)

                sub_btn = page.query_selector("[data-qa='vacancy-response-submit-popup']") or \
                          page.query_selector("button:has-text('Откликнуться')") or \
                          page.query_selector("button:has-text('Отправить отклик')")

                if sub_btn and sub_btn.is_visible():
                    sub_btn.click()
                    time.sleep(2)

                session_applied += 1
                db.save_vacancy(vac_id, title, employer, salary, vac_url, score, reason, "applied")
                db.record_application(vac_id, cover_letter, "sent")
                logger.info(f"[+++] ОБЛАЧНЫЙ ОТКЛИК №{session_applied} ОТПРАВЛЕН: {title} в {employer}!")
                telegram.notify_application_sent(title, employer, vac_url, score)

                # Пауза между откликами
                time.sleep(12)

    except Exception as e:
        logger.error(f"Исключение во время сессии: {e}", exc_info=True)
    finally:
        browser.close()
        p.stop()
        logger.info(f"Сессия завершена. Отправлено откликов за запуск: {session_applied}")

if __name__ == "__main__":
    run_cloud_session()
