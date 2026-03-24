from glob import glob

from piper.voice import PiperVoice
from piper.config import SynthesisConfig
from piper.audio_playback import AudioPlayer
import json
import os


def check_and_create_config(
    file_name: str,
) -> None:
    if file_name not in os.listdir():
        try:
            file = open(file_name, "w")
            file.write(
                """{"settings": {"speed": 1.05,"model": "en_US-danny-low.onnx"}, "presets": []}"""
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
    with AudioPlayer(voice.config.sample_rate) as player:
        for i, audio_chunk in enumerate(voice.synthesize(text, syn_config=syn_config)):
            if i > 0:
                player.play(bytes(0))
            player.play(audio_chunk.audio_int16_bytes)


def get_voices() -> list:
    voices_paths = glob("*.onnx")
    voices = [voice.replace(".onnx", "") for voice in voices_paths]
    return voices
