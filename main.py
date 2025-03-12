from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if __name__ == '__main__':

    driver = Driver(uc=True)
    seat = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "circle[id='seat_block_25002656\\:24001584\\:001\\:424']"))
    )
    # ✅ ActionChains를 사용하여 클릭 (권장)
    ActionChains(driver).move_to_element(seat).click().perform()

    button = driver.find_element("xpath",
        "//button[contains(@class, 'EntButton_button__bdl_j') and contains(@class, 'EntButton_primary__UOX1_')]")
    button.click()
