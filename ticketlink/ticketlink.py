import pyautogui
import cv2
import numpy as np
import time

# 🔹 타겟 색상 설정 (BGR 기준) 예: 빨간색 좌석
target_colors = {
    "red": ([0, 0, 200], [50, 50, 255]),
    "blue": ([200, 0, 0], [255, 50, 50]),
    "green": ([0, 200, 0], [50, 255, 50]),
    # 회색 좌석은 제외할 수 있도록 나중에 비교
    "gray": ([100, 100, 100], [160, 160, 160])
}

if __name__ == "__main__":

    # 색 기준: BGR로 변환
    target_bgr = np.array([69, 203, 152], dtype="uint8")

    # 범위 설정 (유사한 색까지 포함하고 싶을 때)
    lower = np.array([60, 190, 140], dtype="uint8")
    upper = np.array([80, 220, 170], dtype="uint8")

    # 스크린샷
    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # 색 범위에 해당하는 마스크 생성
    mask = cv2.inRange(frame, lower, upper)
    coords = cv2.findNonZero(mask)

    if coords is not None:
        # ▶ 여러 초록색 좌표 중에서 원하는 걸 선택

        # 🔸 1. 가장 왼쪽 위 좌석 선택 (y 우선 정렬, 그 다음 x)
        sorted_coords = sorted(coords, key=lambda pt: (pt[0][0], -pt[0][1]))  # 위 → 아래, 왼쪽 → 오른쪽
        x, y = sorted_coords[0][0]

        # 🔸 2. 또는 가장 오른쪽 아래 좌석
        # sorted_coords = sorted(coords, key=lambda pt: (-pt[0][1], -pt[0][0]))
        # x, y = sorted_coords[0][0]

        # 🔸 3. 또는 특정 영역 안에 있는 것만 필터링
        # filtered = [pt for pt in coords if 1000 < pt[0][0] < 1500 and 500 < pt[0][1] < 900]
        # if filtered:
        #     x, y = filtered[0][0]

        print(f"선택된 좌표: ({x}, {y})")
        pyautogui.moveTo(x, y)
        pyautogui.click()
    else:
        print("초록색 좌석을 찾지 못했습니다.")