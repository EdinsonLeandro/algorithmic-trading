import os, time, random, subprocess
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from typing import Tuple


# --- Configuration ---
# Keeping selectors and settings in one place makes the script easier to maintain.
class Config:
    """Holds all static configuration variables for the scraper."""
    BASE_URL = 'https://www.hfm.com/int/en/'
    LOGIN_URL = 'https://my.hfm.com/en/int/login'

    DEFAULT_WAIT_TIME = 30  # Max time in seconds to wait for an element

    # Using more stable CSS selectors where possible
    COOKIES_ACCEPT_BUTTON = "button.orejime-Button--save"
    LOGIN_USERNAME_INPUT = "#emailPhone"
    LOGIN_PASSWORD_INPUT = "#password"
    WALLET = "[data-testid='wallet_balance']"


# --- Main Scraper Class ---
class HfmLogIn:
    """
    A standalone Selenium scraper for HFM copy trading strategies.
    It logs in, navigates, and scrapes provider data into a CSV file.
    """
    def __init__(self, credentials):
        self.credentials = credentials
        
        # Initialize the browser instance
        self._create_driver_instance()

        # Initialize WebDriverWait for element interactions
        self.wait = WebDriverWait(self.driver, Config.DEFAULT_WAIT_TIME)


    @staticmethod
    def _get_driver_paths() -> Tuple[str, str]:
        """
        Determines the paths for the chromedriver executable and the browser executable.
        """
        base_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir)*2)
        drivers_dir = os.path.join(base_dir, 'drivers', 'chromedriver.exe')
        testing_dir = os.path.join(base_dir, 'drivers', 'chrome-win64_113', 'chrome.exe')
        
        return drivers_dir, testing_dir


    def _create_driver_instance(self) -> uc.Chrome:
        """
        Creates a new instance of the Chrome WebDriver with the necessary options.
        """
        drivers_dir, testing_dir = self._get_driver_paths()
        
        # Configure Chrome options
        option = Options()
        option.add_argument('--disable-popup-blocking')

        # Initialize the undetected Chrome driver
        try:
            self.driver = uc.Chrome(driver_executable_path=drivers_dir, options=option, browser_executable_path=testing_dir)
            self.driver.maximize_window()

            # Navigate to the starting URL. Give time to: open a new tab, solve CAPTCHA and close the tab.
            self.driver.get(Config.BASE_URL)
            time.sleep(random.uniform(15.5, 19.5))

            print("Driver instance created successfully.")

        except Exception as e:
            print(f"Error creating driver instance: {e}")
            raise


    def _wait_and_click(self, by, value):
        """
        Waits for an element to be clickable, then safely clicks it.
        """
        try:
            # Wait for the element to be clickable
            element = self.wait.until(EC.element_to_be_clickable((by, value)))
            
            # Short pause before click for stability
            time.sleep(random.uniform(2, 4))
            element.click()

        except ElementClickInterceptedException:
            # If a regular click is blocked, use JavaScript to force the click
            print(f"Warning: Element '{value}' was intercepted. Trying JavaScript click.")
            element = self.driver.find_element(by, value)
            self.driver.execute_script("arguments[0].click();", element)

        except TimeoutException:
            print(f"Error: Timed out waiting for element '{value}'.")
            raise


    def login(self):
        """
        Handles the entire login process, including cookie handling.
        """
        # Accept cookies if the banner appears (robustly handles cases where it doesn't)
        try:
            self._wait_and_click(By.CSS_SELECTOR, Config.COOKIES_ACCEPT_BUTTON)
            print("Accepted cookies.")
        except TimeoutException:
            print("Cookie banner not found or timed out.")

        print("Starting login process")
        self.driver.get(Config.BASE_URL)

        # Navigate to the login page
        self.driver.get(Config.LOGIN_URL)
        print("Navigated to login page.")

        # Fill credentials and submit
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, Config.LOGIN_USERNAME_INPUT)))
        self.driver.find_element(By.CSS_SELECTOR, Config.LOGIN_USERNAME_INPUT).send_keys(self.credentials['email'])
        time.sleep(random.uniform(2, 4))

        # Wait for the password field to be visible and fill it
        password_field = self.driver.find_element(By.CSS_SELECTOR, Config.LOGIN_PASSWORD_INPUT)
        password_field.send_keys(self.credentials['password'])
        time.sleep(random.uniform(2, 4))

        password_field.submit()  # .submit() is cleaner than sending an ENTER key
        
        print("\nCredentials submitted. Please complete 2FA in the browser window.")
        # Wait for the user to complete 2FA and the dashboard to load
        try:
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, Config.WALLET)))
            
            # Allow time for the dashboard to fully load
            time.sleep(random.uniform(2, 4)) 
            print("Login successful, dashboard loaded.")
        except TimeoutException:
            print("Login failed or took too long after 2FA. Exiting.")
            self.close()
            exit()


    def run(self) -> uc.Chrome:
        """
        Executes the full scraping process from start to finish.
        """
        try:
            # Logging in
            self.login()

            return self.driver

        except Exception as e:
            print(f"An unexpected error occurred during the process: {e}")
            self.close()


    def close(self):
        """
        Closes the WebDriver session.
        """
        print("Closing browser.")

        # Ensure all browsers are closed even if an error occurs
        subprocess.call(["taskkill","/F","/IM","chrome.exe"])


# --- Execution Block ---
if __name__ == "__main__":

    # Load .env file
    load_dotenv()

    # --- Get Credentials Securely ---
    user_email = os.getenv("HFM_EMAIL")
    user_password = os.getenv("HFM_PASSWORD")

    if not user_email or not user_password:
        print("Email and password are required. Exiting.")
    else:
        user_credentials = {'email': user_email, 'password': user_password}
        
        # Initialize and run the scraper
        scraper = HfmLogIn(credentials=user_credentials)
        scraper.run()

        breakpoint()