import os

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Center, HorizontalGroup, VerticalGroup, Container
from textual.reactive import Reactive
from textual.widgets import (
    Footer,
    Header,
    RichLog,
    Input,
    Label,
    ListView,
    ListItem,
    Select,
)
from utils import check_and_create_config, load_config, save_config

history = []
configs: dict = {}
CONFIG_FILE = "config.json"


class PresetInput(Input):
    index = len(history)
    old_val = ""
    used_history = False
    BINDINGS = [
        ("ctrl+o", "save_preset", "Save preset"),
        ("up", "history_up", "History up"),
        ("down", "history_down", "History down"),
    ]

    def action_history_up(self):
        if self.index > 0:
            self.index = self.index - 1
            self.value = history[self.index]
            self.used_history = True

    def action_history_down(self):
        if self.index < len(history) - 1:
            self.index = self.index + 1
            self.value = history[self.index]
            self.used_history = True

        elif self.index == len(history) - 1:
            self.index = self.index + 1
            self.value = self.old_val
            self.used_history = False

    def action_save_preset(self):
        preset_text = self.value
        if preset_text not in configs.get("presets"):
            configs["presets"].append(preset_text)
            save_config(CONFIG_FILE, configs)

            self.app.query_one("#presets-list", ListView).mount(
                ListItem(Label(preset_text))
            )

    @on(Input.Changed)
    def save_old_value(self, event: Input.Changed):
        if not self.used_history:
            self.old_val = event.input.value
        print(self.old_val)

    @on(Input.Submitted)
    def handle_input_submition(self, event: Input.Submitted):
        input_text = event.input.value
        logs = self.app.query_one(RichLog)
        logs.write(input_text)
        event.input.value = ""
        history.append(input_text)
        self.index = len(history)
        self.used_history = False


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
            RichLog(
                id="log",
                auto_scroll=True,
                highlight=False,
            ),
            self.settings,
        )

        yield PresetInput(placeholder="Type something here...", type="text", id="input")

        yield Footer(show_command_palette=False)

    def on_mount(self):
        global configs

        self.title = "Vexalith"
        self.sub_title = "Speak your mind"
        text = self.query_one(RichLog)
        text.write("Your History log is here")

        check_and_create_config(CONFIG_FILE)
        configs = load_config(CONFIG_FILE)

        self.query_one("#presets-list", ListView).mount(
            *[ListItem(Label(preset)) for preset in configs.get("presets")]
        )

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


if __name__ == "__main__":
    app = VexalithApp()
    app.run()
