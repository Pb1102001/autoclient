# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.core.window import Window
import os
import time
import datetime
import threading
import ntplib

# ===================== 中文字体 =====================
if platform == "win":
    LabelBase.register(name="Font", fn_regular="C:/Windows/Fonts/simsun.ttc")
elif platform == "android":
    try:
        import jnius
        LabelBase.register(name="Font", fn_regular="/system/fonts/DroidSansFallback.ttf")
    except:
        LabelBase.register(name="Font", fn_regular="DroidSansFallback.ttf")
else:
    LabelBase.register(name="Font", fn_regular="/System/Library/Fonts/PingFang.ttc")

# ===================== NTP 网络时间 =====================
ntp_client = ntplib.NTPClient()
NTP_SERVERS = ["ntp.ntsc.ac.cn", "cn.ntp.org.cn", "time1.aliyun.com"]

def get_ntp_beijing_time():
    for server in NTP_SERVERS:
        try:
            res = ntp_client.request(server, timeout=0.8)
            utc = datetime.datetime.utcfromtimestamp(res.tx_time)
            return utc + datetime.timedelta(hours=8)
        except:
            continue
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

def str_to_time(s):
    try:
        s = s.strip()
        if "." in s:
            return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
        else:
            return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except:
        return None

# ===================== 免ROOT 点击核心 =====================
def click_no_root(x, y):
    """免ROOT点击（安卓无障碍服务）"""
    if platform == "android":
        cmd = f"am broadcast -a com.autoclick.ACTION_CLICK --ei x {x} --ei y {y}"
        os.system(cmd)
    else:
        try:
            import pyautogui
            pyautogui.click(x, y)
        except:
            pass

# ===================== 全局配置 =====================
config = {
    "points": [],
    "interval": 0.1,
    "double_click": False,
    "continuous": True,
    "start_time": "",
    "end_time": "",
    "running": False,
}

# ===================== 主界面 =====================
class AutoClickPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 12
        self.spacing = 6
        self.font = "Font"

        self.add_widget(Label(text="【免ROOT·NTP精准版】点击器", font_name=self.font, font_size=20, size_hint=(1, 0.07)))

        # XY
        xy_layout = BoxLayout(size_hint=(1, 0.07))
        self.x_input = TextInput(hint_text="X", input_filter="int", font_name=self.font, font_size=16)
        self.y_input = TextInput(hint_text="Y", input_filter="int", font_name=self.font, font_size=16)
        xy_layout.add_widget(self.x_input)
        xy_layout.add_widget(self.y_input)
        self.add_widget(xy_layout)

        self.get_btn = Button(text="获取坐标", font_name=self.font, font_size=16, size_hint=(1, 0.07))
        self.get_btn.bind(on_press=self.get_pos)
        self.add_widget(self.get_btn)

        self.add_btn = Button(text="添加到序列", font_name=self.font, font_size=16, size_hint=(1, 0.07), background_color=(0.1,0.7,0.2,1))
        self.add_btn.bind(on_press=self.add_point)
        self.add_widget(self.add_btn)

        self.points_label = Label(text="序列：空", font_name=self.font, font_size=14, size_hint=(1, 0.12))
        self.add_widget(self.points_label)

        self.clear_btn = Button(text="清空序列", font_name=self.font, font_size=14, size_hint=(1, 0.06), background_color=(0.8,0.2,0.2,1))
        self.clear_btn.bind(on_press=self.clear_points)
        self.add_widget(self.clear_btn)

        # 间隔
        inter_layout = BoxLayout(size_hint=(1, 0.07))
        inter_layout.add_widget(Label(text="点击间隔(秒):", font_name=self.font, font_size=15))
        self.interval_input = TextInput(text="0.1", font_name=self.font, font_size=15)
        inter_layout.add_widget(self.interval_input)
        self.add_widget(inter_layout)

        # 时间
        self.add_widget(Label(text="开始时间 (2026-04-16 15:30:00.123)", font_name=self.font, font_size=13, size_hint=(1, 0.05)))
        self.start_time_input = TextInput(font_name=self.font, font_size=15, size_hint=(1, 0.07))
        self.add_widget(self.start_time_input)

        self.add_widget(Label(text="结束时间 (格式同上)", font_name=self.font, font_size=13, size_hint=(1, 0.05)))
        self.end_time_input = TextInput(font_name=self.font, font_size=15, size_hint=(1, 0.07))
        self.add_widget(self.end_time_input)

        # 选项
        opt1 = BoxLayout(size_hint=(1, 0.07))
        opt1.add_widget(Label(text="双击:", font_name=self.font, font_size=15))
        self.s_double = Switch(active=False)
        opt1.add_widget(self.s_double)

        opt2 = BoxLayout(size_hint=(1, 0.07))
        opt2.add_widget(Label(text="循环:", font_name=self.font, font_size=15))
        self.s_continuous = Switch(active=True)
        opt2.add_widget(self.s_continuous)

        self.add_widget(opt1)
        self.add_widget(opt2)

        # 权限提示
        self.tip = Label(text="请在无障碍权限中开启本APP", font_name=self.font, font_size=14, color=(1,0.3,0.3,1), size_hint=(1, 0.05))
        self.add_widget(self.tip)

        # 控制
        self.start_btn = Button(text="开始(免ROOT NTP)", font_name=self.font, font_size=18, size_hint=(1, 0.12), background_color=(0.2,0.8,0.2,1))
        self.start_btn.bind(on_press=self.start_thread)

        self.stop_btn = Button(text="停止", font_name=self.font, size_hint=(1, 0.12), font_size=18, background_color=(0.9,0.2,0.2,1))
        self.stop_btn.bind(on_press=self.stop_click)

        self.add_widget(self.start_btn)
        self.add_widget(self.stop_btn)

        self.status = Label(text="状态: 待机", font_name=self.font, font_size=15, size_hint=(1, 0.07))
        self.add_widget(self.status)

    def get_pos(self, instance):
        self.status.text = "点击屏幕获取坐标"
        Window.bind(on_touch_down=self._on_touch)

    def _on_touch(self, window, touch):
        x, y = int(touch.x), int(touch.y)
        self.x_input.text = str(x)
        self.y_input.text = str(y)
        self.status.text = f"坐标：{x},{y}"
        Window.unbind(on_touch_down=self._on_touch)
        return True

    def add_point(self, instance):
        try:
            x = int(self.x_input.text)
            y = int(self.y_input.text)
            config["points"].append((x, y))
            self.show_points()
        except:
            self.status.text = "XY输入错误"

    def clear_points(self, instance):
        config["points"].clear()
        self.points_label.text = "序列：空"

    def show_points(self):
        lines = [f"{i+1}. {x},{y}" for i,(x,y) in enumerate(config["points"])]
        self.points_label.text = "\n".join(lines)

    # ===================== 执行点击 =====================
    def do_click(self, x, y):
        click_no_root(x, y)
        if config["double_click"]:
            time.sleep(0.08)
            click_no_root(x, y)

    # ===================== 任务线程 =====================
    def task(self):
        config["running"] = True
        t_start = str_to_time(self.start_time_input.text.strip())
        t_end = str_to_time(self.end_time_input.text.strip())
        config["interval"] = float(self.interval_input.text)
        config["double_click"] = self.s_double.active
        config["continuous"] = self.s_continuous.active

        # 等待开始时间
        while config["running"]:
            now = get_ntp_beijing_time()
            self.set_status(f"等待 | {now.strftime('%H:%M:%S.%f')[:-3]}")
            if t_start is None or now >= t_start:
                break
            time.sleep(0.001)

        # 循环点击
        while config["running"]:
            now = get_ntp_beijing_time()
            if t_end and now >= t_end:
                self.set_status("结束时间到")
                break

            for x, y in config["points"]:
                if not config["running"]:
                    return
                now = get_ntp_beijing_time()
                if t_end and now >= t_end:
                    self.set_status("结束")
                    return
                self.do_click(x, y)
                self.set_status(f"点击 {x},{y} | {now.strftime('%H:%M:%S.%f')[:-3]}")
                time.sleep(config["interval"])

            if not config["continuous"]:
                break

        self.set_status("完成")
        config["running"] = False

    @mainthread
    def set_status(self, txt):
        self.status.text = txt

    def start_thread(self, instance):
        if not config["points"]:
            self.status.text = "请添加坐标"
            return
        threading.Thread(target=self.task, daemon=True).start()

    def stop_click(self, instance):
        config["running"] = False
        self.status.text = "已停止"

class AppMain(App):
    def build(self):
        return AutoClickPanel()

if __name__ == "__main__":
    AppMain().run()