import json
import os


def check_and_create_config(
    file_name: str,
) -> None:
    if file_name not in os.listdir():
        try:
            file = open(file_name, "w")
            file.write("""{"settings": {},"presets": []}""")
            file.close()
            print("File created ")
        except Exception as e:
            print(f"Somthing bad happened: {e}")


def load_config(file_name: str) -> dict:
    with open(file_name, "r") as f:
        data: dict = json.load(f)
    return data


def save_config(file_name: str, config: dict) -> None:
    with open(file_name, "w") as f:
        json.dump(config, f, indent=4)