from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == '__main__':

    driver = Driver(uc=True)
    button = driver.find_element("xpath",
        "//button[contains(@class, 'EntButton_button__bdl_j') and contains(@class, 'EntButton_primary__UOX1_')]")
    button.click()
