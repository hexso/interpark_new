from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys

ticket_id = sys.argv[1]  # 첫 번째 인자 (상품설명)
credential_file_name = sys.argv[2]  # 첫 번째 인자 (상품설명)
areas = []
if len(sys.argv) > 3:
    areas = sys.argv[2].replace(' ', '').split(',')

class Ticketer():

    def __init__(self, ticket_id):
        self.ticket_id = ticket_id

    def get_seat_list(self):
        '''
        앞의 3구역을 찾는다.
        :return: seats_list (정렬된 좌석 element 리스트)
        '''
        global areas
        seats_list = []

        #구역이 설정되지 않은경우 전체 좌석에서 찾는다.
        if len(areas) == 0 or (len(areas) == 1 and areas[0] == ''):
            seats = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "circle"))
            )
            seats_list.extend(seats)
        else:
            #배치구역에서 찾기.
            for area in areas:
                b_area = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"g#seat_block_001\\:{area}"))
                )
                if b_area != '':
                    seats = b_area.find_elements(By.TAG_NAME, "circle")
                    seats_list.extend(seats)

        print(f'총 {len(seats_list)}개의 좌석 확인')

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

    def login(self):
        self.driver.open(
            "https://accounts.interpark.com/authorize/ticket-pc?postProc=FULLSCREEN&origin=https%3A%2F%2Fticket.interpark.com%2FGate%2FTPLoginConfirmGate.asp%3FGroupCode%3D%26Tiki%3D%26Point%3D%26PlayDate%3D%26PlaySeq%3D%26HeartYN%3D%26TikiAutoPop%3D%26BookingBizCode%3D%26MemBizCD%3DWEBBR%26CPage%3D%26GPage%3Dhttps%253A%252F%252Ftickets.interpark.com%252F&version=v2")

        with open(credential_file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
        while True:
            try:
                login_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
                )
                break
            except:
                print("로그인버튼이 활성화 되지 않았습니다. 다시 시도해주세요.")
                continue


        # 첫 번째 줄: 아이디, 두 번째 줄: 패스워드
        username = lines[0].strip()
        password = lines[1].strip()

        username_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys(username)
        password_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_input.send_keys(password)
        login_button.click()

    def run(self):
        self.driver = Driver(uc=True)

        #로그인 완료 기다리기
        self.login()
        while True:
            try:
                if self.driver.get_current_url() == "https://tickets.interpark.com/":

                    break
            except:
                continue
            time.sleep(0.1)

        #상품 페이지로 이동
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

        button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'EntButton_button__bdl_j') and contains(@class, 'EntButton_primary__UOX1_')]"))
        )
        button.click()

if __name__ == '__main__':
    ticketer = Ticketer(ticket_id)
    ticketer.run()
