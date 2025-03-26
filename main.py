import logging

import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GROUP_ID = os.getenv('GROUP_ID')
SECTIONS_XPATH = "//div[contains(@class, 'listing-search-item__content')]"
ELEMENT_XPATH = "//a[contains(@class, 'listing-search-item__link listing-search-item__link--title')]"
PRICE_XPATH = "//div[contains(@class, 'listing-search-item__price')]"

def get_latest():
    seen = set(open("seen.txt").read().split('\n'))
    browser.get("https://www.pararius.com/apartments/amsterdam/0-2250")
    sections = browser.find_elements(By.XPATH, SECTIONS_XPATH)
    if sections:
        for index, section in enumerate(sections[:3][::-1]):
            section_text = "\n".join(section.text.split('\n')[:-1])
            href = section.find_elements(By.XPATH, ELEMENT_XPATH)[2 - index].get_attribute('href')
            price = section.find_elements(By.XPATH, PRICE_XPATH)[2 - index].text.split()[0]
            message = f"[{price}]({href}) - {section_text}"
            if href in seen:
                t = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&parse_mode=Markdown&text="seen already, skipping {href}"'
                requests.get(t)
                logger.info(f"seen already, skipping {href}")
            else:
                open("seen.txt", "a").write(f"{href}\n")
                logger.info(f"[{price}]({href}) - {section_text}")
                t = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={GROUP_ID}&parse_mode=Markdown&text={message}'
                response = requests.get(t)
    else:
        t = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&parse_mode=Markdown&text="no sections"'
        response = requests.get(t)
        logger.info('😴😴😴')


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--headless")
browser = webdriver.Chrome(options=chrome_options)

if __name__ == "__main__":
    get_latest()
    
