from glob import glob
import json
import socket
import tkinter as tk


def load_config(file_name: str) -> dict:
    try:
        with open(file_name, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_config(file_name: str, config: dict) -> None:
    with open(file_name, "w") as f:
        json.dump(config, f, indent=4)


def send_message(text: str):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 19620))
        client.sendall(text.encode("utf-8"))
        client.close()
        print(f"Sent: {text}")
    except:
        print("TUI app not running")


BACK_COLOR = "#0B0B27"
history: list[str] = []
last_entery_text: str = ""
history_index: int = None

root = tk.Tk()

root.title("Vexalith Overlay")
root.configure(
    background=BACK_COLOR,
)
root.geometry("400x300")
root.overrideredirect(True)
root.attributes("-topmost", True)

if not glob("overlay_pos.json"):
    with open("overlay_pos.json", "a") as file:
        json.dump({"x": 400, "y": 300}, file, indent=4)


print(load_config("overlay_pos.json"))
drag_data = load_config("overlay_pos.json") or {"x": 0, "y": 0}
root.geometry(f"+{drag_data['x']}+{drag_data['y']}")


def start_drag(event: tk.Event):
    drag_data["x"] = event.x_root - root.winfo_x()
    drag_data["y"] = event.y_root - root.winfo_y()


def do_drag(event: tk.Event):
    x = event.x_root - drag_data["x"]
    y = event.y_root - drag_data["y"]
    root.geometry(f"+{x}+{y}")


def exit_app(event: None):
    save_config("overlay_pos.json", {"x": root.winfo_x(), "y": root.winfo_y()})
    root.quit()
    root.update()


root.bind("<Button-1>", start_drag)
root.bind("<B1-Motion>", do_drag)
root.bind("<Control-b>", exit_app)
root.bind("<Control-B>", exit_app)

root.wm_attributes("-alpha", 0.7)

title = tk.Label(
    root,
    text="Vexalith-Olay | Press Ctrl+b to exit",
    background="#3E3E77",
    padx=10,
    fg="white",
)

title.pack(side="top", fill="x")

middle_frame = tk.Frame(root, background=BACK_COLOR)
middle_frame.pack(side="top", fill="both", expand=True)


list_box = tk.Listbox(
    middle_frame,
    bg=BACK_COLOR,
    fg="white",
    selectbackground=BACK_COLOR,
    selectforeground="white",
    activestyle="none",
    borderwidth=2,
    relief="groove",
    highlightthickness=0,
)
list_box.pack(side="top", fill="both", expand=True, padx=10, pady=(5, 0))

entery = tk.Entry(
    root,
    bg=BACK_COLOR,
    fg="white",
    insertbackground="white",
)
entery.pack(side="bottom", fill="x", padx=10, pady=10)
entery.focus()


def on_input_enter(event: None):
    global history_index

    text = entery.get().strip()
    if not text:
        return

    history.append(text)
    history_index = None
    list_box.insert(tk.END, f"- {text}")
    send_message(text)
    entery.delete(0, tk.END)


def on_arrow_up_history(event: None):
    global last_entery_text, history_index

    if not history:
        return

    if history_index is None:
        last_entery_text = entery.get().strip()
        history_index = len(history) - 1
    elif history_index > 0:
        history_index -= 1

    entery.delete(0, tk.END)
    entery.insert(0, history[history_index])


def on_arrow_down_history(event: None):
    global last_entery_text, history_index

    if history_index is None:
        return

    if history_index < len(history) - 1:
        history_index += 1
        entery.delete(0, tk.END)
        entery.insert(0, history[history_index])
        return

    entery.delete(0, tk.END)
    entery.insert(0, last_entery_text)
    history_index = None


def on_focus_in(event):
    if event.widget == root:
        root.wm_attributes("-alpha", 0.7)
        entery.focus()


def on_focus_out(event):
    if event.widget == root:
        root.wm_attributes("-alpha", 0.3)


entery.bind("<Return>", on_input_enter)
entery.bind("<Up>", on_arrow_up_history)
entery.bind("<Down>", on_arrow_down_history)
root.bind("<FocusIn>", on_focus_in)
root.bind("<FocusOut>", on_focus_out)

root.mainloop()
