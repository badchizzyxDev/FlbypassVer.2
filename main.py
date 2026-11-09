from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation
import threading, subprocess, os, time

Window.clearcolor = get_color_from_hex('#0a0a0f')

# ── colours ──────────────────────────────────────────────
C_BG      = '#0a0a0f'
C_CARD    = '#13131f'
C_GREEN   = '#00ff88'
C_BLUE    = '#00aaff'
C_PURPLE  = '#aa44ff'
C_RED     = '#ff4466'
C_YELLOW  = '#ffcc00'
C_TEXT    = '#e0e0e0'
C_SUB     = '#666677'
C_BTN     = '#1a1a2e'

# ── bypass methods ────────────────────────────────────────
METHODS = [
    {
        "id": "datetime",
        "icon": "📅",
        "title": "Date/Time Warp",
        "desc": "เลื่อนวันไปข้างหน้า → FL token หมดอายุ",
        "color": C_YELLOW,
        "auto": True,
        "steps": [
            "กำลังปิด Automatic date/time...",
            "เลื่อนวันไปข้างหน้า 3 ปี...",
            "รอ FL session หมดอายุ...",
            "Bypass สำเร็จ ✅",
        ],
        "cmds": [
            "settings put global auto_time 0",
            "date -s '20280101.120000'",
            None,
            None,
        ]
    },
    {
        "id": "airplane",
        "icon": "✈️",
        "title": "Airplane Mode Install",
        "desc": "ตัด network ขณะติดตั้ง → FL approval ไม่ถึง",
        "color": C_BLUE,
        "auto": True,
        "steps": [
            "เปิด Airplane Mode...",
            "รอ FL connection timeout...",
            "ปิด Airplane Mode...",
            "พร้อมติดตั้งแอปแล้ว ✅",
        ],
        "cmds": [
            "settings put global airplane_mode_on 1",
            None,
            "settings put global airplane_mode_on 0",
            None,
        ]
    },
    {
        "id": "account",
        "icon": "👤",
        "title": "Secondary Account",
        "desc": "เปิดหน้า Add Account → เพิ่ม account ที่ไม่ถูก supervise",
        "color": C_PURPLE,
        "auto": True,
        "steps": [
            "เปิด Account Settings...",
            "นำทางไปหน้า Add Account...",
            "รอการยืนยัน...",
            "เปิดหน้าแล้ว — เพิ่ม account ได้เลย ✅",
        ],
        "cmds": [
            "am start -a android.settings.ADD_ACCOUNT_SETTINGS",
            None,
            None,
            None,
        ]
    },
    {
        "id": "devmode",
        "icon": "⚙️",
        "title": "Developer Mode",
        "desc": "เปิด Developer Options → unlock install unknown apps",
        "color": C_GREEN,
        "auto": True,
        "steps": [
            "เปิด Developer Options...",
            "เปิด USB Debugging...",
            "เปิด Install Unknown Apps...",
            "Developer Mode เปิดแล้ว ✅",
        ],
        "cmds": [
            "settings put global development_settings_enabled 1",
            "settings put global adb_enabled 1",
            "settings put secure install_non_market_apps 1",
            None,
        ]
    },
]

# ── rounded card canvas helper ────────────────────────────
def add_bg(widget, color_hex, radius=18):
    with widget.canvas.before:
        Color(*get_color_from_hex(color_hex))
        widget._bg_rect = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda w,v: setattr(w._bg_rect,'pos',v),
                size=lambda w,v: setattr(w._bg_rect,'size',v))

# ══════════════════════════════════════════════════════════
# HOME SCREEN
# ══════════════════════════════════════════════════════════
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', spacing=0)

        # header
        hdr = BoxLayout(orientation='vertical', size_hint_y=None,
                        height=140, padding=[24,24,24,8])
        add_bg(hdr, '#0d0d1a')

        title = Label(
            text='🔓 FL Bypass',
            font_size='28sp', bold=True,
            color=get_color_from_hex(C_GREEN),
            size_hint_y=None, height=50,
            halign='left', valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        hdr.add_widget(title)

        sub = Label(
            text='เลือก method — กดแล้วรันอัตโนมัติ',
            font_size='13sp',
            color=get_color_from_hex(C_SUB),
            size_hint_y=None, height=28,
            halign='left', valign='middle'
        )
        sub.bind(size=sub.setter('text_size'))
        hdr.add_widget(sub)

        status_row = BoxLayout(size_hint_y=None, height=34, spacing=8)
        dot = Label(text='● ADB Connected', font_size='12sp',
                    color=get_color_from_hex(C_GREEN),
                    size_hint_x=None, width=140)
        status_row.add_widget(dot)
        status_row.add_widget(Label())
        hdr.add_widget(status_row)
        root.add_widget(hdr)

        # scroll cards
        scroll = ScrollView(size_hint_y=1)
        grid = GridLayout(cols=1, spacing=12, size_hint_y=None,
                         padding=[16,16,16,32])
        grid.bind(minimum_height=grid.setter('height'))

        for m in METHODS:
            grid.add_widget(self._make_card(m))

        scroll.add_widget(grid)
        root.add_widget(scroll)
        self.add_widget(root)

    def _make_card(self, m):
        card = BoxLayout(orientation='vertical', spacing=10,
                        size_hint_y=None, height=140,
                        padding=[20,16,20,16])
        add_bg(card, C_CARD, radius=18)

        # top row
        top = BoxLayout(size_hint_y=None, height=48, spacing=12)

        icon_box = BoxLayout(size_hint_x=None, width=48,
                            size_hint_y=None, height=48)
        add_bg(icon_box, C_BTN, radius=12)
        icon = Label(text=m['icon'], font_size='22sp',
                    size_hint_y=None, height=48)
        icon_box.add_widget(icon)
        top.add_widget(icon_box)

        txt_col = BoxLayout(orientation='vertical', spacing=2)
        title_l = Label(
            text=m['title'], font_size='16sp', bold=True,
            color=get_color_from_hex(m['color']),
            halign='left', valign='middle',
            size_hint_y=None, height=26
        )
        title_l.bind(size=title_l.setter('text_size'))
        desc_l = Label(
            text=m['desc'], font_size='12sp',
            color=get_color_from_hex(C_SUB),
            halign='left', valign='middle',
            size_hint_y=None, height=20
        )
        desc_l.bind(size=desc_l.setter('text_size'))
        txt_col.add_widget(title_l)
        txt_col.add_widget(desc_l)
        top.add_widget(txt_col)
        card.add_widget(top)

        # run button
        btn = Button(
            text=f'⚡ Run {m["title"]}',
            font_size='14sp', bold=True,
            background_color=get_color_from_hex(C_BTN),
            color=get_color_from_hex(m['color']),
            size_hint_y=None, height=44,
            border=(18,18,18,18)
        )
        btn.bind(on_press=lambda x, method=m: self.run_method(method))
        card.add_widget(btn)

        return card

    def run_method(self, method):
        app = App.get_running_app()
        screen = app.root.get_screen('progress')
        screen.start(method)
        app.root.current = 'progress'


# ══════════════════════════════════════════════════════════
# PROGRESS SCREEN
# ══════════════════════════════════════════════════════════
class ProgressScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.method = None
        self._thread = None

        root = BoxLayout(orientation='vertical', padding=[24,40,24,24],
                        spacing=20)

        # title
        self.title_lbl = Label(
            text='', font_size='22sp', bold=True,
            color=get_color_from_hex(C_GREEN),
            size_hint_y=None, height=50,
            halign='center'
        )
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        root.add_widget(self.title_lbl)

        # big icon
        self.icon_lbl = Label(
            text='', font_size='52sp',
            size_hint_y=None, height=80
        )
        root.add_widget(self.icon_lbl)

        # progress bar
        pb_box = BoxLayout(size_hint_y=None, height=18, padding=[0,4])
        self.pb = ProgressBar(max=100, value=0)
        pb_box.add_widget(self.pb)
        root.add_widget(pb_box)

        self.pct_lbl = Label(
            text='0%', font_size='13sp',
            color=get_color_from_hex(C_SUB),
            size_hint_y=None, height=24, halign='center'
        )
        root.add_widget(self.pct_lbl)

        # log scroll
        log_scroll = ScrollView(size_hint_y=1)
        log_card = BoxLayout(orientation='vertical', size_hint_y=None,
                            padding=16, spacing=6)
        log_card.bind(minimum_height=log_card.setter('height'))
        add_bg(log_card, C_CARD, radius=14)

        self.log_grid = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.log_grid.bind(minimum_height=self.log_grid.setter('height'))
        log_card.add_widget(self.log_grid)
        log_scroll.add_widget(log_card)
        root.add_widget(log_scroll)

        # status label
        self.status_lbl = Label(
            text='', font_size='14sp',
            color=get_color_from_hex(C_TEXT),
            size_hint_y=None, height=32,
            halign='center'
        )
        root.add_widget(self.status_lbl)

        # back button
        self.back_btn = Button(
            text='← กลับหน้าหลัก',
            font_size='14sp',
            background_color=get_color_from_hex(C_BTN),
            color=get_color_from_hex(C_TEXT),
            size_hint_y=None, height=48,
            opacity=0, disabled=True
        )
        self.back_btn.bind(on_press=self.go_home)
        root.add_widget(self.back_btn)

        self.add_widget(root)

    def start(self, method):
        self.method = method
        self.pb.value = 0
        self.pct_lbl.text = '0%'
        self.log_grid.clear_widgets()
        self.status_lbl.text = 'กำลังรัน...'
        self.status_lbl.color = get_color_from_hex(C_TEXT)
        self.title_lbl.text = f'{method["icon"]} {method["title"]}'
        self.icon_lbl.text = method["icon"]
        self.back_btn.opacity = 0
        self.back_btn.disabled = True

        self._thread = threading.Thread(target=self._run_steps, daemon=True)
        self._thread.start()

    def _run_steps(self):
        steps = self.method['steps']
        cmds  = self.method['cmds']
        total = len(steps)

        for i, (step, cmd) in enumerate(zip(steps, cmds)):
            Clock.schedule_once(lambda dt, s=step, idx=i, t=total:
                self._update_step(s, idx, t), 0)
            time.sleep(1.2)

            if cmd:
                try:
                    subprocess.run(
                        ['su', '-c', cmd],
                        capture_output=True, timeout=5
                    )
                except Exception:
                    pass

            pct = int((i + 1) / total * 100)
            Clock.schedule_once(lambda dt, p=pct: self._set_pb(p), 0)
            time.sleep(0.4)

        Clock.schedule_once(lambda dt: self._done(), 0)

    def _update_step(self, step, idx, total):
        colors = [C_YELLOW, C_BLUE, C_PURPLE, C_GREEN]
        color  = colors[idx % len(colors)]
        row = BoxLayout(size_hint_y=None, height=28, spacing=8)
        num = Label(
            text=f'[{idx+1}/{total}]',
            font_size='11sp',
            color=get_color_from_hex(color),
            size_hint_x=None, width=52
        )
        txt = Label(
            text=step, font_size='12sp',
            color=get_color_from_hex(C_TEXT),
            halign='left', valign='middle'
        )
        txt.bind(size=txt.setter('text_size'))
        row.add_widget(num)
        row.add_widget(txt)
        self.log_grid.add_widget(row)
        self.status_lbl.text = step

    def _set_pb(self, val):
        self.pb.value = val
        self.pct_lbl.text = f'{val}%'

    def _done(self):
        self.status_lbl.text = '✅ เสร็จแล้ว!'
        self.status_lbl.color = get_color_from_hex(C_GREEN)
        anim = Animation(opacity=1, duration=0.4)
        self.back_btn.disabled = False
        anim.start(self.back_btn)

    def go_home(self, *a):
        App.get_running_app().root.current = 'home'


# ══════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════
class FLBypassApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ProgressScreen(name='progress'))
        return sm


if __name__ == '__main__':
    FLBypassApp().run()
