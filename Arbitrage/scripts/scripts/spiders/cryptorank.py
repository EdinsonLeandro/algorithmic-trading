import scrapy
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as OptionsChrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import numpy as np
import os, pickle, time, random
from collections import defaultdict


class CryptorankSpider(scrapy.Spider):
    name = 'cryptorank'
    allowed_domains = ['cryptorank.io']
    start_urls = ['https://cryptorank.io/']


    def __init__(self, input_spider):

        # Parameters
        self.delay = 15.5
        self.credentials = input_spider

        # These names should be extracted from the website "https://cryptorank.io/price/bnb/arbitrage"
        self.coins = ['bnb', 'solana', 'lido-staked-ether', 'ripple', 'dogecoin', 'toncoin', 'cardano', 'shiba-inu',
                      'avalanche', 'chainlink', 'tron', 'bitcoin-cash', 'polkadot', 'near-protocol', 'matic-network']

        # Move back one folder in order to reach "drivers". Number "1" set it.
        # https://softhints.com/python-change-directory-parent/
        drivers_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chromedriver.exe'

        # "executable_path" has been deprecated selenium python. Here is the solution
        # https://stackoverflow.com/questions/64717302/deprecationwarning-executable-path-has-been-deprecated-selenium-python
        # https://stackoverflow.com/questions/18707338/print-raw-string-from-variable-not-getting-the-answers
        self.drivers_dir = r'%s' %drivers_dir

        # Testing version directory
        self.testing_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chrome-win64_113/chrome.exe'

        option = OptionsChrome()
        option.add_argument('--disable-popup-blocking')

        self.driver = uc.Chrome(driver_executable_path=self.drivers_dir, options=option, browser_executable_path=self.testing_dir)
        self.driver.maximize_window()
        
        # Login to LinkedIn
        self.login()


    # https://www.selenium.dev/documentation/webdriver/waits/
    # https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html
    def pause_spider(self, driver, path):
        WebDriverWait(driver, timeout=self.delay).\
            until(EC.element_to_be_clickable((By.XPATH, path)))

        time.sleep( round(random.uniform(0.7, 1.1), 4) )


    def load_cookie(self, driver, path):
        """
        Function to load cookie from browser.
        """
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for item in cookies:
                driver.add_cookie(item)


    def save_cookie(self, driver, path):
        """
        Function to save cookies.
        """        
        with open(path, 'wb') as filehandler:
            pickle.dump(driver.get_cookies(), filehandler)


    def login(self):
        """Function to go to Cryptorank.io and login"""
        path_file = f"Data/Cookies/cryptorank_account.pkl"

        # # If there is a cookie, the web page goes directly to feed
        # if os.path.exists(path_file):
        #     self.driver.get(self.start_urls[0])
        #     self.load_cookie(self.driver, path_file)
        #     self.driver.get(self.start_urls[0])

        #     # Wait until "Home" icon is clickable.
        #     self.pause_spider(self.driver, "//div[@id='top-bar']/div/div/a")

        # else:
        # Open linkedIn in web browser
        self.driver.get(self.start_urls[0])

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//div[@id='top-bar']/div/div/a")

        # Click on "Sign Up"
        self.driver.find_element(By.XPATH, "//div[@class='sc-f053cd28-0 kEnaMQ']/button[2]").click()

        # Wait until "Log in" icon is clickable.
        self.pause_spider(self.driver, "//div[@aria-label='Sign Up']/div[2]/div[1]/div/a[2]")

        # Click "Log in"
        self.driver.find_element(By.XPATH, "//div[@aria-label='Sign Up']/div[2]/div[1]/div/a[2]").click()

        # Wait
        time.sleep(round(random.uniform(1.1, 1.5), 4))

        # Write email and password
        # https://www.selenium.dev/documentation/webdriver/elements/finders/
        self.driver.find_element(By.XPATH, "//input[@type='email']").send_keys(self.credentials[0])
        self.driver.find_element(By.XPATH, "//input[@type='password']").send_keys(self.credentials[1])

        # Wait
        time.sleep(round(random.uniform(0.7, 1.1), 4))

        # Press "Enter" after write. "Keys.RETURN" do the same
        # https://www.geeksforgeeks.org/special-keys-in-selenium-python/
        self.driver.find_element(By.XPATH, "//input[@type='password']").send_keys(Keys.ENTER)

        # self.save_cookie(self.driver, path_file)


    def get_website(self, url):
        # Get website
        self.driver.get(f"https://cryptorank.io/price/{url}/arbitrage")

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//div[@id='top-bar']/div/div/a")            

        # Input stablecoin
        input_stablecoin = self.driver.find_element(By.XPATH, "//input[@placeholder='Filter by pairs']")
        ActionChains(self.driver).send_keys_to_element(input_stablecoin, "USDT")\
                                    .pause(round(random.uniform(0.7, 1.1), 1))\
                                    .send_keys(Keys.ENTER)\
                                    .perform()

        # Input Centralized Exchange
        self.driver.find_element(By.XPATH, "//div[@class='sc-b6334aa-0 bFXahO']/button[3]").click()
        time.sleep( round(random.uniform(1.1, 1.5), 4) )


    def get_data(self):
        # # Get row names
        # rows = self.driver.find_elements(By.XPATH, "//tbody/tr/th/div/a[1]")
        # rows = [item.text for item in rows]

        # # Get column names
        # columns = self.driver.find_elements(By.XPATH, "//tbody/tr/th/div/a[1]")
        # columns = [item.text for item in columns]

        # Get row and column names
        rows_cols = self.driver.find_elements(By.XPATH, "//thead/tr/th/following::node()/a[contains(@href,'/exchanges/')]")
        rows_cols = [item.get_attribute('href') for item in rows_cols]

        # Get exchange names
        rows_cols = [item.split('/')[-1] for item in rows_cols]

        # Get number of rows
        n_cols = len(self.driver.find_elements(By.XPATH, "//thead/tr/th")) - 1

        # Get number of columns
        n_rows = len(self.driver.find_elements(By.XPATH, "//tbody/tr"))

        # Select row and column names based on the number of rows and columns.
        columns = rows_cols[:n_cols]
        rows = rows_cols[n_cols:n_rows + n_cols]

        # Get percentage data
        percentages = self.driver.find_elements(By.XPATH, "//tbody/tr/td/span")
        percentages = [item.text for item in percentages]
        percentages = [float(item.replace('%', '')) for item in percentages]

        while True:
            try:
                percentages = np.reshape(percentages, (n_rows, n_cols))
                break
            except:
                percentages.append(0.0)

        # Save data into dictionary
        data = defaultdict(list)

        for item in range(percentages.shape[1]):
            data[columns[item]] = percentages[:, item].tolist()

        return rows, data


    def parse(self, response):
        for coin in self.coins:
            # Get website and filter by "USDT" and "CEX"
            self.get_website(coin)

            # Get data
            indexes, raw_data = self.get_data()

            # Yield
            yield {'Cryptocurrency': coin,
                   'Arbitrage data': raw_data,
                   'Indexes' : indexes}

        self.driver.close()