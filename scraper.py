import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class BettingSiteScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new") # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36")
        chrome_options.add_argument("--remote-debugging-port=9222") # Add remote debugging port
        chrome_options.add_argument("--disable-setuid-sandbox") # Added for sandbox environment
        chrome_options.add_argument("--disable-extensions") # Added to reduce overhead
        chrome_options.add_argument("--disable-browser-side-navigation") # Avoid issues with navigation
        chrome_options.add_argument("--disable-features=VizDisplayCompositor") # For display issues
        chrome_options.add_argument("--start-maximized") # Start in maximized mode
        chrome_options.add_argument("--window-size=1920,1080") # Set window size
        chrome_options.add_argument("--disable-infobars") # Disable infobars
        chrome_options.add_argument("--disable-notifications") # Disable notifications
        chrome_options.add_argument("--disable-popup-blocking") # Disable popup blocking
        chrome_options.add_argument("--disable-web-security") # Disable web security
        chrome_options.add_argument("--allow-running-insecure-content") # Allow insecure content
        chrome_options.add_argument("--no-first-run") # Skip first run wizard
        chrome_options.add_argument("--no-default-browser-check") # Skip default browser check
        chrome_options.add_argument("--disable-blink-features=AutomationControlled") # Bypass some bot detection

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # self.driver.maximize_window() # Already handled by --start-maximized
            return True
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False

    def scrape_sportybet(self, username, password):
        """Scrape SportyBet bet history"""
        logger.info("Starting SportyBet scraping...")

        if not self.setup_driver():
            return []

        try:
            self.driver.get("https://www.sportybet.com/ng/")

            # Wait for login elements
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "login-username"))
            )

            # Login
            self.driver.find_element(By.ID, "login-username").send_keys(username)
            self.driver.find_element(By.ID, "login-password").send_keys(password)
            self.driver.find_element(By.ID, "login-submit").click()

            # Wait for successful login
            WebDriverWait(self.driver, 30).until(
                EC.url_contains("sportybet.com/ng/sport/main")
            )

            # Handle account protection popup
            try:
                popup_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
                )
                popup_button.click()
                logger.info("Dismissed account protection popup")
            except:
                logger.info("No account protection popup found")

            # Navigate to bet history
            bet_history_link = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'bet-history') or contains(text(), 'Bet History')]"))
            )
            bet_history_link.click()

            # Wait for bet history to load
            time.sleep(5)

            # Scroll to load all history
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 10

            while scroll_attempts < max_scrolls:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1

            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return self.parse_sportybet_history(soup)

        except Exception as e:
            logger.error(f"Error scraping SportyBet: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def parse_sportybet_history(self, soup):
        """Parse SportyBet bet history from HTML"""
        bet_history = []

        # Look for various possible bet history containers
        bet_containers = (
            soup.find_all('div', class_=lambda x: x and 'bet' in x.lower() and 'history' in x.lower()) +
            soup.find_all('div', class_=lambda x: x and 'bet' in x.lower() and 'item' in x.lower()) +
            soup.find_all('tr', class_=lambda x: x and 'bet' in x.lower()) +
            soup.find_all('div', {'data-testid': lambda x: x and 'bet' in x.lower()})
        )

        for container in bet_containers:
            bet_data = {}

            # Extract bet ID
            bet_id = container.find(text=lambda x: x and 'bet id' in x.lower())
            if bet_id:
                bet_data['bet_id'] = bet_id.strip()

            # Extract status
            status_indicators = ['won', 'lost', 'pending', 'void', 'cancelled']
            for indicator in status_indicators:
                if container.find(text=lambda x: x and indicator in x.lower()):
                    bet_data['status'] = indicator.title()
                    break

            # Extract stake amount
            stake_text = container.find(text=lambda x: x and ('₦' in x or 'NGN' in x))
            if stake_text:
                bet_data['stake'] = stake_text.strip()

            # Extract date
            date_element = container.find('time') or container.find(attrs={'datetime': True})
            if date_element:
                bet_data['date'] = date_element.get('datetime', date_element.text.strip())

            if bet_data:  # Only add if we found some data
                bet_history.append(bet_data)

        logger.info(f"Parsed {len(bet_history)} bet records from SportyBet")
        return bet_history

    def scrape_bet9ja(self, username, password):
        """Scrape Bet9ja bet history"""
        logger.info("Starting Bet9ja scraping...")

        if not self.setup_driver():
            return []

        try:
            self.driver.get("https://web.bet9ja.com/")

            # Wait for login elements
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )

            # Login
            self.driver.find_element(By.NAME, "username").send_keys(username)
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Login']").click()

            # Wait for successful login
            time.sleep(5)

            # Navigate to bet history (this may vary based on Bet9ja's current structure)
            try:
                bet_history_link = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'history') or contains(text(), 'History')]"))
                )
                bet_history_link.click()
            except:
                logger.warning("Could not find bet history link for Bet9ja")
                return []

            time.sleep(5)

            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return self.parse_bet9ja_history(soup)

        except Exception as e:
            logger.error(f"Error scraping Bet9ja: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def parse_bet9ja_history(self, soup):
        """Parse Bet9ja bet history from HTML"""
        bet_history = []

        # Look for table rows or divs containing bet data
        bet_rows = soup.find_all('tr') + soup.find_all('div', class_=lambda x: x and 'bet' in x.lower())

        for row in bet_rows:
            bet_data = {}

            # Extract relevant data (this is a generic approach)
            text_content = row.get_text().lower()
            if any(keyword in text_content for keyword in ['bet', 'stake', 'win', 'loss']):
                bet_data['raw_content'] = row.get_text().strip()
                bet_history.append(bet_data)

        logger.info(f"Parsed {len(bet_history)} bet records from Bet9ja")
        return bet_history

    def scrape_msport(self, username, password):
        """Scrape MSport bet history"""
        logger.info("Starting MSport scraping...")

        if not self.setup_driver():
            return []

        try:
            # Use mobile user agent for MSport to avoid CAPTCHA
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
            })

            self.driver.get("https://www.msport.com/ng/")

            # Wait for login elements
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.NAME, "mobile"))
            )

            # Login
            self.driver.find_element(By.NAME, "mobile").send_keys(username)
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

            # Wait for successful login
            time.sleep(5)

            # Navigate to bet history
            try:
                bet_history_link = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'history') or contains(text(), 'History')]"))
                )
                bet_history_link.click()
            except:
                logger.warning("Could not find bet history link for MSport")
                return []

            time.sleep(5)

            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return self.parse_msport_history(soup)

        except Exception as e:
            logger.error(f"Error scraping MSport: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def parse_msport_history(self, soup):
        """Parse MSport bet history from HTML"""
        bet_history = []

        # Generic parsing approach for MSport
        bet_containers = soup.find_all('div', class_=lambda x: x and 'bet' in x.lower())

        for container in bet_containers:
            bet_data = {'raw_content': container.get_text().strip()}
            bet_history.append(bet_data)

        logger.info(f"Parsed {len(bet_history)} bet records from MSport")
        return bet_history

def scrape_all_sites(credentials):
    """
    Scrape all betting sites with provided credentials

    credentials format:
    {
        'sportybet': {'username': 'xxx', 'password': 'xxx'},
        'bet9ja': {'username': 'xxx', 'password': 'xxx'},
        'msport': {'username': 'xxx', 'password': 'xxx'}
    }
    """
    scraper = BettingSiteScraper(headless=True)  # Set to True for headless mode
    all_bet_history = {}

    # Scrape SportyBet
    if 'sportybet' in credentials:
        creds = credentials['sportybet']
        all_bet_history['sportybet'] = scraper.scrape_sportybet(creds['username'], creds['password'])

    # Scrape Bet9ja
    if 'bet9ja' in credentials:
        creds = credentials['bet9ja']
        all_bet_history['bet9ja'] = scraper.scrape_bet9ja(creds['username'], creds['password'])

    # Scrape MSport
    if 'msport' in credentials:
        creds = credentials['msport']
        all_bet_history['msport'] = scraper.scrape_msport(creds['username'], creds['password'])

    # Save all data to JSON
    with open('all_betting_history.json', 'w', encoding='utf-8') as f:
        json.dump(all_bet_history, f, ensure_ascii=False, indent=4)

    logger.info("All betting history saved to all_betting_history.json")
    return all_bet_history

# Example usage
if __name__ == "__main__":
    # Define credentials for all sites
    credentials = {
        'sportybet': {
            'username': '07068639238',
            'password': 'Harkins20'
        },
        'bet9ja': {
            'username': 'Dolani78',
            'password': 'Harkins20'  # or '*#Harkins20#*'
        },
        'msport': {
            'username': '8154175495',
            'password': 'Harkins20'
        }
    }

    # Scrape all sites
    result = scrape_all_sites(credentials)
    print("Scraping completed. Check all_betting_history.json for results.")

