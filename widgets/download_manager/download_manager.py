from typing import Callable
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Tree
from utils import get_piper_models_tree


class ConfirmChoice(ModalScreen):

    def __init__(self, file_name: str):
        self.file_name = file_name
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure about downloading this voice?", id="question"),
            Button("No", variant="error", id="cancel"),
            Button("Yes", variant="primary", id="confirm"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(self.file_name)
        else:
            self.dismiss(None)


class DownloadManager(ModalScreen):

    CSS_PATH = "download_manager.tcss"
    BINDINGS = [("escape", "exit_manager", "Exit")]

    def __init__(self, on_download_request: Callable[[str]]):
        self.on_download_request = on_download_request
        super().__init__()

    voices: dict = {}

    def compose(self) -> ComposeResult:
        yield Label("Download Manager", id="download-title")
        yield Tree(id="models-tree", label="Loading...")
        yield Footer()

    def on_mount(self) -> None:
        self.fetch_models()

    @work(thread=True)
    def fetch_models(self) -> None:
        voices = get_piper_models_tree()

        self.app.call_from_thread(self.populate_tree, voices)

    def populate_tree(self, voices: dict) -> None:
        tree = self.query_one("#models-tree", Tree)
        tree.root.label = "Languages"
        tree.root.expand()

        def build_tree(node, current_dict, current_path=""):
            for key, value in current_dict.items():
                path = f"{current_path}/{key}" if current_path else key

                if isinstance(value, dict):
                    child_node = node.add(key)
                    build_tree(child_node, value, path)
                else:
                    node.add_leaf(key, data=path)

        build_tree(tree.root, voices)

    def action_exit_manager(self):
        self.app.pop_screen()

    @on(Tree.NodeSelected)
    def on_node_selected(self, event: Tree.NodeSelected):
        if not str(event.node.label).endswith(".onnx"):
            return

        full_path = event.node.data

        self.app.push_screen(ConfirmChoice(full_path), self.start_download)

    def start_download(self, file_name: str):
        self.notify(f"Start downloading {file_name}....")
        self.on_download_request(file_name)
