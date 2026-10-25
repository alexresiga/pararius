import logging

import os
import sys
import requests
from selenium.webdriver.common.by import By
from seleniumbase import SB

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GROUP_ID = os.getenv('GROUP_ID')
SECTIONS_XPATH = "//div[contains(@class, 'listing-search-item__content')]"
# relative XPaths so they only match inside the given listing section
ELEMENT_XPATH = ".//a[contains(@class, 'listing-search-item__link listing-search-item__link--title')]"
PRICE_XPATH = ".//div[contains(@class, 'listing-search-item__price')]"


def escape_markdown(text):
    # Telegram's legacy Markdown fails the whole message on an unmatched entity character
    for char in ('\\', '_', '*', '`', '['):
        text = text.replace(char, f'\\{char}')
    return text


def send_message(chat_id, text):
    response = requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
    )
    if not response.ok:
        logger.error(f"telegram sendMessage failed ({response.status_code}): {response.text}")
    return response.ok


def get_latest(sb):
    """Returns True if the run succeeded, False if no listings were found or a message failed to send."""
    with open("seen.txt") as f:
        seen = set(f.read().split('\n'))
    # UC mode disconnects chromedriver while the page loads so Cloudflare's challenge doesn't detect automation
    sb.uc_open_with_reconnect("https://www.pararius.com/apartments/amsterdam/0-2250", 6)
    browser = sb.driver
    sections = browser.find_elements(By.XPATH, SECTIONS_XPATH)
    logger.info(f"page title: {browser.title!r}, url: {browser.current_url}, sections found: {len(sections)}")
    if not sections:
        source = browser.page_source
        if "Just a moment" in browser.title or "challenges.cloudflare.com" in source or "cf-chl" in source:
            logger.warning("blocked by Cloudflare challenge page")
        else:
            logger.warning(f"no Cloudflare challenge detected, listing markup may have changed. page start: {source[:500]!r}")
        send_message(CHAT_ID, "no sections")
        logger.info('😴😴😴')
        return False

    ok = True
    for section in sections[:3][::-1]:
        links = section.find_elements(By.XPATH, ELEMENT_XPATH)
        prices = section.find_elements(By.XPATH, PRICE_XPATH)
        if not links or not prices:
            logger.warning(f"listing is missing a title link or price, skipping: {section.text!r}")
            ok = False
            continue
        section_text = "\n".join(line for line in section.text.split('\n')[:-1] if line != "Save as favourite")
        href = links[0].get_attribute('href')
        price = prices[0].text.split()[0]
        if href in seen:
            send_message(CHAT_ID, escape_markdown(f"seen already, skipping {href}"))
            logger.info(f"seen already, skipping {href}")
            continue
        logger.info(f"[{price}]({href}) - {section_text}")
        if send_message(GROUP_ID, f"[{escape_markdown(price)}]({href}) - {escape_markdown(section_text)}"):
            # only mark as seen once delivered, so a failed send is retried next run
            with open("seen.txt", "a") as f:
                f.write(f"{href}\n")
        else:
            ok = False
    return ok


if __name__ == "__main__":
    missing = [name for name in ('TOKEN', 'CHAT_ID', 'GROUP_ID') if not os.getenv(name)]
    if missing:
        logger.error(f"missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    # xvfb gives Chrome a virtual display on Linux; headed Chrome is far less likely to be flagged than headless
    with SB(uc=True, xvfb=True) as sb:
        succeeded = get_latest(sb)
    # a non-zero exit fails the workflow run so GitHub sends a failure email instead of silently passing
    sys.exit(0 if succeeded else 1)
