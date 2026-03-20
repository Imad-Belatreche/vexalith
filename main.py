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
                ListItem(Label("Preset 1")),
                ListItem(Label("Preset 2")),
                ListItem(Label("Preset 3")),
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

        yield Input(placeholder="Type something here...", type="text", id="input")

        yield Footer(show_command_palette=False)

    def on_mount(self):
        self.title = "Vexalith"
        self.sub_title = "Speak your mind"
        text = self.query_one(RichLog)
        text.write("Your History log is here")

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
