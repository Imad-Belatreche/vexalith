from queue import Queue
from textual import on
from textual.widgets import Input, ListItem, ListView, RichLog
from constants import CONFIG_FILE, SpeakModes
from utils import save_config
from widgets.label_item import LabelItem


class PresetInput(Input):
    def __init__(
        self,
        history: list,
        configs: dict,
        audio_queue: Queue,
        placeholder: str,
        type: str,
        id: str,
    ):
        self.audio_queue = audio_queue
        self.history = history
        self.configs = configs
        super().__init__(id=id, type=type, placeholder=placeholder)

    index = 0
    old_val = ""
    used_history = False

    last_spoken = ""
    debounce_timer = None
    mode = SpeakModes.SUBMIT

    BINDINGS = [
        ("ctrl+t", "change_mode", "Change mode"),
        ("ctrl+o", "save_preset", "Save preset"),
        ("up", "history_up", "History up"),
        ("down", "history_down", "History down"),
    ]

    def speak_only_unspoken(self, current_text: str):
        if self.last_spoken.startswith(current_text):
            pass
        elif current_text.startswith(self.last_spoken):
            new_text = current_text[len(self.last_spoken) :].strip()
            if new_text:
                self.audio_queue.put(new_text)
        else:
            if current_text.strip():
                self.audio_queue.put(current_text)

        self.last_spoken = current_text

    def on_mount(self):
        self.index = len(self.history)
        print(f"Configs type on mount: {type(self.configs)}")
        return super().on_mount()

    def action_history_up(self):
        if self.index > 0:
            self.index = self.index - 1
            self.value = self.history[self.index]
            self.used_history = True
            self.cursor_position = len(self.value)

    def action_history_down(self):
        if self.index < len(self.history) - 1:
            self.index = self.index + 1
            self.value = self.history[self.index]
            self.used_history = True
            self.cursor_position = len(self.value)

        elif self.index == len(self.history) - 1:
            self.index = self.index + 1
            self.value = self.old_val
            self.used_history = False
            self.cursor_position = len(self.value)
            self.last_spoken = ""

    def action_save_preset(self):
        print(f"Configs type save preset: {type(self.configs)}")

        preset_text = self.value.strip()
        if preset_text and preset_text not in self.configs.get("presets"):
            self.configs["presets"].append(preset_text)
            save_config(CONFIG_FILE, self.configs)

            self.app.query_one("#presets-list", ListView).mount(
                ListItem(LabelItem(preset_text))
            )

    def action_change_mode(self):
        if self.mode == SpeakModes.SUBMIT:
            self.mode = SpeakModes.DEBOUNCE
        else:
            self.mode = SpeakModes.SUBMIT

        self.notify(
            f"Mode changed to: {self.mode.name}",
            title="System",
            severity="information",
            timeout=2,
        )

    @on(Input.Changed)
    def save_old_value(self, event: Input.Changed):
        if not self.used_history:
            self.old_val = event.input.value.strip()

        if self.mode == SpeakModes.DEBOUNCE:
            if self.debounce_timer is not None:
                self.debounce_timer.stop()

            text_speak = event.value

            if text_speak and not self.used_history:
                current_debounce = float(
                    self.configs.get("settings", {}).get("debounce_time", 0.8)
                )
                self.debounce_timer = self.set_timer(
                    current_debounce,
                    lambda: self.speak_only_unspoken(text_speak),
                )

    @on(Input.Submitted)
    def handle_input_submition(self, event: Input.Submitted):
        input_text = event.input.value.strip()
        if not input_text:
            return
        if input_text == self.history[-1] if self.history else None:
            self.value = ""
            self.index = len(self.history)
            if self.mode == SpeakModes.SUBMIT:
                self.audio_queue.put(input_text)
            self.last_spoken = ""
            return
        if self.mode == SpeakModes.SUBMIT:
            self.audio_queue.put(input_text)
        logs = self.app.query_one(RichLog)
        logs.write(f"- {input_text}")
        event.input.value = ""
        self.history.append(input_text)
        self.index = len(self.history)
        self.used_history = False
        self.last_spoken = ""
