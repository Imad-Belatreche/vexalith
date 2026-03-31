from textual.containers import Container
from textual.widgets import Label, ProgressBar


class DownloadNotification(Container):
    CSS_PATH = "download_manager.tcss"

    def __init__(
        self,
        id: str,
        label: str = "",
    ):
        self.label = label

        super().__init__(id=id)

    def compose(self):

        yield Label(self.label)
        yield ProgressBar(show_percentage=True, show_eta=True, show_bar=True)

    def set_label(self, text: str):
        self.query_one(Label).update(text)

    def reset_progress(self, total: float | None = None):
        self.query_one(ProgressBar).update(total=total, progress=0)

    def update_progress(self, progress: float, total: float | None = None):
        if total is not None:
            self.query_one(ProgressBar).total = total
        self.query_one(ProgressBar).advance(advance=progress)
