from textual import on
from textual.containers import Container, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class StartScreen(ModalScreen):
    def __init__(self):
        id = "start_screen"
        super().__init__(id=id)

    CSS = """
    StartScreen {
        align: center middle;
    }
    
    Container {
        height: 1;
        width: 60;
    }
    
    #welcome-title {
            text-align: center;
            width: 100%;
    }
    
    #welecom-diag {
        align: center middle;

        grid-size: 1 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }
    """

    def compose(self):

        yield Container(Label("Welcome to Vexalith", id="welcome-title"))
        yield Grid(
            Label(
                "It seems you have no voice model available\nThen let's download one !"
            ),
            Label("Select a model from the tree after closing this window"),
            Button(
                label="Ok",
                variant="success",
            ),
            id="welecom-diag",
        )

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed):
        self.app.pop_screen()
