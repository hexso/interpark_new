import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout

class TicketApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 인터파크 버튼
        self.interpark_btn = QPushButton("인터파크", self)
        self.interpark_btn.clicked.connect(lambda: self.run_script("interpark/interpark.py"))
        layout.addWidget(self.interpark_btn)

        # 멜론 버튼
        self.melon_btn = QPushButton("멜론", self)
        self.melon_btn.clicked.connect(lambda: self.run_script("melon/melon.py"))
        layout.addWidget(self.melon_btn)

        # 티켓링크 버튼
        self.ticketlink_btn = QPushButton("티켓링크", self)
        self.ticketlink_btn.clicked.connect(lambda: self.run_script("ticketlink/ticketlink.py"))
        layout.addWidget(self.ticketlink_btn)

        self.setLayout(layout)
        self.setWindowTitle("티켓 예매")
        self.resize(300, 150)

    def run_script(self, script_path):
        """ 버튼 클릭 시 해당 main.py 실행 후 현재 창 종료 """
        try:
            subprocess.Popen(["python", script_path])  # 외부 스크립트 실행
            self.close()  # 현재 창 닫기
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TicketApp()
    ex.show()
    sys.exit(app.exec_())
