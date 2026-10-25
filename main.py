import json
import logging

import os
import re
import sys
import time
import requests
from selenium.webdriver.common.by import By
from seleniumbase import SB

from closeness import Closeness

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GROUP_ID = os.getenv('GROUP_ID')
SECTIONS_XPATH = "//div[contains(@class, 'listing-search-item__content')]"
# relative XPaths so they only match inside the given listing section
ELEMENT_XPATH = ".//a[contains(@class, 'listing-search-item__link listing-search-item__link--title')]"
PRICE_XPATH = ".//div[contains(@class, 'listing-search-item__price')]"
# Dutch postcode as shown on a listing, e.g. "1061 MJ Amsterdam"
POSTCODE_RE = re.compile(r'\b(\d{4}) ?[A-Z]{2}\b')


def load_favourites():
    """Zip codes picked on the GitHub Pages map (index.html). Empty means listings get no closeness score."""
    try:
        with open("favourites.json") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


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
    return response


def report_problem(text):
    # problems go to the private chat so the group only ever gets listings
    logger.warning(text)
    # Telegram rejects messages over 4096 characters; leave room for escaping
    send_message(CHAT_ID, escape_markdown(text[:3500]))


def closeness_line(closeness, postcode):
    """First line of a listing message: 0-5 stars for how close it is to the favourite zip codes."""
    if not closeness.favourites:
        return ''
    if not postcode:
        return "☆☆☆☆☆ ?/5 · no zip code on the listing\n"
    result = closeness.score(postcode.group(1))
    if result is None:
        return f"☆☆☆☆☆ ?/5 · {postcode.group(1)} isn't on the map\n"
    score, km, nearest = result
    stars = '★' * score + '☆' * (5 - score)
    where = f"in {nearest}" if km == 0 and nearest == postcode.group(1) else f"{km:.1f} km from {nearest}"
    return f"{stars} {score}/5 · {where} {closeness.names[nearest]}\n"


def get_latest(sb):
    """Returns True if the run succeeded, False if no listings were found or a message failed to send."""
    with open("seen.txt") as f:
        seen = set(f.read().split('\n'))
    favourites = load_favourites()
    closeness = Closeness("amsterdam_pc4.geojson", favourites)
    logger.info(f"favourite zip codes: {', '.join(sorted(favourites)) or 'none, listings get no closeness score'}")
    # UC mode disconnects chromedriver while the page loads so Cloudflare's challenge doesn't detect automation
    sb.uc_open_with_reconnect("https://www.pararius.com/apartments/amsterdam/0-2250", 6)
    browser = sb.driver
    sections = browser.find_elements(By.XPATH, SECTIONS_XPATH)
    logger.info(f"page title: {browser.title!r}, url: {browser.current_url}, sections found: {len(sections)}")
    if not sections:
        source = browser.page_source
        if "Just a moment" in browser.title or "challenges.cloudflare.com" in source or "cf-chl" in source:
            report_problem(f"No listings found: blocked by Cloudflare challenge page (title {browser.title!r})")
        else:
            report_problem(
                f"No listings found and no Cloudflare challenge detected, listing markup may have changed.\n"
                f"title: {browser.title!r}\nurl: {browser.current_url}"
            )
            logger.warning(f"page start: {source[:500]!r}")
        return False

    ok = True
    # check every listing on the page, oldest first, so none are missed when several appear within an hour
    for section in sections[::-1]:
        links = section.find_elements(By.XPATH, ELEMENT_XPATH)
        prices = section.find_elements(By.XPATH, PRICE_XPATH)
        if not links or not prices:
            report_problem(f"Listing is missing a title link or price, markup may have changed. Skipped:\n{section.text}")
            ok = False
            continue
        section_text = "\n".join(line for line in section.text.split('\n')[:-1] if line != "Save as favourite")
        href = links[0].get_attribute('href')
        price = prices[0].text.split()[0]
        if href in seen:
            # log only; messaging every seen listing on the page would flood the chat each run
            logger.info(f"seen already, skipping {href}")
            continue
        score = closeness_line(closeness, POSTCODE_RE.search(section.text))
        logger.info(f"{score}[{price}]({href}) - {section_text}")
        response = send_message(GROUP_ID, f"{escape_markdown(score)}[{escape_markdown(price)}]({href}) - {escape_markdown(section_text)}")
        if response.ok:
            # only mark as seen once delivered, so a failed send is retried next run
            with open("seen.txt", "a") as f:
                f.write(f"{href}\n")
        else:
            report_problem(f"Failed to send {href} to the group ({response.status_code}): {response.text}\nIt will be retried next run.")
            ok = False
        # stay under Telegram's limit of 20 messages per minute to a group
        time.sleep(3)
    return ok


if __name__ == "__main__":
    missing = [name for name in ('TOKEN', 'CHAT_ID', 'GROUP_ID') if not os.getenv(name)]
    if missing:
        logger.error(f"missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    # xvfb gives Chrome a virtual display on Linux; headed Chrome is far less likely to be flagged than headless
    try:
        with SB(uc=True, xvfb=True) as sb:
            succeeded = get_latest(sb)
    except Exception as e:
        report_problem(f"Script crashed: {type(e).__name__}: {e}")
        raise
    # a non-zero exit fails the workflow run so GitHub sends a failure email instead of silently passing
    sys.exit(0 if succeeded else 1)
