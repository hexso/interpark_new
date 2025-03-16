from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QThread, pyqtSignal
import time


class Ticketer(QThread):

    update_signal = pyqtSignal(str)

    def __init__(self, parent, ticket_id):
        super().__init__(parent)
        self.ticket_id = ticket_id

    def get_seat_list(self):
        '''
        앞의 3구역을 찾는다.
        :return: seats_list (정렬된 좌석 element 리스트)
        '''
        # seats = WebDriverWait(self.driver, 5).until(
        #     EC.presence_of_all_elements_located((By.TAG_NAME, "circle"))
        # )
        seats_list = []
        areas = ['006','007','008']
        # 배치도에 따라 다르게 설정될 수도 있음. 일단 앞 3구역만 찾기
        for area in areas:
            b_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"g#seat_block_001\\:{area}"))
            )
            if b_area != '':
                seats = b_area.find_elements(By.TAG_NAME, "circle")
                seats_list.extend(seats)

        self.update_signal.emit(f'총 {len(seats_list)}개의 좌석 확인')

        return seats_list

    def sort_seats(self, seat_list):
        seat_data = []
        for seat in seat_list:
            # ✅ 각 요소에서 cx, cy 속성 가져오기
            cx = float(seat.get_attribute("cx"))
            cy = float(seat.get_attribute("cy"))

            # ✅ (element, cx, cy) 튜플로 저장
            seat_data.append((seat, cx, cy))

        # ✅ cy 기준 오름차순 정렬
        # ✅ cy 값이 같은 경우, cx 값이 170과 가장 가까운 순으로 정렬
        sorted_seats = sorted(seat_data, key=lambda x: (x[2], abs(x[1] - 170)))
        sorted_seats_list = [element[0] for element in sorted_seats]
        return sorted_seats_list



    def run(self):
        self.driver = Driver(uc=True)
        self.driver.open(
            "https://accounts.interpark.com/authorize/ticket-pc?postProc=FULLSCREEN&origin=https%3A%2F%2Fticket.interpark.com%2FGate%2FTPLoginConfirmGate.asp%3FGroupCode%3D%26Tiki%3D%26Point%3D%26PlayDate%3D%26PlaySeq%3D%26HeartYN%3D%26TikiAutoPop%3D%26BookingBizCode%3D%26MemBizCD%3DWEBBR%26CPage%3D%26GPage%3Dhttps%253A%252F%252Ftickets.interpark.com%252F&version=v2")

        while True:
            try:
                if self.driver.get_current_url() == "https://tickets.interpark.com/":

                    break
            except:
                continue
            time.sleep(0.1)

        self.driver.get(f"https://tickets.interpark.com/goods/{self.ticket_id}")
        time.sleep(2)
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="productSide"]/div/div[2]/a[1]'))
        )
        element.click()

        while True:
            try:
                if self.driver.get_current_url() == "https://tickets.interpark.com/onestop/ko/seat":
                    break
            except:
                continue

        seats = self.get_seat_list()
        sorted_list = self.sort_seats(seats)
        for seat in sorted_list:
            if 'disabled' not in seat.get_attribute('class'):
                # ✅ ActionChains를 사용하여 클릭 (권장)
                ActionChains(self.driver).move_to_element(seat).click().perform()
                break


        button = self.driver.find_element("xpath",
                                     "//button[contains(@class, 'EntButton_button__bdl_j') and contains(@class, 'EntButton_primary__UOX1_')]")
        button.click()