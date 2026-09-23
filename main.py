import subprocess
import customtkinter as ctk
import pygame
import random
import cv2
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os
import sys
import json
import tkinter as tk
import time
import math
import threading
import queue
import shutil
import re
import asyncio
from tkinter import filedialog, messagebox, simpledialog
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# --- INITIALISIERUNG & SOUNDS ---
pygame.mixer.init()
volume = 0.5
voice_volume = 1.0

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# --- DESIGN FARBEN ---
ctk.set_appearance_mode("dark")
BG_COLOR = "#120D08" 
SIDEBAR_COLOR = "#211713" 
FRAME_COLOR = "#1A1412" 
BUTTON_COLOR = "#6E1717" 
BUTTON_HOVER = "#922424" 
STOP_COLOR = "#3A0B0B" 
STOP_HOVER = "#5C0D0D" 
TEXT_COLOR = "#E8D7B5" 
LOG_COLOR = "#0D0908" 
ctk.set_default_color_theme("dark-blue")

# --- TEXT POOLS ---
startup_responses = [
    "Alle Systeme sind online Dungeonmaster.", "Ich bin bereit Dungeonmaster.",
    "Systemcheck abgeschlossen. Alle Systeme laufen einwandfrei.", "Willkommen zurück Dungeonmaster.",
    "Bereit für das nächste Abenteuer, Dungeonmaster.", "Alle Sensoren aktiv, ich höre zu.",
    "Sprachsteuerung erfolgreich initialisiert.", "Dungeonmaster ich warte auf deine Befehle.",
    "Bereit die Welt ins Chaos zu stürzen Dungeonmaster."
]

shutdown_responses = [
    "Bis bald, Dungeonmaster.", "Systeme werden heruntergefahren.",
    "Ich verabschiede mich. Bis zum nächsten Abenteuer, Dungeonmaster.",
    "Gute Nacht Dungeonmaster.", "Cortana geht jetzt schlafen.",
    "Dungeonmaster ich freue mich auf den nächsten Einsatz."
]

hello_responses = [
    "Hallo,zusammen!", "Wilkommen Abenteurer, euer Schicksal wartet auf euch.",
    "Schön dass ihr da seid", "Mögen eure Würfel heute gnädig sein",
    "Lasst das Abenteuer beginnen", "Seid gegrüßt Helden",
    "Cortana steht zu euren Diensten", "Ich wünsche euch eine legendäre Session"
]

splitter_responses = [
    "Warnung, Splittersignatur erkannt", "Anomale Energiequelle lokalisiert. Splitter bestätigt",
    "Magische Resonanz erkannt. Splitter befindet sich in unmittelbarer Nähe"
]

# --- HILFSFUNKTIONEN ---
def remove_black_background(image, black_threshold=28, feather=35, crop_transparent=True):
    image = image.convert("RGBA")
    pixels = np.array(image, dtype=np.uint8)
    rgb = pixels[:, :, :3].astype(np.int16)
    original_alpha = pixels[:, :, 3].astype(np.float32)
    brightness = np.max(rgb, axis=2).astype(np.float32)

    if feather <= 0:
        new_alpha = np.where(brightness <= black_threshold, 0.0, original_alpha)
    else:
        fade_end = black_threshold + feather
        fade_factor = ((brightness - black_threshold) / max(feather, 1))
        fade_factor = np.clip(fade_factor, 0.0, 1.0)
        new_alpha = original_alpha * fade_factor
        new_alpha = np.where(brightness >= fade_end, original_alpha, new_alpha)

    pixels[:, :, 3] = new_alpha.astype(np.uint8)
    cleaned = Image.fromarray(pixels, mode="RGBA")
    if crop_transparent:
        alpha_box = cleaned.getchannel("A").getbbox()
        if alpha_box: cleaned = cleaned.crop(alpha_box)
    return cleaned

def get_app_directory():
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~")) if os.name == "nt" else os.path.expanduser("~/.config")
    app_dir = os.path.join(base, "Tormentor")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_settings_path():
    return os.path.join(get_app_directory(), "settings.json")

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- AUDIO GENERIERUNG & DECKUNG ---
async def create_voice(text, dateiname="sound/zufallsantwort.mp3"):
    audio = eleven_client.text_to_speech.convert(
        text=text, voice_id="VS1VhupKYSrE2QWBtG9z", model_id="eleven_multilingual_v2", output_format="mp3_44100_128"
    )
    with open(dateiname, "wb") as f:
        for chunk in audio: f.write(chunk)

async def create_dice_voice(text):
    audio = eleven_client.text_to_speech.convert(
        text=text, voice_id="VS1VhupKYSrE2QWBtG9z", model_id="eleven_multilingual_v2",
        voice_settings={"stability": 0.65, "similarity_boost": 0.85, "speed": 0.85}, output_format="mp3_44100_128"
    )
    with open("sound/wuerfelergebnis.mp3", "wb") as f:
        for chunk in audio: f.write(chunk)

def play_voice_file(filename, duck_music=True):
    with open(get_settings_path(), "r", encoding="utf-8") as f:
        settings = json.load(f)
    m_vol = float(settings.get("music_volume", 0.5))
    v_vol = float(settings.get("voice_volume", 1.0))
    
    voice = pygame.mixer.Sound(filename)
    voice.set_volume(v_vol)
    if duck_music: pygame.mixer.music.set_volume(m_vol * 0.25)
    
    channel = pygame.mixer.Channel(1)
    channel.stop()
    channel.play(voice)
    while channel.get_busy(): pygame.time.wait(100)
    if duck_music: pygame.mixer.music.set_volume(m_vol)

def frage_tormentor(frage, log_callback=None):
    try:
        antwort = client.responses.create(
            model="gpt-4.1-mini",
            instructions="Du bist Tormentor, ein düsterer Dungeons-and-Dragons-Assistent. Antwort auf Deutsch. Formoliere atmosphärisch, aber kurz.",
            input=frage
        )
        text = antwort.output_text.strip()
        if log_callback: log_callback(f"Tormentor: {text}")
        return text
    except Exception as fehler:
        if log_callback: log_callback(f"OpenAI-Fehler: {fehler}")
        return "Die Verbindung zu meinem arkanen Wissen ist unterbrochen."

def roll_dice(command, log_callback=None):
    erlaubte_wuerfel = [4, 6, 8, 10, 12, 20, 100]
    zahlwoerter = {"ein": 1, "eine": 1, "einen": 1, "eins": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10}
    anzahl = 1

    anzahl_treffer = re.search(r"\b(\d+)\s*(?:mal\s*)?(?:w|würfel)?", command)
    if anzahl_treffer: anzahl = int(anzahl_treffer.group(1))
    else:
        for wort, zahl in zahlwoerter.items():
            if re.search(rf"\b{wort}\b", command): anzahl = zahl; break

    wuerfel_treffer = re.search(r"(?:w\s*)?(4|6|8|10|12|20|100)\b", command)
    if not wuerfel_treffer: return
    seiten = int(wuerfel_treffer.group(1))
    if seiten not in erlaubte_wuerfel: return

    anzahl = max(1, min(anzahl, 20))
    ergebnisse = [random.randint(1, seiten) for _ in range(anzahl)]
    gesamtergebnis = sum(ergebnisse)

    if log_callback:
        if anzahl == 1: log_callback(f"Würfelergebnis: W{seiten} -> {ergebnisse[0]}")
        else: log_callback(f"Würfelergebnis: {anzahl}W{seiten} -> {ergebnisse} | Summe: {gesamtergebnis}")

    if anzahl == 1:
        ergebnis = ergebnisse[0]
        if seiten == 20 and ergebnis == 20: antwort = "Natürliche 20! Kritischer Erfolg!"
        elif seiten == 20 and ergebnis == 1: antwort = "Natürliche 1! Kritischer Fehlschlag!"
        else: antwort = f"Der W {seiten} zeigt eine {ergebnis}."
    else:
        antwort = f"Ich habe {anzahl} W {seiten} gewürfelt. Die Summe beträgt {gesamtergebnis}."
   
    asyncio.run(create_dice_voice(antwort))
    play_voice_file("sound/wuerfelergebnis.mp3", duck_music=True)

# --- RUN CORTANA LOGIK THREAD ---
def run_cortana(stop_event=None, log_callback=None, lore_callback=None):
    from audio_input import speech_source
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5
    
    while stop_event is None or not stop_event.is_set():
        with speech_source() as source:
            if log_callback: log_callback("Cortana hört zu...")
            try:
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=15)
                command = recognizer.recognize_google(audio, language="de-DE").lower()
                if log_callback: log_callback(f"Erkannt: {command}")
            except: continue

            wake = re.search(r"\b(?:cortana|katana|kortana)\b", command)
            if not wake: continue
            direct_command = command[wake.end():].strip(" ,.!?")

            if not direct_command:
                if log_callback: log_callback("Cortana wurde aktiviert. Ja, Dungeonmaster?")
                if not os.path.isfile(resource_path("sound/aktivierung.mp3")):
                    asyncio.run(create_voice("Ja, Dungeonmaster?", "sound/aktivierung.mp3"))
                play_voice_file("sound/aktivierung.mp3", duck_music=True)

                with speech_source() as cmd_source:
                    try: command_audio = recognizer.listen(cmd_source, timeout=10, phrase_time_limit=15)
                    except Exception: continue
                    try:
                        command = recognizer.recognize_google(command_audio, language="de-DE").lower()
                        if log_callback: log_callback(f"Befehl: {command}")
                    except Exception: continue
            else:
                command = direct_command

            command = re.sub(r"[,.!?]", "", command).strip()
            if command in ("starte aufnahme", "starte die aufnahme", "aufnahme starten", "beginne aufnahme"):
                if lore_callback: lore_callback("start")
                elif log_callback: log_callback("Bitte Tormentor Lore in der Desktop-Oberfläche öffnen.")
                continue
            if command in ("beende aufnahme", "beende die aufnahme", "aufnahme beenden", "stoppe aufnahme", "stoppe die aufnahme", "aufnahme stoppen"):
                if lore_callback: lore_callback("stop")
                continue

            if "bist du da" in command:
                txt = random.choice(startup_responses)
                asyncio.run(create_voice(txt))
                play_voice_file("sound/zufallsantwort.mp3")
            elif "würfel" in command or "würfle" in command:
                roll_dice(command, log_callback)
            elif "frage tormentor" in command:
                frage = command.replace("frage tormentor", "").strip()
                antwort = frage_tormentor(frage, log_callback)
                asyncio.run(create_voice(antwort))
                play_voice_file("sound/zufallsantwort.mp3")
            elif "stopp" in command or "stop" in command:
                pygame.mixer.music.stop()

# --- APP CLASS ---
class TormentorApp(ctk.CTk):
    def resource_path(self, relative_path): return resource_path(relative_path)
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self._ensure_media_settings()
        self.settings_button_position = (828, 18)
        self.settings_button_size = (52, 52)

        global volume, voice_volume
        volume = max(0.0, min(1.0, float(self.settings.get("music_volume", 0.5))))
        pygame.mixer.music.set_volume(volume)
