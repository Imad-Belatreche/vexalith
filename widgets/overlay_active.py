from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Center, Middle
from textual.widgets import Label


class OverlayActiveScreen(Screen):
    CSS = """
    OverlayActiveScreen {
        align: center middle;
        background: $background;
    }
    
    OverlayActiveScreen Label {
        text-align: center;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(
            "Overlay is currently active.\nClose the overlay window to restore Vexalith."
        )
