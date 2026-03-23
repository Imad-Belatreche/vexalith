from queue import Queue
from threading import Thread

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
from utils import check_and_create_config, load_config, play_text
from widgets.label_item import LabelItem
from widgets.preset_input import PresetInput

history = []
configs: dict = {}

syn_settings = SynthesisConfig(
    noise_scale=0.3, length_scale=1.0, noise_w_scale=0.55, normalize_audio=True
)
voice = PiperVoice.load(
    model_path="en_US-danny-low.onnx", config_path="en_US-danny-low.onnx.json"
)

audio_queue = Queue()


def tts_worker():
    while True:
        text = audio_queue.get()
        if text is None:
            break

        play_text(text, voice=voice, syn_config=syn_settings)


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
                        ("Model 1", "Model 1"),
                        ("Model 2", "Model 2"),
                        ("Model 3", "Model 3"),
                    ],
                    prompt="Select an option",
                ),
                Label("Speed:", classes="setting-item"),
                Select(
                    options=[
                        ("Speed 1", "Speed 1"),
                        ("Speed 2", "Speed 2"),
                        ("Speed 3", "Speed 3"),
                    ],
                    prompt="Select an option",
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
        global configs

        self.title = "Vexalith"
        self.sub_title = "Speak your mind"

        check_and_create_config(CONFIG_FILE)
        configs.update(load_config(CONFIG_FILE))

        self.query_one("#presets-list", ListView).mount(
            *[ListItem(LabelItem(preset)) for preset in configs.get("presets")]
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


if __name__ == "__main__":
    thread = Thread(target=tts_worker)
    thread.start()
    app = VexalithApp()
    app.run()

    audio_queue.put(None)
    thread.join()
