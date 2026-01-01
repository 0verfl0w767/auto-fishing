import time
import numpy as np
import cv2
import pyautogui
import mss
import win32gui, win32con, win32api

class Overlay:
    def __init__(self, left, top, width, height):
        self.hInstance = win32api.GetModuleHandle(None)
        self.className = "OverlayWindow"

        wndClass = win32gui.WNDCLASS()
        wndClass.lpfnWndProc = self.wndProc
        wndClass.hInstance = self.hInstance
        wndClass.lpszClassName = self.className
        win32gui.RegisterClass(wndClass)

        exStyle = win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW

        self.hwnd = win32gui.CreateWindowEx(
            exStyle,
            self.className,
            None,
            win32con.WS_POPUP,
            left, top, width, height,
            None, None, self.hInstance, None
        )

        win32gui.SetLayeredWindowAttributes(self.hwnd, 0x000000, 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, left, top, width, height, 0)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        win32gui.UpdateWindow(self.hwnd)

    def wndProc(self, hwnd, msg, wParam, lParam):
        if msg == win32con.WM_PAINT:
            hdc, ps = win32gui.BeginPaint(hwnd)
            pen = win32gui.CreatePen(win32con.PS_SOLID, 3, 0x0000FF)
            win32gui.SelectObject(hdc, pen)
            win32gui.SelectObject(hdc, win32gui.GetStockObject(win32con.NULL_BRUSH))
            rect = win32gui.GetClientRect(hwnd)
            win32gui.Rectangle(hdc, *rect)
            win32gui.EndPaint(hwnd, ps)
            return 0
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

screen_width = 1920
screen_height = 1080

overlay_width = 300
overlay_height = 300

left = (screen_width - overlay_width) // 2
top = (screen_height - overlay_height) // 2

overlay = Overlay(left, top, overlay_width, overlay_height)
monitor = {
    "left": left,
    "top": top,
    "width": overlay_width,
    "height": overlay_height
}

THRESHOLD = 15
PIXEL_CHANGE_LIMIT = 4000
CAST_IGNORE_DURATION = 2.5  # 던진 직후 무적
MAX_HISTORY = 3  # 최근 프레임 변화 합산

sct = mss.mss()
prev_frame = None
frame_history = []

pyautogui.rightClick()
last_cast_time = time.time()

print("자동 낚시 시작")

try:
    while True:
        # 화면 캡처
        img = np.array(sct.grab(monitor))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_frame is None:
            prev_frame = gray
            continue

        # 프레임 차이
        frame_diff = cv2.absdiff(prev_frame, gray)
        _, thresh = cv2.threshold(frame_diff, THRESHOLD, 255, cv2.THRESH_BINARY)
        changed_pixels = cv2.countNonZero(thresh)

        # 최근 프레임 변화 합산
        frame_history.append(changed_pixels)
        if len(frame_history) > MAX_HISTORY:
            frame_history.pop(0)
        total_change = sum(frame_history)

        if total_change > PIXEL_CHANGE_LIMIT:
            if time.time() - last_cast_time > CAST_IGNORE_DURATION:
                current_time = time.strftime("%H:%M:%S", time.localtime())
                print(f"[{current_time}] 입질 감지!")
                pyautogui.rightClick()
                time.sleep(0.3)
                pyautogui.rightClick()
                last_cast_time = time.time()

        prev_frame = gray
        time.sleep(0.05)

except KeyboardInterrupt:
    print("종료")
    win32gui.DestroyWindow(overlay.hwnd)
