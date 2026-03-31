from copy import deepcopy
from queue import Queue
import subprocess
from threading import Lock, Thread

from piper import PiperVoice, SynthesisConfig
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Center, HorizontalGroup, VerticalGroup, Container
from textual.reactive import Reactive
from textual.widgets import (
    Footer,
    Header,
    RichLog,
    Label,
    ListView,
    ListItem,
    Select,
)
from constants import CONFIG_FILE
from utils import (
    check_and_create_config,
    get_voices,
    load_config,
    play_text,
    save_config,
)
from widgets.download_manager.download_manager import DownloadManager
from widgets.label_item import LabelItem
from widgets.preset_input import PresetInput

history = []
configs: dict = {}

check_and_create_config(CONFIG_FILE)
configs.update(load_config(CONFIG_FILE))

speed = configs.get("settings").get("speed", 1.0)
model = configs.get("settings").get("model", "en_US-danny-low.onnx")
debounce_time = configs.get("settings").get("debounce_time", 0.8)

settings_queue = Queue()
audio_queue = Queue()
state_lock = Lock()

speed_list = [1.0, 1.3, 1.5, 0.7, 0.5]
timer_list = [0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2]
speed_list.sort()


def make_syn_settings(speed_val: float) -> SynthesisConfig:
    return SynthesisConfig(
        noise_scale=0.3,
        length_scale=speed_val,
        noise_w_scale=0.55,
        normalize_audio=True,
    )


voice = PiperVoice.load(model_path=model)
syn_settings = make_syn_settings(speed)


def tts_worker():
    while True:
        try:
            text = audio_queue.get()
            if text is None:
                break
            with state_lock:
                current_voice = voice
                current_settings = syn_settings

            play_text(text, voice=current_voice, syn_config=current_settings)
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"[Audio Error]: {e}")


def settings_worker():
    global voice, syn_settings

    while True:
        item = settings_queue.get()
        if item is None:
            break
        try:
            kind = item["kind"]
            value = item["value"]
            config_snapshot = item["config"]

            if kind == "speed":
                with state_lock:
                    syn_settings = make_syn_settings(float(value))

            elif kind == "model":
                new_voice = PiperVoice.load(
                    model_path=f"{value}",
                    config_path=f"{value}.json",
                )
                with state_lock:
                    voice = new_voice

            save_config(CONFIG_FILE, config_snapshot)

        finally:
            settings_queue.task_done()


def add_settings_to_queue(kind: str, value):
    settings_queue.put(
        {
            "kind": kind,
            "value": value,
            "config": deepcopy(configs),
        }
    )


class VexalithApp(App):
    CSS_PATH = "vexalith.tcss"
    COMMAND_PALETTE_BINDING = "ctrl+k"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+p", "toggle_presets", "Toggle presets"),
        ("ctrl+s", "toggle_settings", "Toggle settings"),
    ]

    show_presets = Reactive(False)
    show_settings = Reactive(False)

    def compose(self) -> ComposeResult:

        yield Header(show_clock=True, icon="🗣️")

        self.presets = VerticalGroup(
            Center(
                Label("Presets", classes="side-titles"),
            ),
            ListView(
                id="presets-list",
            ),
            id="presets",
        )

        self.settings = VerticalGroup(
            Center(
                Label("Settings", classes="side-titles"),
            ),
            Container(
                Label("Model:", classes="setting-item"),
                Select(
                    options=[
                        *[
                            (voice.replace("v_models/", "").replace(".onnx", ""), voice)
                            for voice in get_voices()
                        ],
                        ("Download models", "get_models"),
                    ],
                    prompt="Select an option",
                    value=model,
                    allow_blank=False,
                    id="model_select",
                ),
                Label("Speed:", classes="setting-item"),
                Select(
                    options=[(str(speed), speed) for speed in speed_list],
                    prompt="Select an option",
                    value=speed,
                    allow_blank=False,
                    id="speed_select",
                ),
                Label("Debounce timer:", classes="setting-item"),
                Select(
                    options=[(str(timer), timer) for timer in timer_list],
                    prompt="Select a timer",
                    value=debounce_time,
                    allow_blank=False,
                    id="timer_select",
                ),
                id="settings-container",
            ),
            id="settings",
        )

        yield HorizontalGroup(
            self.presets,
            VerticalGroup(
                Center(Label("=={{   History log   }}==")),
                RichLog(
                    id="log",
                    auto_scroll=True,
                    highlight=False,
                    wrap=True,
                ),
                classes="main-area",
            ),
            self.settings,
        )

        yield PresetInput(
            placeholder="Type something here...",
            type="text",
            id="input",
            audio_queue=audio_queue,
            configs=configs,
            history=history,
        )

        yield Footer(show_command_palette=False)

    def on_mount(self):
        global configs, speed, model, debounce_time

        self.title = "Vexalith"
        self.sub_title = "Speak your mind"

        self.query_one("#presets-list", ListView).mount(
            *[ListItem(LabelItem(preset)) for preset in configs.get("presets", [])]
        )
        self.query_one("#input").focus()

    def action_toggle_dark(self):
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def watch_show_presets(self, show: bool) -> None:
        self.presets.styles.width = 30 if show else 0

    def action_toggle_presets(self):
        self.show_presets = not self.show_presets

    def watch_show_settings(self, show: bool) -> None:
        self.settings.styles.width = 30 if show else 0

    def action_toggle_settings(self):
        self.show_settings = not self.show_settings

    @on(ListView.Selected)
    def on_list_view_selected(self, event: ListView.Selected):
        input_field = self.query_one("#input", PresetInput)
        label = event.item.query_one(LabelItem)
        input_field.value = label.label
        input_field.select_on_focus = False
        input_field.focus()
        input_field.cursor_position = len(input_field.value)

    @on(Select.Changed)
    def on_select_changed(self, event: Select.Changed):
        global model, speed

        if event.select.id == "model_select":
            if event.value == "get_models":
                event.value = event.select.value
                self.push_screen(DownloadManager())
            else:
                model = event.value
                configs["settings"]["model"] = model
                add_settings_to_queue("model", model)

                self.query_one(PresetInput).last_spoken = ""

        elif event.select.id == "speed_select":
            speed = event.value
            configs["settings"]["speed"] = speed
            add_settings_to_queue("speed", speed)

        elif event.select.id == "timer_select":
            debounce_time = event.value
            configs["settings"]["debounce_time"] = debounce_time
            add_settings_to_queue("debounce_time", debounce_time)

        self.query_one(PresetInput).focus()


if __name__ == "__main__":
    audio_thread = Thread(target=tts_worker)
    settings_thread = Thread(target=settings_worker)

    audio_thread.start()
    settings_thread.start()

    app = VexalithApp()
    app.run()

    audio_queue.put(None)
    settings_queue.put(None)

    audio_thread.join()
    settings_thread.join()
