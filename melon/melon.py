from selenium.webdriver.common.by import By
import threading
import requests
import time
import datetime
import sys
import chromedriver_autoinstaller
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # 설치 필요
from selenium import webdriver

BEFORE_START_SEC = 2 #초단위
START_TIME_MILLI = 1500
# 일단 가우시안 말고 0.2초마다로 바꾸자.
optimized_time_offsets = [1.2]

class Melon(): # 브라우저 돌아가는 스레드
    def __init__(self, ticket_id, start_time, scheduleNo='100001'):
        self.running = True
        self.finished = False
        self.ticket_id = ticket_id
        self.scheduleNo = scheduleNo
        self.driver = None
        self.member_key = None
        self.driver = None
        self.tempkey = None
        self.nflActId = None
        self.real_key = None
        self.session = None
        self.lock = threading.Lock()
        self.start_time = start_time

    # 1. 아마 아이디마다 고유의 멤버키가 있을것으로 예상된다. 이것을 먼저 받아야 한다.
    def get_memberkey(self):
        url = "https://tktapi.melon.com/api/prersrv/usercond.json"
        params = {
            "prodId": self.ticket_id,
            "pocCode": "SC0002",
            "sellTypeCode": "ST0002",
            "sellCondNo": "1",
            "autheTypeCode": "BG0010",
            "btnType": "B",
            "v": "1",
            "requestservicetype": "P"
        }

        # User-Agent와 같은 헤더 설정
        headers = {
            "User-Agent": self.driver.execute_script("return navigator.userAgent;")  # 현재 브라우저의 User-Agent 가져오기
        }

        # `requests.Session()` 초기화
        session = requests.Session()

        # Selenium에서 쿠키 가져오기
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        response = session.get(url, headers=headers, params=params)
        member_key = response.json()['data']['memberKey']
        self.member_key = member_key
        return member_key

    #2. auth
    def do_auth(self):
        headers = {
            "User-Agent": self.driver.execute_script("return navigator.userAgent;")  # 현재 브라우저의 User-Agent 가져오기
        }
        url = f"https://tktapi.melon.com/api/v1/authorization/melon-member/identity-verification.json"
        params = {
            "memberKey": self.member_key,
            "ticketViewType": "minors",
            "requestservicetype": "P"
        }

        # `requests.Session()` 초기화
        session = requests.Session()

        # Selenium에서 쿠키 가져오기
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        response = session.get(url, headers=headers, params=params)
        return response

    #3. 일시적으로 생성되는 key 두개를 받는다. nflActId,key
    def get_temp_keys(self):
        headers = {
            "User-Agent": self.driver.execute_script("return navigator.userAgent;")  # 현재 브라우저의 User-Agent 가져오기
        }
        url = f"https://tktapi.melon.com/api/product/prodKey.json"
        params = {
            "prodId": self.ticket_id,
            "scheduleNo": self.scheduleNo,
            "v": "1",
            "requestservicetype": "P"
        }

        session = requests.Session()
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        response = session.get(url, headers=headers, params=params)
        return response

    # 4. nflActId,key들을 통해 실제 접속을 위한 key를 받는다
    def get_real_key(self, nflActid):
        headers = {
            "User-Agent": self.driver.execute_script("return navigator.userAgent;")  # 현재 브라우저의 User-Agent 가져오기
        }
        url = f"https://zam.melon.com/ts.wseq"
        params = {
            'opcode': '5101',
            'nfid': '0',
            'prefix': 'NetFunnel.gRtype=5101;',
            'sid': 'service_1',
            'aid': nflActid,
            'js': 'yes',
            'user_data': self.member_key,
            '1731322891240': ''
        }

        response = self.session.get(url, headers=headers, params=params)
        return response

    #5. 새로운 페이지 들어가기
    def enter_ticket_page(self, response_script):
        # Selenium을 사용하여 JavaScript 실행
        self.driver.refresh()
        time.sleep(2)
        button = self.driver.find_element(By.XPATH, "//dd[@class='cont_process']//button")
        button.click()
        time.sleep(1)
        button2 = self.driver.find_element(By.XPATH, "//*[@id='ticketReservation_Btn']")
        button2.click()
        time.sleep(0.5)
        self.driver.execute_script(response_script)

    def login(self):
        url = 'https://member.melon.com/muid/family/ticket/login/web/login_inform.htm?cpId=WP15&returnPage=https://ticket.melon.com/main/readingGate.htm'
        self.driver.get(url)
        while True:
            if 'member.melon' not in self.driver.current_url:
                return
            time.sleep(0.2)

    def run(self):

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        chromedriver_autoinstaller.install()
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        self.login()

        self.driver.get(f"https://ticket.melon.com/performance/index.htm?prodId={self.ticket_id}")

        # 현재 시간 불러오기
        target_time = datetime.datetime.strptime(start_time, "%H:%M:%S").time()
        now = datetime.datetime.now()
        target_time = datetime.datetime(now.year, now.month, now.day, target_time.hour, target_time.minute,
                                        target_time.second)
        print("예약 시작 시간까지 대기합니다..")

        # 예약 시작 시간 5초 전까지 대기
        while now < datetime.datetime(now.year, now.month, now.day, target_time.hour, target_time.minute,
                                      target_time.second) - datetime.timedelta(seconds=BEFORE_START_SEC):
            time.sleep(0.01)
            now = datetime.datetime.now()  # 현재 시간을 다시 업데이트

        print("자 들어갑니다")

        #멤버키를 먼저 받는다.
        self.get_memberkey()
        self.do_auth()

        self.threads = []

        # `requests.Session()` 초기화
        session = requests.Session()

        # Selenium에서 쿠키 가져오기
        for cookie in self.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        self.session = session

        real_key_list = []
        def get_key(target_time, time_offset):
            '''
            time_offset: 목표시간 대비
            :return:
            '''
            send_time = target_time - datetime.timedelta(milliseconds=time_offset)
            thread_response = None
            while datetime.datetime.now() < send_time:
                time.sleep(0.001)
            with self.lock:
                if self.nflActId == None:
                    thread_response = self.get_temp_keys()
                    thread_response = thread_response.json()
                    if 'key' in thread_response:
                        if thread_response['key'] != '':
                            self.nflActId = thread_response['nflActId']
                            print(f'nflActId를 획득했습니다. 값 {self.nflActId}')
                            response = self.get_real_key(self.nflActId)
                            response_script = response.text
                            real_key_list.append(response_script)
                            return

            with self.lock:
                if self.nflActId != None:
                    response = self.get_real_key(self.nflActId)
                    response_script = response.text
                    print(response_script)
                    real_key_list.append(response_script)
                    return



        for time_offset in optimized_time_offsets:
            print(f"target time : {time_offset}")
            thread = threading.Thread(target=get_key, args=(target_time, time_offset,))
            self.threads.append(thread)
            thread.start()

        for thread in self.threads:
            thread.join()

        for key in real_key_list:
            print(key)

        print('수행을 완료하였습니다.')
        while True:
            pass
            time.sleep(5)


if __name__ == '__main__':
    ticket_id = sys.argv[1]  # 첫 번째 인자 (상품설명)
    start_time = sys.argv[2]  # 시작 시간
    areas = []
    ticketer = Melon(ticket_id, start_time)
    ticketer.run()
