from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox
from PyQt5.QtWidgets import QPushButton, QListWidget, QListWidgetItem, QGroupBox, QComboBox, QMessageBox, QTimeEdit, QCheckBox
from PyQt5.QtGui import QIntValidator, QIcon
from bs4 import BeautifulSoup
import datetime
import sys
import requests
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QProcess
import os

TIMESLEEP = 0.01
SCHEDULE_NO = '100001'
START_TIME_MILLI = 1500
REQUESTS_CNT = 5
key_list = []

headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'referer': 'https://tickets.melon.com/',
}

class ImportGoodsDetail(QThread):
    loadFinished = pyqtSignal(dict)
    printLog = pyqtSignal(str)

    def __init__(self, parent, ticket_id):
        super().__init__(parent)
        self.parent = parent
        self.ticket_id = ticket_id

    def run(self):
        #get title name
        url = f"https://ticket.melon.com/performance/index.htm?prodId={self.ticket_id}"
        response = requests.get(url, headers=headers)
        # BeautifulSoup 객체 생성
        soup = BeautifulSoup(response.text, 'html.parser')

        # <meta> 태그 중 property="og:title" 인 요소 찾기
        meta_tag = soup.find('meta', property='og:title')

        if meta_tag:
            title = meta_tag.get('content')
            print(title)
        else:
            title = "해당 타이틀을 찾을 수 없음. 그러나 정상작동할껄?"
            print("해당 메타 태그를 찾을 수 없습니다.")

        ticket_info_url = "https://tktapi.melon.com/api/product/schedule/daylist.json"
        params = {
            "prodId": self.ticket_id,
            "pocCode": "SC0002",
            "perfTypeCode": "GN0001",
            "sellTypeCode": "ST0002", #선예매는 ST0002, 일반예매는 ST0001 #Todo: 일반예매도 가능하게끔 개선 필요
            "corpCodeNo": "",
            "prodTypeCode": "PT0001", #일반 상품 PT0001 -> 이건 따로 수정할 필요 없어 보임
            "reflashYn": "N",  #일반 상품은 reflashYn=N이로 설정된다.
            "requestservicetype": "P"
        }
        
        response = requests.get(ticket_info_url, headers=headers, params=params)
        response = response.json()['data']
        print(response)

        genreName = ""
        goodsName = title

        sequences = []

        for data in response['perfDaylist']:
            sequences.append({
                'playSeq': data['groupSch'],
                'playDate': data['perfDay'],
                'playTime': '',
            })

        self.printLog.emit(f'공연 정보를 불러왔습니다.')

        self.loadFinished.emit({
            'genreName': genreName,
            'goodsName': goodsName,
            'playEndDate': '',
            'playStartDate': '',
            'sequences': sequences
        })

class Form(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.running = False
        self.tickets_detail = None

        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_clear_log.clicked.connect(self.lw_log.clear)
        self.btn_find.clicked.connect(self.fetch_goods_detail)

        self.processes = []

    def init_ui(self):
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowTitle('멜론 대기열 접속기')

        self.hbox_settings = QHBoxLayout()

        self.lb_id = QLabel('아이디')
        self.le_id = QLineEdit()

        self.lb_pw = QLabel('비밀번호')
        self.le_pw = QLineEdit()
        self.le_pw.setEchoMode(QLineEdit.Password)

        self.lb_ticket_id = QLabel('공연 ID')
        self.le_ticket_id = QLineEdit()
        # 숫자만 입력가능하게
        self.le_ticket_id.setValidator(QIntValidator())

        self.btn_find = QPushButton('공연 찾기')

        # 숫자만 입력가능하게
        self.le_ticket_id.setValidator(QIntValidator())

        self.hbox_settings.addWidget(self.lb_id)
        self.hbox_settings.addWidget(self.le_id)
        self.hbox_settings.addWidget(self.lb_pw)
        self.hbox_settings.addWidget(self.le_pw)
        self.hbox_settings.addWidget(self.lb_ticket_id)
        self.hbox_settings.addWidget(self.le_ticket_id)
        self.hbox_settings.addWidget(self.btn_find)

        self.gb_settings = QGroupBox('설정')
        self.gb_settings.setLayout(self.hbox_settings)

        self.vbox.addWidget(self.gb_settings)

        self.vbox_log = QVBoxLayout()
        self.lw_log = QListWidget()
        self.vbox_log.addWidget(self.lw_log)

        self.gb_ticket_detail = QGroupBox('공연 정보')
        self.hbox_ticket_detail = QHBoxLayout()

        self.lb_ticket_genre = QLabel('장르: ')
        self.lb_ticket_genre_value = QLabel('')

        self.lb_ticket_name = QLabel('공연명: ')
        self.lb_ticket_name_value = QLabel('')

        self.lb_ticket_start_date = QLabel('시작일: ')
        self.lb_ticket_start_date_value = QLabel('')

        self.lb_ticket_end_date = QLabel('종료일: ')
        self.lb_ticket_end_date_value = QLabel('')

        self.lb_ticket_seq = QLabel('회차: ')
        self.cmb_ticket_seq = QComboBox()
        # 콤보박스 내용물 크기에 맞게 조절
        self.cmb_ticket_seq.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lb_time = QLabel('예매 시작 시간: ')

        self.timeEdit = QTimeEdit()
        self.timeEdit.setDisplayFormat("HH:mm:ss")
        self.timeEdit.setTime(datetime.datetime.now().time())

        self.hbox_ticket_detail.addWidget(self.lb_ticket_genre)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_genre_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_name)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_name_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_start_date)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_start_date_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_end_date)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_end_date_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_seq)
        self.hbox_ticket_detail.addWidget(self.cmb_ticket_seq)
        self.hbox_ticket_detail.addWidget(self.lb_time)
        self.hbox_ticket_detail.addWidget(self.timeEdit)

        self.gb_ticket_detail.setLayout(self.hbox_ticket_detail)

        self.vbox.addWidget(self.gb_ticket_detail)

        self.gb_log = QGroupBox('로그')
        self.gb_log.setLayout(self.vbox_log)

        self.vbox.addWidget(self.gb_log)

        self.hbox_control = QHBoxLayout()

        self.btn_start = QPushButton('시작')
        self.btn_stop = QPushButton('중지')
        self.btn_stop.setEnabled(False)
        self.cb_pre_sales = QCheckBox('선예매')
        #돌릴 프로그램 개수
        self.lb_program_cnt = QLabel('프로그램 개수: ')
        self.sb_program_cnt = QSpinBox()
        self.sb_program_cnt.setMinimum(1)
        self.sb_program_cnt.setValue(1)
        
        #요청 스레드 개수
        self.lb_thread = QLabel("스레드 개수")
        self.sb_thread_count = QSpinBox()
        self.sb_thread_count.setMinimum(2)
        self.sb_thread_count.setMaximum(20)
        self.sb_thread_count.setValue(5)
        self.lb_pre_req = QLabel("스레드 선시작 (초)")
        self.sb_pre_req = QSpinBox()
        self.sb_pre_req.setMinimum(1)
        self.sb_pre_req.setMaximum(10)
        self.sb_pre_req.setValue(3)
        self.btn_clear_log = QPushButton('로그 지우기')

        self.hbox_control.addWidget(self.btn_start)
        self.hbox_control.addWidget(self.btn_stop)
        self.hbox_control.addWidget(self.cb_pre_sales)
        self.hbox_control.addWidget(self.lb_program_cnt)
        self.hbox_control.addWidget(self.sb_program_cnt)
        #self.hbox_control.addWidget(self.lb_thread)
        #self.hbox_control.addWidget(self.sb_thread_count)
        self.hbox_control.addWidget(self.lb_pre_req)
        self.hbox_control.addWidget(self.sb_pre_req)
        self.hbox_control.addWidget(self.btn_clear_log)

        self.gb_control = QGroupBox('제어')
        self.gb_control.setLayout(self.hbox_control)

        self.vbox.addWidget(self.gb_control)

    def copy_to_clipboard(self, text):
        """ 클립보드에 텍스트 복사 """
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        print(f"클립보드에 복사됨: {text}")

    def update_dynamic_list(self, process: QProcess):
        """ 동적으로 GUI에 리스트 값 추가 및 복사 버튼 생성 """
        output = process.readAllStandardOutput().data().decode().strip()
        process_id = str(process.processId())
        # 리스트 값을 추가
        if output:
            hbox = QHBoxLayout()
            lbl_value = QLabel(output)
            btn_copy = QPushButton("복사")
            btn_copy.clicked.connect(lambda checked, text=output: self.copy_to_clipboard(text))

            hbox.addWidget(lbl_value)
            hbox.addWidget(btn_copy)
            self.vbox_dynamic_dict[process_id].addLayout(hbox)

    def fetch_goods_detail(self):
        ticket_id = self.le_ticket_id.text().replace(' ', '')
        if ticket_id == '':
            QMessageBox.warning(self, '경고', '공연 ID를 입력해주세요.')
            return

        try:
            int(ticket_id)
        except:
            QMessageBox.warning(self, '경고', '공연 ID는 숫자로 입력해주세요.')
            return

        self.btn_find.setEnabled(False)
        self.importGoodsDetail = ImportGoodsDetail(self, ticket_id)
        self.importGoodsDetail.loadFinished.connect(self.loadFinished)
        self.importGoodsDetail.start()

    @pyqtSlot(dict)
    def loadFinished(self, data):
        self.btn_find.setEnabled(True)
        self.lb_ticket_genre_value.setText(data['genreName'])
        self.lb_ticket_genre_value.setStyleSheet('font-weight: bold; color: green;')
        self.lb_ticket_name_value.setText(data['goodsName'])
        self.lb_ticket_name_value.setStyleSheet('font-weight: bold; color: blue;')
        self.lb_ticket_start_date_value.setText(data['playStartDate'])
        self.lb_ticket_start_date_value.setStyleSheet('font-weight: bold; color: red;')
        self.lb_ticket_end_date_value.setText(data['playEndDate'])
        self.lb_ticket_end_date_value.setStyleSheet('font-weight: bold; color: red;')

        self.cmb_ticket_seq.clear()
        for seq in data['sequences']:
            self.cmb_ticket_seq.addItem(
                f"{seq['playSeq']}: {seq['playDate'][:4]}년 {seq['playDate'][4:6]}월 {seq['playDate'][6:8]}일 {seq['playTime'][:2]}시 {seq['playTime'][2:]}분")

        self.tickets_detail = data

    def start(self):
        inter_ticket_id = self.le_ticket_id.text().replace(' ', '')

        if inter_ticket_id == '':
            QMessageBox.warning(self, '경고', '공연 ID를 입력해주세요.')
            return

        try:
            int(inter_ticket_id)
        except:
            QMessageBox.warning(self, '경고', '공연 ID는 숫자로 입력해주세요.')
            return

        if self.tickets_detail is None:
            QMessageBox.warning(self, '경고', '공연 정보를 불러와주세요.')
            return


        start_time = self.timeEdit.text()

        # 동적으로 리스트를 표시할 그룹박스
        self.gb_dynamic_dict = {}
        self.vbox_dynamic_dict = {}

        for i in range(self.sb_program_cnt.value()):  # ✅ 각 검색어를 별도 프로세스로 실행
            process = QProcess(self)
            process.setProgram(sys.executable)  # 실행할 프로그램 (Python)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            melon_file_path = os.path.join(current_dir, "melon.py")

            process.setArguments([melon_file_path, str(inter_ticket_id), str(start_time)])  # ✅ 인덱스 값과 검색어 전달
            process.setProcessChannelMode(QProcess.MergedChannels)  # ✅ 표준출력(stdout) + 표준에러(stderr) 합치기
            process.readyReadStandardOutput.connect(lambda p=process: self.update_dynamic_list(p))
            process.readyReadStandardError.connect(lambda p=process: self.printLog(p))
            process.start()
            self.processes.append(process)

            #복사를 위한 QBOX 추가하기
            process_name = str(process.processId())
            qgbox = QGroupBox()
            qvbox = QVBoxLayout()
            qgbox.setLayout(qvbox)
            self.vbox.addWidget(qgbox)
            self.gb_dynamic_dict[process_name] = qgbox
            self.vbox_dynamic_dict[process_name] = qvbox

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    @pyqtSlot(str)
    def printLog(self, text):
        currenttime_str = datetime.datetime.now().strftime('%H:%M:%S')
        item = QListWidgetItem(f'[{currenttime_str}] {text}')
        self.lw_log.addItem(item)

        if self.lw_log.count() > 400:
            self.lw_log.takeItem(0)

        self.lw_log.scrollToBottom()

    @pyqtSlot()
    def taskDone(self):
        self.worker.driver.quit()
        self.worker.quit()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.printLog('프로그램이 종료되었습니다.')

    def stop(self):
        self.btn_stop.setEnabled(False)
        self.printLog('브라우저를 중지 중입니다...')
        for process in self.processes:
            process.terminate()
        self.processes = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    sys.exit(app.exec_())