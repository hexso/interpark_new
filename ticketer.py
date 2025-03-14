from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QThread, pyqtSignal


class Ticketer(QThread):

    update_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.driver = Driver(uc=True)

    def get_seat_list(self):
        seats = WebDriverWait(self.driver, 5).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "circle"))
        )
        self.update_signal.emit(f'총 {len(seats)}개의 좌석 확인')
        return seats

    def sort_seats(self):
        '''
        좌석을 최대한 앞자리를 기준으로 0번부터 좌석을 정렬한다.
        :return: seats_list (정렬된 좌석 element 리스트)
        '''


    def run(self):

        seats = self.get_seat_list()

        # ✅ ActionChains를 사용하여 클릭 (권장)
        ActionChains(self.driver).move_to_element(seat).click().perform()

        button = self.driver.find_element("xpath",
                                     "//button[contains(@class, 'EntButton_button__bdl_j') and contains(@class, 'EntButton_primary__UOX1_')]")
        button.click()