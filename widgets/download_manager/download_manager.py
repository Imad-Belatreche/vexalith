import os

import requests
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Tree, Select
from utils import get_model_select_options, get_piper_models_tree, get_voices
from widgets.download_manager.download_notification import DownloadNotification


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

    voices: dict = {}

    def compose(self) -> ComposeResult:
        yield Label("Download Manager", id="download-title")
        yield Tree(id="models-tree", label="Loading...")
        yield DownloadNotification(id="download-notif")
        yield Footer()

    def on_mount(self) -> None:
        self.fetch_models()

    @work(thread=True)
    def fetch_models(self) -> None:
        voices = get_piper_models_tree()

        self.app.call_from_thread(self.populate_tree, voices)

    def populate_tree(self, voices: dict) -> None:
        # Grab the tree we yielded in compose()
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
        notif = self.query_one(DownloadNotification)
        notif.styles.display = "block"
        notif.reset_progress()
        self.app.push_screen(ConfirmChoice(full_path), self.start_download)

    @work(thread=True)
    def start_download(self, file_name: str | None) -> None:
        if file_name is None:
            return

        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        notif = self.query_one(DownloadNotification)

        import os

        os.makedirs("v_models", exist_ok=True)

        files_to_download = [file_name, f"{file_name}.json"]

        for file_ref in files_to_download:
            ref_path_split = file_ref.split("/")
            file_path = f"v_models/{ref_path_split[-1]}"

            self.app.call_from_thread(
                notif.set_label, f"Downloading {ref_path_split[-1]}..."
            )

            response = requests.get(f"{base_url}{file_ref}", stream=True)
            response.raise_for_status()

            total_size_str = response.headers.get("content-length")
            total_size = float(total_size_str) if total_size_str else None

            self.app.call_from_thread(notif.reset_progress, total=total_size)

            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        self.app.call_from_thread(
                            notif.update_progress, float(len(chunk)), total_size
                        )

        self.app.call_from_thread(self.download_finished)

    def download_finished(self):
        select = self.app.query_one("#model_select", Select)
        # TODO: REMOVE DULICATION
        select.set_options(options=get_model_select_options(get_voices()))
        print(f"Set this voice when finish: {get_voices()[0]}")
        select.value = get_voices()[0]
        self.query_one(DownloadNotification).styles.display = "none"
