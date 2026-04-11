from glob import glob

from huggingface_hub import HfApi
from piper.voice import PiperVoice
from piper.config import SynthesisConfig
import sounddevice as sd
import json
import os


def check_and_create_config(
    file_name: str,
) -> None:
    if "v_models" not in os.listdir():
        os.makedirs("v_models", exist_ok=True)

    if file_name not in os.listdir():
        try:
            file = open(file_name, "w")
            file.write(
                """{"settings": {"model": "get_models","speed": 1.0,"mode": 1, "debounce_time": 0.8}, "presets": []}"""
            )
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


def play_text(text: str, voice: PiperVoice, syn_config: SynthesisConfig):
    with sd.RawOutputStream(
        samplerate=voice.config.sample_rate, channels=1, dtype="int16"
    ) as stream:
        for audio_chunk in voice.synthesize(text, syn_config=syn_config):
            stream.write(audio_chunk.audio_int16_bytes)

        silence_pad = bytes(voice.config.sample_rate)
        stream.write(silence_pad)


def get_voices() -> list[str]:
    voices_paths = glob("v_models/*.onnx")
    return voices_paths


def get_piper_models_tree():
    api = HfApi()
    repo_id = "rhasspy/piper-voices"
    files = api.list_repo_tree(repo_id, recursive=True)

    voice_models = [f.path for f in files if f.path.endswith(".onnx")]
    models_dict: dict = {}

    for model in voice_models:
        parts = model.split("/")
        current_level = models_dict

        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {}

            current_level = current_level[part]

        file_name = parts[-1]
        current_level[file_name] = None

    return models_dict


def get_model_select_options(voices: list[str]) -> list:
    return [
        *[(os.path.basename(voice).replace(".onnx", ""), voice) for voice in voices],
        ("Download models", "get_models"),
    ]
