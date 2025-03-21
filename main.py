from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox
from PyQt5.QtWidgets import QPushButton, QListWidget, QListWidgetItem, QGroupBox, QComboBox, QMessageBox, QTimeEdit, QCheckBox
from PyQt5.QtWidgets import QDialog, QRadioButton, QDoubleSpinBox
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QProcess
from PyQt5.QtGui import QIntValidator, QIcon, QPixmap
import datetime
import requests
import sys

class ImportGoodsDetail(QThread):
    loadFinished = pyqtSignal(dict)
    printLog = pyqtSignal(str)

    def __init__(self, parent, ticket_id):
        super().__init__(parent)
        self.parent = parent
        self.ticket_id = ticket_id

    def run(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'referer': 'https://tickets.interpark.com/',
        }
        summary_url = f"https://api-ticketfront.interpark.com/v1/goods/{self.ticket_id}/summary?goodsCode={self.ticket_id}&priceGrade=&seatGrade="
        response = requests.get(summary_url, headers=headers)
        response = response.json()['data']

        genreName = response['genreName']
        goodsName = response['goodsName']
        playEndDate = response['playEndDate']
        playStartDate = response['playStartDate']

        goodsCode = response['goodsCode']
        placeCode = response['placeCode']

        seq_url = f"https://api-ticketfront.interpark.com/v1/goods/24011622/playSeq?endDate={playEndDate}&goodsCode={self.ticket_id}&isBookableDate=true&page=1&pageSize=1550&startDate={playStartDate}"
        response = requests.get(seq_url, headers=headers)
        response = response.json()['data']

        sequences = []

        for data in response:
            sequences.append({
                'playSeq': data['playSeq'],
                'playDate': data['playDate'],
                'playTime': data['playTime'],
            })

        self.printLog.emit(f'공연 정보를 불러왔습니다.')

        self.loadFinished.emit({
            'genreName': genreName,
            'goodsName': goodsName,
            'playEndDate': playEndDate,
            'playStartDate': playStartDate,
            'sequences': sequences,
            'goodsCode': goodsCode,
            'placeCode': placeCode,
        })


class Form(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.processes = []
        self.auto_reselect = False

        self.running = False
        self.tickets_detail = None

        self.btn_start.clicked.connect(self.start)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_clear_log.clicked.connect(self.lw_log.clear)
        self.btn_find.clicked.connect(self.fetch_goods_detail)

    def init_ui(self):
        self.vbox = QVBoxLayout()
        self.setLayout(self.vbox)

        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowTitle('Interpark Receiver')

        self.vbox_log = QVBoxLayout()
        self.lw_log = QListWidget()
        self.vbox_log.addWidget(self.lw_log)

        self.gb_ticket_detail = QGroupBox('공연 정보')
        self.hbox_ticket_detail = QHBoxLayout()

        self.lb_ticket_id = QLabel('공연 ID')
        self.le_ticket_id = QLineEdit()
        self.le_ticket_id.setPlaceholderText('공연 ID를 입력해주세요.')
        self.le_ticket_id.setFixedWidth(150)

        self.btn_find = QPushButton('공연 찾기')

        self.cb_global = QCheckBox('글로벌 예매')
        self.cb_wait = QCheckBox('자동 대기열 진입')
        self.cb_wait.setChecked(True)  # ✅ 기본값을 체크 상태로 설정

        self.lb_ticket_genre = QLabel('장르: ')
        self.lb_ticket_genre_value = QLabel('')

        self.lb_ticket_name = QLabel('공연명: ')
        self.lb_ticket_name_value = QLabel('')

        self.lb_ticket_start_date = QLabel('시작일: ')
        self.lb_ticket_start_date_value = QLabel('')

        self.lb_ticket_end_date = QLabel('종료일: ')
        self.lb_ticket_end_date_value = QLabel('')

        self.hbox_ticket_detail.addWidget(self.lb_ticket_id)
        self.hbox_ticket_detail.addWidget(self.le_ticket_id)
        self.hbox_ticket_detail.addWidget(self.btn_find)
        self.hbox_ticket_detail.addWidget(self.cb_global)
        self.hbox_ticket_detail.addWidget(self.cb_wait)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_genre)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_genre_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_name)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_name_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_start_date)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_start_date_value)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_end_date)
        self.hbox_ticket_detail.addWidget(self.lb_ticket_end_date_value)

        self.gb_ticket_detail.setLayout(self.hbox_ticket_detail)

        self.vbox.addWidget(self.gb_ticket_detail)

        self.gb_seq_detail = QGroupBox('회차 정보')
        self.hbox_seq_detail = QHBoxLayout()

        # 몇명이나 예매할지
        self.lb_ticket_count = QLabel('연석: ')
        self.sb_ticket_count = QSpinBox()
        self.sb_ticket_count.setMinimum(1)
        self.sb_ticket_count.setMaximum(5)
        self.sb_ticket_count.setValue(1)

        #돌릴 프로그램 개수
        self.lb_program_cnt = QLabel('프로그램 개수: ')
        self.sb_program_cnt = QSpinBox()
        self.sb_program_cnt.setMinimum(1)
        self.sb_program_cnt.setValue(1)

        #좌석배치구역
        self.le_area = QLineEdit()
        self.le_area.setPlaceholderText('좌석구역 ex:)001,002,003')
        self.le_area.setFixedWidth(100)

        self.rb_left = QRadioButton('좌측 우선')
        self.rb_left.setChecked(True)
        self.rb_middle = QRadioButton('중앙 우선')
        self.rb_right = QRadioButton('우측 우선')

        self.lb_time = QLabel('예매 시작 시간: ')

        self.timeEdit = QTimeEdit()
        self.timeEdit.setDisplayFormat("HH:mm:ss")
        self.timeEdit.setTime(datetime.datetime.now().time())

        self.hbox_seq_detail.addWidget(self.lb_ticket_count)
        self.hbox_seq_detail.addWidget(self.sb_ticket_count)
        self.hbox_seq_detail.addWidget(self.lb_program_cnt)
        self.hbox_seq_detail.addWidget(self.sb_program_cnt)
        self.hbox_seq_detail.addWidget(self.le_area)
        self.hbox_seq_detail.addWidget(self.rb_left)
        self.hbox_seq_detail.addWidget(self.rb_middle)
        self.hbox_seq_detail.addWidget(self.rb_right)
        self.hbox_seq_detail.addWidget(self.lb_time)
        self.hbox_seq_detail.addWidget(self.timeEdit)

        self.gb_seq_detail.setLayout(self.hbox_seq_detail)
        self.vbox.addWidget(self.gb_seq_detail)

        self.gb_log = QGroupBox('로그')
        self.gb_log.setLayout(self.vbox_log)

        self.vbox.addWidget(self.gb_log)

        self.hbox_control = QHBoxLayout()

        self.btn_start = QPushButton('시작')
        self.btn_stop = QPushButton('중지')
        self.btn_stop.setEnabled(False)
        self.cb_pre_sales = QCheckBox('선예매')
        self.lb_thread = QLabel("스레드 개수")
        self.sb_thread_count = QSpinBox()
        self.sb_thread_count.setMinimum(2)
        self.sb_thread_count.setMaximum(20)
        self.sb_thread_count.setValue(5)
        self.lb_pre_req = QLabel("스레드 선시작 (초)")
        self.sb_pre_req = QDoubleSpinBox()
        self.sb_pre_req.setMinimum(0.001)
        self.sb_pre_req.setMaximum(10.0)
        self.sb_pre_req.setValue(3.0)
        self.sb_pre_req.setSingleStep(0.1)
        self.sb_pre_req.setDecimals(3)
        # 캡챠 딜레이 컨트롤 추가
        self.lb_captcha_delay = QLabel("캡챠 딜레이 (초)")
        self.sb_captcha_delay = QDoubleSpinBox()
        self.sb_captcha_delay.setMinimum(0.001)
        self.sb_captcha_delay.setMaximum(5.0)
        self.sb_captcha_delay.setValue(0.5)
        self.sb_captcha_delay.setSingleStep(0.1)
        self.sb_captcha_delay.setDecimals(3)
        self.btn_clear_log = QPushButton('로그 지우기')

        self.hbox_control.addWidget(self.btn_start)
        self.hbox_control.addWidget(self.btn_stop)
        self.hbox_control.addWidget(self.cb_pre_sales)
        self.hbox_control.addWidget(self.lb_thread)
        self.hbox_control.addWidget(self.sb_thread_count)
        self.hbox_control.addWidget(self.lb_pre_req)
        self.hbox_control.addWidget(self.sb_pre_req)
        self.hbox_control.addWidget(self.lb_captcha_delay)  # 새로운 컨트롤 추가
        self.hbox_control.addWidget(self.sb_captcha_delay)  # 새로운 컨트롤 추가
        self.hbox_control.addWidget(self.btn_clear_log)

        self.gb_control = QGroupBox('제어')
        self.gb_control.setLayout(self.hbox_control)

        self.vbox.addWidget(self.gb_control)

    def fetch_goods_detail(self):
        ticket_id = self.le_ticket_id.text().replace(' ', '')
        if ticket_id == '':
            QMessageBox.warning(self, '경고', '공연 ID를 입력해주세요.')
            return

        self.importGoodsDetail = ImportGoodsDetail(self, ticket_id)
        self.importGoodsDetail.loadFinished.connect(self.loadFinished)
        self.importGoodsDetail.start()

    @pyqtSlot(str)
    def printLog(self, text):
        currenttime_str = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        item = QListWidgetItem(f'[{currenttime_str}] {text}')
        self.lw_log.addItem(item)

        if self.lw_log.count() > 400:
            self.lw_log.takeItem(0)

        self.lw_log.scrollToBottom()


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

    def start(self):
        inter_ticket_id = self.le_ticket_id.text().replace(' ', '')
        if inter_ticket_id == '':
            self.printLog("상품코드 입력하고 조회부터 하세요")
            return

        for i in range(1):  # ✅ 각 검색어를 별도 프로세스로 실행
            process = QProcess(self)
            process.setProgram("python")  # 실행할 프로그램 (Python)
            process.setArguments(["ticketer.py", str(inter_ticket_id), f'id{i}.txt'])  # ✅ 인덱스 값과 검색어 전달
            process.setProcessChannelMode(QProcess.MergedChannels)  # ✅ 표준출력(stdout) + 표준에러(stderr) 합치기
            process.readyReadStandardOutput.connect(lambda p=process: self.printLog(p))
            process.readyReadStandardError.connect(lambda p=process: self.printLog(p))
            process.start()
            self.processes.append(process)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop(self):
        for process in self.processes:
            process.terminate()
            self.printLog(f"프로세스 {process.processId()} 종료됨.")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    sys.exit(app.exec_())
