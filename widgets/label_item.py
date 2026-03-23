from textual.widgets import Label


class LabelItem(Label):
    def __init__(self, label: str):
        super().__init__()
        self.label = label

    def compose(self):
        yield Label(self.label)
