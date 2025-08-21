import time, subprocess, random
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from hfm_log import HfmLogIn
import re

# --- Configuration ---
# Keeping selectors and settings in one place makes the script easier to maintain.
class Config:
    """
    Holds all static configuration variables for the scraper.
    """
    COPY_TRADING_URL = 'https://my.hfm.com/en/copy-trading/performance'

    DEFAULT_WAIT_TIME = 60  # Max time in seconds to wait for an element

    # Using more stable CSS selectors where possible
    VIEW_ALL = "(//a[contains(@class, 'viewAll')])[1]"
    NEXT_PAGE_BUTTON = "//div[contains(@class,'hfPaginator')]/a[9]"
    LAST_PAGE = "//div[contains(@class,'hfPaginator')]/a[8]"
    STRATEGY_CARD = "table.hfDataTable.collapsed > tbody > tr > td > div > a"
    SORT_LIST = "//div[contains(@class, 'performance_sortDropDown')]"
    LIST_VIEW = "//button[contains(@class, 'hfButton btn-icon btn-secondary')]"


# --- Main Scraper Class ---
class HfmUserId:
    """
    A standalone Selenium scraper for HFM copy trading strategies.
    It logs in, navigates, and scrapes provider data into a CSV file.
    """
    def __init__(self, driver):
        # Store the WebDriver instance
        self.driver = driver

        # Initialize WebDriverWait for element interactions
        self.wait = WebDriverWait(self.driver, Config.DEFAULT_WAIT_TIME)


    def _wait_and_click(self, by, value):
        """
        Waits for an element to be clickable, then safely clicks it.
        """
        try:
            # Wait for the element to be clickable
            element = self.wait.until(EC.element_to_be_clickable((by, value)))
            
            # Short pause before click for stability
            time.sleep(random.uniform(2, 4))

            self.driver.execute_script("arguments[0].click();", element)

        except TimeoutException:
            print(f"Error: Timed out waiting for element '{value}'.")
            raise


    def _navigate_to_strategies(self):
        """
        Navigates from the dashboard to the strategy list page.
        """
        print("Navigating to HFcopy strategies...")

        # Navigate to the copy trading page
        self.driver.get(Config.COPY_TRADING_URL)

        # Confirm page load by waiting for the first "View All" button
        self.wait.until(EC.visibility_of_element_located((By.XPATH, Config.VIEW_ALL)))
        time.sleep(random.uniform(2, 4))  # Allow time for dynamic content to load

        print("Strategy list page loaded.")


    def _check_list_view(self):
        """
        Checks if the list view is displayed correctly. It's important because in this view the ID's will be visible
        """
        try:
            # If finding the element return errors, it means the list view is already displayed
            self.driver.find_element(By.XPATH, Config.SORT_LIST)

            # Click the list view button
            self._wait_and_click(By.XPATH, Config.LIST_VIEW)

            # Wait for the last page element to be visible
            self.wait.until(EC.visibility_of_element_located((By.XPATH, Config.LAST_PAGE)))

            print("List view is displayed.")

        except:
            print("List view already displayed.")


    def _scrape_user_names_id(self):
        """
        Scrapes provider data from all pages and returns it as a list of dicts.
        """
        print("Starting scrape...")
        scraped_data = []

        # Get the last page element
        last_page = int(self.driver.find_element(By.XPATH, Config.LAST_PAGE).text.strip())

        for page_count in range(last_page-1):
            print(f"Scraping page {page_count}")

            # Wait for the strategy cards to be present on the current page
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, Config.STRATEGY_CARD)))
            time.sleep(random.uniform(2, 4)) # Wait for any dynamic content to settle

            # Get all strategy profiles on the current page
            profiles = self.driver.find_elements(By.CSS_SELECTOR, Config.STRATEGY_CARD)
            for profile in profiles:
                try:
                    # Extract the provider name and ID
                    name = profile.find_element(By.CSS_SELECTOR, "div > b").text.strip()
                    id = profile.find_element(By.CSS_SELECTOR, "div > div > span").text.strip()

                    match = re.search("\d+", id)
                    if match:
                        id = match.group()
                    else:
                        id = None
                        print(f"Warning: No valid ID found in '{id}'.")

                    scraped_data.append({'Provider name': name, 'ID': id})
                except NoSuchElementException:
                    print("Warning: Could not extract details for one profile on this page.")

            # Attempt to click the 'Next' page button
            try:
                self._wait_and_click(By.XPATH, Config.NEXT_PAGE_BUTTON)
                page_count += 1
            except NoSuchElementException:
                print("\nLast page reached. No 'Next' button found.")
                break
        
        print(f"Scraping finished. Found {len(scraped_data)} total providers.")

        return scraped_data


    def run(self):
        """
        Executes the full scraping process from start to finish.
        """
        try:
            # Navigating to the strategies page
            self._navigate_to_strategies()

            # Check if the list view is displayed
            self._check_list_view()

            # Scrape user names
            data = self._scrape_user_names_id()

            return data

        except Exception as e:
            print(f"An unexpected error occurred during the process: {e}")
            self.close()

        # finally:
        #     self.close()


    def close(self):
        """
        Closes the WebDriver session.
        """
        print("Closing browser.")

        # Ensure all browsers are closed even if an error occurs
        subprocess.call(["taskkill","/F","/IM","chrome.exe"])


# --- Execution Block ---
if __name__ == "__main__":
    # Initialize and run the scraper to log in
    driver = HfmLogIn().run()

    scraper = HfmUserId(driver=driver)
    data = scraper.run()

    pd.DataFrame(data).to_csv("hfm_users.csv", index=False)
