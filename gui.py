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
from tkinter import filedialog, messagebox, simpledialog
from main import run_cortana

pygame.mixer.init()
volume = 0.5
voice_volume = 1.0


ctk.set_appearance_mode("dark")
BG_COLOR = "#120D08" #fast schwarz
SIDEBAR_COLOR = "#211713" #dunkelbraun
FRAME_COLOR = "#1A1412" #schwarzbraun
BUTTON_COLOR = "#6E1717" #dunkelrot
BUTTON_HOVER = "#922424" #hellrot
STOP_COLOR = "#3A0B0B" #dunkles rot
STOP_HOVER = "#5C0D0D" #helles rot
TEXT_COLOR = "#E8D7B5" #beige
LOG_COLOR = "#0D0908" #schwarz
ctk.set_default_color_theme("dark-blue")


def remove_black_background(
        image,
        black_threshold=28,
        feather=35,
        crop_transparent=True
):
    """
    Entfernt schwarze bzw. fast schwarze Bildflächen und macht sie transparent.
    """
    image = image.convert("RGBA")
    pixels = np.array(image, dtype=np.uint8)

    rgb = pixels[:, :, :3].astype(np.int16)
    original_alpha = pixels[:, :, 3].astype(np.float32)
    brightness = np.max(rgb, axis=2).astype(np.float32)

    if feather <= 0:
        new_alpha = np.where(
            brightness <= black_threshold,
            0.0,
            original_alpha
        )
    else:
        fade_end = black_threshold + feather
        fade_factor = (
            (brightness - black_threshold)
            / max(feather, 1)
        )
        fade_factor = np.clip(fade_factor, 0.0, 1.0)
        new_alpha = original_alpha * fade_factor
        new_alpha = np.where(
            brightness >= fade_end,
            original_alpha,
            new_alpha
        )

    pixels[:, :, 3] = new_alpha.astype(np.uint8)
    cleaned = Image.fromarray(pixels, mode="RGBA")

    if crop_transparent:
        alpha_box = cleaned.getchannel("A").getbbox()
        if alpha_box:
            cleaned = cleaned.crop(alpha_box)

    return cleaned

def get_app_directory():
    """
    Gemeinsamer, beschreibbarer Tormentor-Ordner.
    GUI und main.py greifen dadurch garantiert auf dieselbe settings.json zu.
    """
    if os.name == "nt":
        base = os.environ.get(
            "LOCALAPPDATA",
            os.path.expanduser("~")
        )
    else:
        base = os.path.expanduser("~/.config")

    app_dir = os.path.join(base, "Tormentor")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_settings_path():
    return os.path.join(
        get_app_directory(),
        "settings.json"
    )
def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

class TormentorApp(ctk.CTk):
    def resource_path(self, relative_path):
        return resource_path(relative_path)
    def __init__(self):
        super().__init__()

        self.settings = self.load_settings()
        self._ensure_media_settings()
        self.settings_button_position = (828, 18)
        self.settings_button_size = (52, 52)

        global volume, voice_volume

        volume = float(
            self.settings.get(
                "music_volume",
                self.settings.get("volume", 0.5)
            )
        )
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)

        voice_volume = float(
            self.settings.get("voice_volume", 1.0)
        )
        voice_volume = max(0.0, min(1.0, voice_volume))

        self.voice_volume_dragging = False
        self.sound_volume_dragging = False

        self.video_path = self.resource_path(
            os.path.join("assets", "background.mp4")
        )
        self.video_capture = cv2.VideoCapture(self.video_path)
        self.video_label = tk.Label(
            self,
            text="",
            bg="#0A0A0A",
            borderwidth=0,
            highlightthickness=0
        )
        self.video_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Bosskampf-Spezialhintergrund (PNG + Animation direkt in der GUI)
        self.bossfight_mode = False
        self.bossfight_started_at = 0.0
        self.bossfight_background_pil = None
        # Cache fuer den Bosskampf: verhindert teures Skalieren/Weichzeichnen
        # in jedem einzelnen Frame. Wird nur bei Fenstergroessenaenderung neu gebaut.
        self._boss_cache_size = None
        self._boss_base_cache = None
        self._boss_glow_cache = None
        self._boss_smoke_cache = None
        boss_image_path = self.resource_path(
            os.path.join("assets", "bossfight_crossed_swords.png")
        )
        if os.path.exists(boss_image_path):
            try:
                self.bossfight_background_pil = Image.open(
                    boss_image_path
                ).convert("RGBA")
            except OSError:
                self.bossfight_background_pil = None

        self.title("Tormentor 2.0 – created with ChatGPT/Kodex")
        self.geometry("900x600")
        self.minsize(800, 520)
        self.version_label = ctk.CTkLabel(
            self, text="Version 2.0 created with ChatGPT/Kodex",
            text_color=TEXT_COLOR, fg_color=FRAME_COLOR,
            font=ctk.CTkFont(size=12)
        )
        self.version_label.place(relx=0.5, rely=1.0, anchor="s")

        # Alle Positionen basieren auf dieser Entwurfsgröße.
        # Im Vollbild werden sie proportional hochskaliert.
        self.design_width = 900
        self.design_height = 600

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        stone_image = Image.open(
            self.resource_path("assets/stone_button.png")
        ).convert("RGBA")

        stone_image = remove_black_background(
            stone_image,
            black_threshold=24,
            feather=35,
            crop_transparent=True
        )

        self.stone_button_pil = stone_image.resize(
            (220, 150),
            Image.Resampling.LANCZOS
        )
        self.stone_button_photo = ImageTk.PhotoImage(
            self.stone_button_pil
        )

        # ---------------------------------------------------------
        # Schwebende Bilder laden und vom schwarzen Hintergrund lösen
        # ---------------------------------------------------------

        cortana_image = Image.open(
            self.resource_path("assets/cortana_header.png")
        ).convert("RGBA")

        cortana_image = remove_black_background(
            cortana_image,
            black_threshold=28,
            feather=35,
            crop_transparent=True
        )

        # Größe und Position des Cortana-Headers
        self.cortana_header_pil = cortana_image.resize(
            (230, 150),
            Image.Resampling.LANCZOS
        )
        self.cortana_header_position = (-40, 7)

        start_image = Image.open(
            self.resource_path("assets/start_button.png")
        ).convert("RGBA")

        start_image = remove_black_background(
            start_image,
            black_threshold=28,
            feather=35,
            crop_transparent=True
        )

        stop_image = Image.open(
            self.resource_path("assets/stop_button.png")
        ).convert("RGBA")

        stop_image = remove_black_background(
            stop_image,
            black_threshold=28,
            feather=35,
            crop_transparent=True
        )

        # Beide Schaltflächen erhalten exakt dieselbe sichtbare Größe.
        self.start_button_pil = start_image.resize(
            (130, 100),
            Image.Resampling.LANCZOS
        )
        self.stop_button_pil = stop_image.resize(
            (120, 90),
            Image.Resampling.LANCZOS
        )

        # Positionen: (x, y)
        self.start_button_position = (10, 80)
        self.stop_button_position = (15, 140)

        # Neon-Lautstärkeregler
        volume_slider_image = Image.open(
            self.resource_path("assets/volume_slider.png")
        ).convert("RGBA")

        volume_slider_image = remove_black_background(
            volume_slider_image,
            black_threshold=22,
            feather=45,
            crop_transparent=True
        )

        self.volume_slider_pil = volume_slider_image.resize(
            (110, 40),
            Image.Resampling.LANCZOS
        )

        # Linker Regler: Cortana / Stimme
        self.voice_slider_position = (10, 240)

        # Rechter Regler: Musik / Sounds
        self.sound_slider_position = (10, 305)

        # Reglerbahn relativ zum PNG-Bild:
        # links, oben, rechts, unten
        self.volume_track_relative = (24, 13, 100, 30)

        # ---------------------------------------------------------
        # Schwebender Hauptbereich – ohne CTkFrame und ohne schwarze Flächen
        # ---------------------------------------------------------
        self.main_button_width = 160
        self.main_button_height = 90

        self.main_buttons = [
            {
                "text": "Rätsel",
                "command": self.play_riddle,
                "position": (315, 135)
            },
            {
                "text": "Taverne",
                "command": self.play_tavern,
                "position": (500, 135)
            },
            {
                "text": "Dungeon",
                "command": self.play_dungeon,
                "position": (315, 215)
            },
            {
                "text": "Wald",
                "command": self.play_forest,
                "position": (500, 215)
            },
            {
                "text": "Höhle",
                "command": self.play_cave,
                "position": (315, 295)
            },
            {
                "text": "Bosskampf",
                "command": self.play_bossfight,
                "position": (500, 295)
            },
            {
                "text": "Musik stoppen",
                "command": self.stop_music,
                "position": (377, 375),
                "width": 220,
                "height": 80
            }
        ]

        self.status_text = "Status: Cortana schläft"
        self.log_messages = [
            f"[{time.strftime('%H:%M:%S')}] Tormentor-Benutzeroberfläche gestartet."
        ]

        # Thread-sichere Warteschlange für Meldungen aus Cortana.
        # Tkinter darf ausschließlich vom GUI-Hauptthread angesprochen werden.
        self.log_queue = queue.Queue()
        self.after(50, self.process_log_queue)

        self.hovered_control = None

        # Klicks und Ziehen werden direkt auf dem Video ausgewertet.
        self.video_label.bind(
            "<Button-1>",
            self.handle_video_press
        )
        self.video_label.bind(
            "<B1-Motion>",
            self.handle_video_drag
        )
        self.video_label.bind(
            "<ButtonRelease-1>",
            self.handle_video_release
        )
        self.video_label.bind(
            "<Motion>",
            self.handle_video_motion
        )
        self.video_label.configure(cursor="")

        # Video erst starten, wenn alle Bilder vollständig geladen sind.
        self.update_video()


        # Der Hauptbereich wird vollständig in update_video()
        # direkt auf den animierten Hintergrund gezeichnet.
    

    def get_pil_font(self, size, bold=False):
        """
        Lädt nach Möglichkeit eine gut lesbare Windows-Schrift.
        Fällt andernfalls auf die PIL-Standardschrift zurück.
        """
        candidates = []

        if os.name == "nt":
            windows_fonts = os.path.join(
                os.environ.get("WINDIR", r"C:\Windows"),
                "Fonts"
            )
            candidates.extend([
                os.path.join(
                    windows_fonts,
                    "georgiab.ttf" if bold else "georgia.ttf"
                ),
                os.path.join(
                    windows_fonts,
                    "arialbd.ttf" if bold else "arial.ttf"
                )
            ])

        for font_path in candidates:
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue

        return ImageFont.load_default()

    def draw_centered_text(
            self,
            draw,
            position,
            text,
            font,
            fill,
            stroke_width=0,
            stroke_fill=None
    ):
        draw.text(
            position,
            text,
            font=font,
            fill=fill,
            anchor="mm",
            stroke_width=stroke_width,
            stroke_fill=stroke_fill
        )

    def draw_floating_main_ui(self, overlay):
        draw = ImageDraw.Draw(overlay)
        scale_x, scale_y = self.get_scale_values()
        uniform_scale = min(scale_x, scale_y)

        status_font = self.get_pil_font(
            max(12, int(21 * uniform_scale)),
            bold=True
        )
        button_font = self.get_pil_font(
            max(9, int(13 * uniform_scale)),
            bold=True
        )
        log_font = self.get_pil_font(
            max(8, int(12 * uniform_scale)),
            bold=False
        )

        status_position = self.scale_position((490, 105))
        self.draw_centered_text(
            draw,
            status_position,
            self.status_text,
            status_font,
            (240, 242, 255, 255),
            stroke_width=max(1, int(2 * uniform_scale)),
            stroke_fill=(20, 12, 30, 240)
        )

        for index, button in enumerate(self.main_buttons):
            x, y = self.scale_position(button["position"])

            original_width = button.get(
                "width",
                self.main_button_width
            )
            original_height = button.get(
                "height",
                self.main_button_height
            )

            width, height = self.scale_size(
                (original_width, original_height)
            )

            stone = self.stone_button_pil.resize(
                (width, height),
                Image.Resampling.LANCZOS
            )

            if self.hovered_control == ("main", index):
                glow_margin = 2
                glow = Image.new(
                    "RGBA",
                    (
                        width + glow_margin * 2,
                        height + glow_margin * 2
                    ),
                    (0, 0, 0, 0)
                )
                glow_draw = ImageDraw.Draw(glow)
                glow_draw.rounded_rectangle(
                    (
                        glow_margin // 2,
                        glow_margin // 2,
                        width + glow_margin + glow_margin // 2,
                        height + glow_margin + glow_margin // 2
                    ),
                    radius=max(6, int(14 * uniform_scale)),
                    outline=(255, 185, 70, 150),
                    width=max(1, int(2 * uniform_scale))
                )
                overlay.alpha_composite(
                    glow,
                    (x - glow_margin, y - glow_margin)
                )

            overlay.alpha_composite(stone, (x, y))

            self.draw_centered_text(
                draw,
                (
                    x + width // 2,
                    y + height // 2 - int(5 * scale_y)
                ),
                button["text"],
                button_font,
                (248, 232, 176, 255),
                stroke_width=max(1, int(uniform_scale)),
                stroke_fill=(40, 20, 10, 220)
            )

        # Logbox: mehrere Meldungen dauerhaft sichtbar halten.
        # Dadurch verschwinden erkannte Sprachbefehle und Fehlermeldungen
        # nicht mehr sofort, sobald die nächste Meldung eintrifft.
        log_x, log_y = self.scale_position((255, 462))
        log_w, log_h = self.scale_size((500, 105))

        draw.rounded_rectangle(
            (log_x, log_y, log_x + log_w, log_y + log_h),
            radius=max(6, int(10 * uniform_scale)),
            fill=(22, 14, 18, 165),
            outline=(150, 100, 60, 210),
            width=max(1, int(2 * uniform_scale))
        )

        # Die letzten vier Meldungen untereinander anzeigen.
        visible_messages = self.log_messages[-4:]
        line_height = max(13, int(20 * uniform_scale))
        text_x = log_x + int(12 * scale_x)
        text_y = log_y + int(10 * scale_y)

        for index, message in enumerate(visible_messages):
            # Sehr lange Meldungen kürzen, damit sie nicht aus der Box laufen.
            if len(message) > 78:
                message = message[:75] + "..."

            draw.text(
                (text_x, text_y + index * line_height),
                message,
                font=log_font,
                fill=(238, 224, 195, 255)
            )

    def get_scale_values(self):
        window_width = max(self.winfo_width(), 1)
        window_height = max(self.winfo_height(), 1)

        scale_x = window_width / self.design_width
        scale_y = window_height / self.design_height

        return scale_x, scale_y

    def scale_position(self, position):
        scale_x, scale_y = self.get_scale_values()
        return (
            int(position[0] * scale_x),
            int(position[1] * scale_y)
        )

    def scale_size(self, size):
        scale_x, scale_y = self.get_scale_values()
        return (
            max(1, int(size[0] * scale_x)),
            max(1, int(size[1] * scale_y))
        )

    def unscale_mouse(self, x, y):
        scale_x, scale_y = self.get_scale_values()

        if scale_x <= 0 or scale_y <= 0:
            return x, y

        return (
            x / scale_x,
            y / scale_y
        )

    def _cover_pil_image(self, source, width, height, zoom=1.0):
        """Skaliert ein PIL-Bild wie CSS cover und schneidet es mittig zu."""
        src_w, src_h = source.size
        scale = max(width / src_w, height / src_h) * max(zoom, 1.0)
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))
        resized = source.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max((new_w - width) // 2, 0)
        top = max((new_h - height) // 2, 0)
        return resized.crop((left, top, left + width, top + height))

    def _prepare_bossfight_cache(self, width, height):
        """Bereitet statische Bosskampf-Ebenen nur bei Groessenaenderung vor."""
        cache_size = (width, height)
        if self._boss_cache_size == cache_size and self._boss_base_cache is not None:
            return

        self._boss_cache_size = cache_size

        # Hintergrund nur EINMAL pro Fenstergroesse skalieren.
        self._boss_base_cache = self._cover_pil_image(
            self.bossfight_background_pil, width, height, zoom=1.0
        ).convert("RGBA")

        # Weiches Zentrumsgluehen einmal vorberechnen. Spaeter wird nur noch
        # dessen Transparenz geaendert - wesentlich guenstiger als Blur pro Frame.
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        cx = width // 2
        cy = int(height * 0.50)
        rx = int(width * 0.19)
        ry = int(height * 0.28)
        glow_draw.ellipse(
            (cx - rx, cy - ry, cx + rx, cy + ry),
            fill=(255, 48, 12, 180)
        )
        glow = glow.filter(ImageFilter.GaussianBlur(max(12, int(width * 0.025))))
        self._boss_glow_cache = glow

        # Rauch ebenfalls nur einmal weichzeichnen. Die fertige Ebene wird
        # waehrend der Animation lediglich langsam verschoben.
        smoke = Image.new("RGBA", (width + 180, height), (0, 0, 0, 0))
        smoke_draw = ImageDraw.Draw(smoke)
        for i in range(7):
            x = int((0.10 + i * 0.15) * width) + 90
            y = int(height * (0.64 + 0.035 * math.sin(i * 1.4)))
            rx = int(width * (0.11 + (i % 3) * 0.02))
            ry = int(height * (0.045 + (i % 2) * 0.018))
            smoke_draw.ellipse(
                (x - rx, y - ry, x + rx, y + ry),
                fill=(100, 96, 92, 22 + (i % 3) * 5)
            )
        smoke = smoke.filter(ImageFilter.GaussianBlur(max(10, int(width * 0.018))))
        self._boss_smoke_cache = smoke

    def render_bossfight_background(self, width, height):
        """Fluessige Bosskampf-Animation mit gecachten Effekten."""
        if self.bossfight_background_pil is None:
            return None

        self._prepare_bossfight_cache(width, height)

        elapsed = time.time() - self.bossfight_started_at
        pulse = (math.sin(elapsed * 2.1) + 1.0) / 2.0
        slow_pulse = (math.sin(elapsed * 0.8) + 1.0) / 2.0

        # Copy ist viel billiger als das komplette PNG pro Frame neu zu skalieren.
        base = self._boss_base_cache.copy()

        # Pulsierendes Glimmen: nur Alpha aendern, kein erneutes Blur.
        glow_alpha = int(55 + 75 * pulse)
        glow = self._boss_glow_cache.copy()
        alpha = glow.getchannel("A").point(lambda a: (a * glow_alpha) // 180)
        glow.putalpha(alpha)
        base = Image.alpha_composite(base, glow)

        # Langsame Rauchbewegung durch Verschieben einer bereits vorbereiteten Ebene.
        smoke_shift = int(70 * math.sin(elapsed * 0.20))
        smoke_frame = self._boss_smoke_cache.crop(
            (90 + smoke_shift, 0, 90 + smoke_shift + width, height)
        )
        base = Image.alpha_composite(base, smoke_frame)

        # Funken sind klein und daher guenstig direkt zu zeichnen.
        sparks_draw = ImageDraw.Draw(base)
        for i in range(18):
            speed = 26 + (i % 6) * 7
            travel = (elapsed * speed + i * 53) % max(height, 1)
            y = int(height - travel)
            x_base = (i * 97) % max(width, 1)
            x = int((x_base + 14 * math.sin(elapsed * 1.2 + i)) % max(width, 1))
            r = 1 + (i % 2)
            a = int(120 + 90 * slow_pulse)
            sparks_draw.ellipse(
                (x - r, y - r, x + r, y + r),
                fill=(255, 150 + (i % 3) * 22, 45, min(a, 230))
            )

        return base

    def update_video(self):
        glow_margin = 6

        window_width = max(self.winfo_width(), 1)
        window_height = max(self.winfo_height(), 1)

        if self.bossfight_mode and self.bossfight_background_pil is not None:
            image = self.render_bossfight_background(window_width, window_height)
        else:
            success, frame = self.video_capture.read()

            if not success:
                self.video_capture.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    0
                )
                success, frame = self.video_capture.read()

            if not success:
                self.after(100, self.update_video)
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_height, frame_width = frame.shape[:2]
            scale = max(
                window_width / frame_width,
                window_height / frame_height
            )
            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)
            frame = cv2.resize(
                frame,
                (new_width, new_height),
                interpolation=cv2.INTER_AREA
            )
            x_start = max((new_width - window_width) // 2, 0)
            y_start = max((new_height - window_height) // 2, 0)
            frame = frame[
                y_start:y_start + window_height,
                x_start:x_start + window_width
            ]
            image = Image.fromarray(frame).convert("RGBA")

        # Ein gemeinsames transparentes Overlay für Header und Buttons.
        overlay = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0)
        )

        pulse = (math.sin(time.time() + 4) + 1) / 2
        alpha = int(70 + pulse * 140)

        if hasattr(self, "cortana_header_pil"):
            header_position = self.scale_position(
                self.cortana_header_position
            )
            header_size = self.scale_size(
                self.cortana_header_pil.size
            )
            header_image = self.cortana_header_pil.resize(
                header_size,
                Image.Resampling.LANCZOS
            )
            
            overlay.paste(
                header_image,
                header_position,
                header_image
            )

        if hasattr(self, "start_button_pil"):
            start_position = self.scale_position(
                self.start_button_position
            )
            start_size = self.scale_size(
                self.start_button_pil.size
            )
            start_image = self.start_button_pil.resize(
                start_size,
                Image.Resampling.LANCZOS
            )

            if self.hovered_control == ("start", 0):
                pulse = (math.sin(time.time() * 4) + 1) / 2
                alpha = int(90 + pulse * 110)
                hover_width = int(start_size[0] * 0.72)
                hover_height = int(start_size[1] * 0.42)
                hover_x = start_position[0] + (start_size[0] - hover_width) // 2
                hover_y = start_position[1] + (start_size[1] - hover_height) // 2
                glow = Image.new(
                "RGBA",
                (start_size[0] + glow_margin * 2, start_size[1] + glow_margin * 2),
                (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow)

                glow_draw.rounded_rectangle(
                        (
                            4,
                            4,
                            hover_width + 4,
                            hover_height + 4
                        ),
                        radius=14,
                        outline=(0, 255, 120, alpha),
                        width=2
                    )
                overlay.alpha_composite(
                    glow,
                    (
                        hover_x - 4,
                        hover_y - 4
                )
            )

        overlay.paste(
            start_image,
            start_position,
            start_image
            )

        if hasattr(self, "stop_button_pil"):
            stop_position = self.scale_position(
                self.stop_button_position
            )
            stop_size = self.scale_size(
                self.stop_button_pil.size
            )
            stop_image = self.stop_button_pil.resize(
                stop_size,
                Image.Resampling.LANCZOS
            )

            if self.hovered_control == ("stop", 0):
                pulse = (math.sin(time.time() * 4) + 1) / 2
                alpha = int(90 + pulse * 110)
                hover_width = int(stop_size[0] * 0.72)
                hover_height = int(stop_size[1] * 0.42)
                hover_x = stop_position[0] + (stop_size[0] - hover_width) // 2
                hover_y = stop_position[1] + (stop_size[1] - hover_height) // 2
                glow = Image.new(
                "RGBA",
                (stop_size[0] + 30, stop_size[1] + 30),
                (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow)

                glow_draw.rounded_rectangle(
                        (
                            4,
                            4,
                            hover_width + 4,
                            hover_height + 4
                        ),
                        radius=14,
                        outline=(255, 60, 60, alpha),
                        width=2
                    )
                overlay.alpha_composite(
                        glow,
                        (hover_x - 4, hover_y - 4)
                    )

        overlay.paste(
            stop_image,
            stop_position,
            stop_image
            )

        if hasattr(self, "volume_slider_pil"):
            draw = ImageDraw.Draw(overlay)

            self.draw_volume_slider(
                overlay,
                draw,
                self.voice_slider_position,
                voice_volume,
                "CORTANA"
            )

            self.draw_volume_slider(
                overlay,
                draw,
                self.sound_slider_position,
                volume,
                "SOUNDS"
            )

        self.draw_settings_button(overlay)
        self.draw_floating_main_ui(overlay)

        image = Image.alpha_composite(
            image,
            overlay
        )

        self.video_image = ImageTk.PhotoImage(
            image=image.convert("RGB")
        )

        self.video_label.configure(
            image=self.video_image
        )
        self.after(
            33,
            self.update_video
        )

    def draw_volume_slider(
            self,
            overlay,
            draw,
            position,
            current_volume,
            label
    ):
        slider_x, slider_y = self.scale_position(position)
        slider_size = self.scale_size(
            self.volume_slider_pil.size
        )
        slider_image = self.volume_slider_pil.resize(
            slider_size,
            Image.Resampling.LANCZOS
        )

        overlay.paste(
            slider_image,
            (slider_x, slider_y),
            slider_image
        )

        scale_x, scale_y = self.get_scale_values()
        rel_left, rel_top, rel_right, rel_bottom = (
            self.volume_track_relative
        )
        rel_left = int(rel_left * scale_x)
        rel_right = int(rel_right * scale_x)
        rel_top = int(rel_top * scale_y)
        rel_bottom = int(rel_bottom * scale_y)

        track_left = slider_x + rel_left
        track_top = slider_y + rel_top
        track_right = slider_x + rel_right
        track_bottom = slider_y + rel_bottom

        draw.text(
            (
                slider_x + int(65 * self.get_scale_values()[0]),
                slider_y - int(8 * self.get_scale_values()[1])
            ),
            label,
            anchor="mm",
            fill=(235, 220, 255, 255)
        )

        draw.rounded_rectangle(
            (track_left, track_top, track_right, track_bottom),
            radius=9,
            fill=(10, 8, 18, 235),
            outline=(255, 35, 190, 235),
            width=2
        )

        fill_right = int(
            track_left
            + (track_right - track_left) * current_volume
        )

        if fill_right > track_left:
            draw.rounded_rectangle(
                (track_left, track_top, fill_right, track_bottom),
                radius=9,
                fill=(0, 225, 255, 245)
            )

        knob_x = fill_right
        knob_y = (track_top + track_bottom) // 2
        knob_radius = max(7, int(12 * min(self.get_scale_values())))

        draw.ellipse(
            (
                knob_x - knob_radius - 5,
                knob_y - knob_radius - 5,
                knob_x + knob_radius + 5,
                knob_y + knob_radius + 5
            ),
            fill=(255, 0, 200, 75)
        )

        draw.ellipse(
            (
                knob_x - knob_radius,
                knob_y - knob_radius,
                knob_x + knob_radius,
                knob_y + knob_radius
            ),
            fill=(20, 10, 35, 255),
            outline=(255, 70, 220, 255),
            width=4
        )

    def handle_video_press(self, event):
        mouse_x, mouse_y = self.unscale_mouse(
            event.x,
            event.y
        )

        start_x, start_y = self.start_button_position
        start_width, start_height = self.start_button_pil.size

        stop_x, stop_y = self.stop_button_position
        stop_width, stop_height = self.stop_button_pil.size

        if (
            start_x <= mouse_x <= start_x + start_width
            and start_y <= mouse_y <= start_y + start_height
        ):
            self.start_cortana()
            return

        if (
            stop_x <= mouse_x <= stop_x + stop_width
            and stop_y <= mouse_y <= stop_y + stop_height
        ):
            self.stop_cortana()
            return

        sx, sy = self.settings_button_position
        sw, sh = self.settings_button_size
        if sx <= mouse_x <= sx + sw and sy <= mouse_y <= sy + sh:
            self.open_settings_menu()
            return

        for button in self.main_buttons:
            x, y = button["position"]
            width = button.get(
                "width",
                self.main_button_width
            )
            height = button.get(
                "height",
                self.main_button_height
            )

            if (
                x <= mouse_x <= x + width
                and y <= mouse_y <= y + height
            ):
                button["command"]()
                return

        if self.is_over_slider(
            mouse_x,
            mouse_y,
            self.voice_slider_position
        ):
            self.voice_volume_dragging = True
            self.set_voice_volume_from_mouse(
                mouse_x,
                save=False,
                log=False
            )
            return

        if self.is_over_slider(
            mouse_x,
            mouse_y,
            self.sound_slider_position
        ):
            self.sound_volume_dragging = True
            self.set_sound_volume_from_mouse(
                mouse_x,
                save=False,
                log=False
            )

    def handle_video_drag(self, event):
        mouse_x, _ = self.unscale_mouse(
            event.x,
            event.y
        )

        if self.voice_volume_dragging:
            self.set_voice_volume_from_mouse(
                mouse_x,
                save=False,
                log=False
            )

        if self.sound_volume_dragging:
            self.set_sound_volume_from_mouse(
                mouse_x,
                save=False,
                log=False
            )

    def handle_video_release(self, event):
        mouse_x, _ = self.unscale_mouse(
            event.x,
            event.y
        )

        if self.voice_volume_dragging:
            self.voice_volume_dragging = False
            self.set_voice_volume_from_mouse(
                mouse_x,
                save=True,
                log=True
            )

        if self.sound_volume_dragging:
            self.sound_volume_dragging = False
            self.set_sound_volume_from_mouse(
                mouse_x,
                save=True,
                log=True
            )

    def handle_video_motion(self, event):
        mouse_x, mouse_y = self.unscale_mouse(
            event.x,
            event.y
        )
        hovered = None

        if self.is_over_image(
            mouse_x,
            mouse_y,
            self.start_button_position,
            self.start_button_pil.size
        ):
            hovered = ("start", 0)

        elif self.is_over_image(
            mouse_x,
            mouse_y,
            self.stop_button_position,
            self.stop_button_pil.size
        ):
            hovered = ("stop", 0)

        else:
            for index, button in enumerate(self.main_buttons):
                x, y = button["position"]
                width = button.get(
                    "width",
                    self.main_button_width
                )
                height = button.get(
                    "height",
                    self.main_button_height
                )

                if (
                    x <= mouse_x <= x + width
                    and y <= mouse_y <= y + height
                ):
                    hovered = ("main", index)
                    break

        sx, sy = self.settings_button_position
        sw, sh = self.settings_button_size
        if sx <= mouse_x <= sx + sw and sy <= mouse_y <= sy + sh:
            hovered = ("settings", 0)

        over_voice = self.is_over_slider(
            mouse_x,
            mouse_y,
            self.voice_slider_position
        )
        over_sound = self.is_over_slider(
            mouse_x,
            mouse_y,
            self.sound_slider_position
        )

        if hovered != ("settings", 0):
            if over_voice:
                hovered = ("voice", 0)
            elif over_sound:
                hovered = ("sound", 0)

        self.hovered_control = hovered
        self.video_label.configure(
            cursor="hand2" if hovered is not None else ""
        )

    def is_over_image(self, x, y, position, size):
        image_x, image_y = position
        image_width, image_height = size

        return (
            image_x <= x <= image_x + image_width
            and image_y <= y <= image_y + image_height
        )

    def is_over_slider(self, x, y, position):
        return self.is_over_image(
            x,
            y,
            position,
            self.volume_slider_pil.size
        )

    def volume_from_mouse(self, mouse_x, position):
        slider_x, _ = position
        rel_left, _, rel_right, _ = self.volume_track_relative

        track_left = slider_x + rel_left
        track_right = slider_x + rel_right

        if track_right <= track_left:
            return 0.0

        new_volume = (
            mouse_x - track_left
        ) / (
            track_right - track_left
        )

        return max(0.0, min(1.0, new_volume))

    def set_voice_volume_from_mouse(
            self,
            mouse_x,
            save=False,
            log=False
    ):
        global voice_volume

        voice_volume = self.volume_from_mouse(
            mouse_x,
            self.voice_slider_position
        )

        self.settings["voice_volume"] = voice_volume

        # Schon beim Ziehen speichern, damit main.py den Wert live lesen kann.
        self.save_settings()

        if log:
            self.add_log(
                f"Cortana-Lautstärke: {int(voice_volume * 100)} %"
            )

    def set_sound_volume_from_mouse(
            self,
            mouse_x,
            save=False,
            log=False
    ):
        global volume

        volume = self.volume_from_mouse(
            mouse_x,
            self.sound_slider_position
        )

        pygame.mixer.music.set_volume(volume)

        if save:
            self.settings["volume"] = volume
            self.settings["music_volume"] = volume
            self.save_settings()

        if log:
            self.add_log(
                f"Sound-Lautstärke: {int(volume * 100)} %"
            )

    def _load_background_video(self, new_video_path, display_name=None):
        """Lädt ein MP4 als animierten Hintergrund."""
        print(f"Video wird gesucht: {new_video_path}")

        if not os.path.exists(new_video_path):
            self.add_log(
                f"Hintergrundvideo '{display_name or os.path.basename(new_video_path)}' nicht gefunden."
            )
            return False

        if self.video_capture is not None:
            self.video_capture.release()

        self.video_path = new_video_path
        self.video_capture = cv2.VideoCapture(self.video_path)

        if not self.video_capture.isOpened():
            self.add_log(
                f"Fehler beim Laden des Hintergrundvideos '{display_name or os.path.basename(new_video_path)}'."
            )
            return False

        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.add_log(
            f"Hintergrundvideo geändert: {os.path.basename(new_video_path)}"
        )
        return True

    def change_background(self, video_name):
        """Lädt weiterhin ein festes Video aus assets/videos/<name>.mp4."""
        self.bossfight_mode = False
        new_video_path = self.resource_path(
            os.path.join(
                "assets",
                "videos",
                f"{video_name}.mp4"
            )
        )
        self._load_background_video(new_video_path, video_name)

    def change_background_random(self, category):
        """
        Wählt zufällig eine MP4 aus assets/videos/<category>/.
        Bei mehreren Dateien wird dieselbe Map nicht direkt zweimal gewählt.
        """
        folder = self.resource_path(
            os.path.join("assets", "videos", category)
        )

        if not os.path.isdir(folder):
            self.add_log(
                f"Map-Ordner nicht gefunden: assets/videos/{category}"
            )
            return

        videos = sorted(
            file_name
            for file_name in os.listdir(folder)
            if file_name.lower().endswith(".mp4")
        )

        if not videos:
            self.add_log(
                f"Keine MP4-Maps in assets/videos/{category} gefunden."
            )
            return

        if not hasattr(self, "last_random_map"):
            self.last_random_map = {}

        last_video = self.last_random_map.get(category)
        choices = videos

        if len(videos) > 1 and last_video in videos:
            choices = [video for video in videos if video != last_video]

        selected_video = random.choice(choices)
        selected_path = os.path.join(folder, selected_video)

        if self._load_background_video(selected_path, selected_video):
            self.last_random_map[category] = selected_video

    def add_log(self, message):
        # Jede Meldung bekommt einen Zeitstempel. So lässt sich beim Testen
        # später nachvollziehen, was Cortana wann verstanden hat.
        timestamp = time.strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")

        # Genug Historie für längere Tests behalten.
        if len(self.log_messages) > 200:
            self.log_messages = self.log_messages[-200:]

    def cortana_log(self, text):
        # Diese Funktion wird aus dem Cortana-Thread aufgerufen.
        # Keine Tkinter-Funktion hier verwenden – nur in die Queue schreiben.
        self.log_queue.put(text)

    def process_log_queue(self):
        # Läuft ausschließlich im Tkinter-Hauptthread.
        try:
            while True:
                text = self.log_queue.get_nowait()
                if isinstance(text, tuple) and text[0] == "lore_command":
                    self.open_lore()
                    if text[1] == "start":
                        self.lore_window.execute(self.lore_window.start_recording)
                    else:
                        self.lore_window.execute(self.lore_window.stop_recording)
                    continue
                self.add_log(text)
        except queue.Empty:
            pass

        if self.winfo_exists():
            self.after(50, self.process_log_queue)

    def start_cortana(self):
        if (
            hasattr(self, "cortana_thread")
            and self.cortana_thread is not None
            and self.cortana_thread.is_alive()
        ):
            self.add_log("Cortana läuft bereits.")
            return
        
        self.cortana_stop_event = threading.Event()
        self.cortana_thread = threading.Thread(target=run_cortana,
        args=(self.cortana_stop_event, self.cortana_log, self.lore_voice_command), daemon=True)
        self.cortana_thread.start()
        self.status_text = "Status: Cortana hört zu"
        self.add_log("Cortana wurde gestartet.")

    def stop_cortana(self):
        if (
            hasattr(self, "cortana_stop_event")
            and self.cortana_stop_event is not None
        ):
            self.cortana_stop_event.set()

        self.status_text = "Status: Cortana schläft"
        self.add_log("Cortana wurde gestoppt.")

    def check_cortana_process(self):
        """
        Prüft, ob main.py noch läuft.
        Wird main.py per Sprachbefehl beendet, aktualisiert sich die GUI automatisch.
        """
        if not hasattr(self, "cortana_process"):
            return

        if self.cortana_process is None:
            return

        if self.cortana_process.poll() is None:
            self.after(
                500,
                self.check_cortana_process
            )
            return

        # Prozess ist beendet.
        self.cortana_process = None

        self.status_text = "Status: Cortana schläft"

        self.add_log(
            "Cortana wurde per Sprachbefehl beendet."
        )

    def draw_settings_button(self, overlay):
        """Zeichnet ein eigenes goldenes Zahnrad – unabhängig von Emoji-/Font-Unterstützung."""
        draw = ImageDraw.Draw(overlay)
        x, y = self.scale_position(self.settings_button_position)
        w, h = self.scale_size(self.settings_button_size)
        scale = max(0.7, min(self.get_scale_values()))
        hovered = self.hovered_control == ("settings", 0)

        cx = x + w // 2
        cy = y + h // 2
        outer_r = max(10, min(w, h) // 2 - max(2, int(3 * scale)))
        tooth_len = max(3, int(6 * scale))
        tooth_half = max(2, int(3 * scale))

        if hovered:
            glow_r = outer_r + max(4, int(6 * scale))
            draw.ellipse(
                (cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r),
                fill=(255, 176, 42, 45),
                outline=(255, 205, 100, 110),
                width=max(1, int(2 * scale))
            )

        # Dunkle runde Grundplatte mit Goldrand.
        draw.ellipse(
            (cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r),
            fill=(31, 19, 16, 235),
            outline=(224, 169, 62, 255),
            width=max(2, int(3 * scale))
        )

        # Acht Zähne.
        for i in range(8):
            angle = math.radians(i * 45)
            tx = cx + math.cos(angle) * (outer_r - 1)
            ty = cy + math.sin(angle) * (outer_r - 1)

            # Kleine tangential ausgerichtete Rechtecke reichen optisch als Zahnradzähne.
            dx = math.cos(angle)
            dy = math.sin(angle)
            px = -dy
            py = dx

            p1 = (tx + dx * tooth_len + px * tooth_half, ty + dy * tooth_len + py * tooth_half)
            p2 = (tx + dx * tooth_len - px * tooth_half, ty + dy * tooth_len - py * tooth_half)
            p3 = (tx - dx * 1 - px * tooth_half, ty - dy * 1 - py * tooth_half)
            p4 = (tx - dx * 1 + px * tooth_half, ty - dy * 1 + py * tooth_half)
            draw.polygon((p1, p2, p3, p4), fill=(211, 154, 49, 255))

        # Innenring und Nabe.
        inner_r = max(6, int(outer_r * 0.53))
        hole_r = max(3, int(outer_r * 0.23))
        draw.ellipse(
            (cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r),
            fill=(76, 48, 27, 255),
            outline=(255, 211, 115, 255),
            width=max(1, int(2 * scale))
        )
        draw.ellipse(
            (cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r),
            fill=(18, 12, 12, 255),
            outline=(188, 126, 37, 255),
            width=max(1, int(2 * scale))
        )
    def _ensure_media_settings(self):
        """Ergänzt alte settings.json automatisch um die neue Medienverwaltung."""
        defaults = {
            "backgrounds": {
                "Rätsel": {"type": "folder", "path": self.resource_path(os.path.join("assets", "videos", "ratsel"))},
                "Taverne": {"type": "folder", "path": self.resource_path(os.path.join("assets", "videos", "taverne"))},
                "Dungeon": {"type": "folder", "path": self.resource_path(os.path.join("assets", "videos", "dungeon"))},
                "Wald": {"type": "folder", "path": self.resource_path(os.path.join("assets", "videos", "wald"))},
                "Höhle": {"type": "folder", "path": self.resource_path(os.path.join("assets", "videos", "hoehle"))},
                "Bosskampf": {"type": "image", "path": self.resource_path(os.path.join("assets", "bossfight_crossed_swords.png"))},
            },
            "sounds": {
                "Rätsel": [self.resource_path("sound/Rätsel1.mp3"), self.resource_path("sound/Rätsel2.mp3")],
                "Taverne": [self.resource_path(f"sound/tavern{i}.mp3") for i in range(1, 5)],
                "Dungeon": [self.resource_path("sound/Dungeon1.mp3"), self.resource_path("sound/Dungeon2.mp3")],
                "Wald": [self.resource_path(f"sound/Wald{i}.mp3") for i in range(1, 4)],
                "Höhle": [self.resource_path(f"sound/Höhle{i}.mp3") for i in range(1, 4)],
                "Bosskampf": [self.resource_path(f"sound/bossfight{i}.mp3") for i in range(1, 5)],
            }
        }
        changed = False
        for key, value in defaults.items():
            if key not in self.settings or not isinstance(self.settings.get(key), dict):
                self.settings[key] = value
                changed = True
            else:
                for category, category_value in value.items():
                    if category not in self.settings[key]:
                        self.settings[key][category] = category_value
                        changed = True
        if changed:
            self.save_settings()

    def _managed_media_dir(self, kind, category):
        safe = "".join(c for c in category if c.isalnum() or c in ("-", "_", " ")).strip() or "Allgemein"
        folder = os.path.join(get_app_directory(), "media", kind, safe)
        os.makedirs(folder, exist_ok=True)
        return folder

    def _copy_media_file(self, source, kind, category):
        folder = self._managed_media_dir(kind, category)
        base = os.path.basename(source)
        target = os.path.join(folder, base)
        stem, ext = os.path.splitext(base)
        number = 2
        while os.path.exists(target) and os.path.abspath(target) != os.path.abspath(source):
            target = os.path.join(folder, f"{stem}_{number}{ext}")
            number += 1
        if os.path.abspath(source) != os.path.abspath(target):
            shutil.copy2(source, target)
        return target

    def open_settings_menu(self):
        win = ctk.CTkToplevel(self)
        win.title("Tormentor – Einstellungen")
        win.geometry("460x380")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text="⚙  EINSTELLUNGEN",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=TEXT_COLOR).pack(pady=(28, 22))
        ctk.CTkButton(
            win, text="🖼  Hintergrundbilder verwalten", height=54,
            fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
            command=lambda: self.open_media_manager("backgrounds")
        ).pack(fill="x", padx=42, pady=8)
        ctk.CTkButton(
            win, text="🔊  Sounds verwalten", height=54,
            fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
            command=lambda: self.open_media_manager("sounds")
        ).pack(fill="x", padx=42, pady=8)
        ctk.CTkButton(
            win, text="📖  Tormentor Lore", height=54,
            fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
            command=self.open_lore
        ).pack(fill="x", padx=42, pady=8)

    def open_lore(self):
        from lore_desktop import LoreWindow
        if not getattr(self, "lore_window", None) or not self.lore_window.winfo_exists():
            self.lore_window = LoreWindow(self)
        self.lore_window.deiconify()
        self.lore_window.lift()

    def lore_voice_command(self, action):
        self.log_queue.put(("lore_command", action))

    def open_media_manager(self, kind):
        title = "Hintergrundbilder" if kind == "backgrounds" else "Sounds"
        win = ctk.CTkToplevel(self)
        win.title(f"{title} verwalten")
        win.geometry("720x520")
        win.transient(self)

        top = ctk.CTkFrame(win, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(top, text=f"{title} verwalten",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(
            top, text="+ Neue Kategorie", width=145,
            command=lambda: self._add_media_category(kind, win)
        ).pack(side="right")

        body = ctk.CTkScrollableFrame(win)
        body.pack(fill="both", expand=True, padx=18, pady=(4, 18))
        self._populate_media_manager(body, kind, win)

    def _populate_media_manager(self, body, kind, manager_window):
        for child in body.winfo_children():
            child.destroy()

        data = self.settings.get(kind, {})
        for category in sorted(data.keys()):
            row = ctk.CTkFrame(body)
            row.pack(fill="x", padx=4, pady=5)

            value = data[category]
            if kind == "sounds":
                count = len(value) if isinstance(value, list) else 0
                detail = f"{count} Sound{'s' if count != 1 else ''}"
            else:
                if isinstance(value, dict):
                    path = value.get("path", "")
                    if value.get("type") == "folder" and os.path.isdir(path):
                        count = len([f for f in os.listdir(path) if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".png", ".jpg", ".jpeg", ".webp"))])
                        detail = f"{count} Hintergrunddatei{'en' if count != 1 else ''}"
                    else:
                        detail = os.path.basename(path) or "Keine Datei"
                else:
                    detail = "Keine Datei"

            ctk.CTkLabel(row, text=category, width=150, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(12, 4), pady=12)
            ctk.CTkLabel(row, text=detail, anchor="w").pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkButton(
                row, text="Verwalten", width=100,
                command=lambda c=category: self.open_category_manager(kind, c, manager_window)
            ).pack(side="right", padx=(4, 10))
            ctk.CTkButton(
                row, text="✕", width=38, fg_color="#4A1414", hover_color="#711D1D",
                command=lambda c=category: self._delete_media_category(kind, c, body, manager_window)
            ).pack(side="right", padx=2)

    def _add_media_category(self, kind, manager_window):
        name = simpledialog.askstring("Neue Kategorie", "Name der neuen Kategorie:", parent=manager_window)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        data = self.settings.setdefault(kind, {})
        if name in data:
            messagebox.showinfo("Tormentor", "Diese Kategorie existiert bereits.", parent=manager_window)
            return
        data[name] = [] if kind == "sounds" else {"type": "folder", "path": self._managed_media_dir("backgrounds", name)}
        self.save_settings()
        manager_window.destroy()
        self.open_media_manager(kind)

    def _delete_media_category(self, kind, category, body, manager_window):
        if not messagebox.askyesno("Kategorie löschen",
                                   f"'{category}' aus Tormentor entfernen?\nDie Originaldateien werden nicht gelöscht.",
                                   parent=manager_window):
            return
        self.settings.get(kind, {}).pop(category, None)
        self.save_settings()
        self._populate_media_manager(body, kind, manager_window)

    def open_category_manager(self, kind, category, parent_window=None):
        win = ctk.CTkToplevel(self)
        win.title(f"{category} – {'Hintergründe' if kind == 'backgrounds' else 'Sounds'}")
        win.geometry("760x540")
        win.transient(self)

        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(header, text=category,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(
            header, text="Umbenennen", width=110,
            command=lambda: self._rename_category(kind, category, win, parent_window)
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            header, text="+ Datei hinzufügen", width=145,
            command=lambda: self._add_media_file(kind, category, list_frame, win)
        ).pack(side="right", padx=4)

        list_frame = ctk.CTkScrollableFrame(win)
        list_frame.pack(fill="both", expand=True, padx=18, pady=(4, 18))
        self._populate_category_files(list_frame, kind, category, win)

    def _category_files(self, kind, category):
        if kind == "sounds":
            value = self.settings.get(kind, {}).get(category, [])
            return list(value) if isinstance(value, list) else []

        value = self.settings.get(kind, {}).get(category, {})
        if not isinstance(value, dict):
            return []
        path = value.get("path", "")
        if value.get("type") == "folder":
            if not os.path.isdir(path):
                return []
            allowed = (".mp4", ".avi", ".mov", ".mkv", ".png", ".jpg", ".jpeg", ".webp")
            return [os.path.join(path, f) for f in sorted(os.listdir(path)) if f.lower().endswith(allowed)]
        return [path] if path else []

    def _populate_category_files(self, frame, kind, category, win):
        for child in frame.winfo_children():
            child.destroy()
        files = self._category_files(kind, category)

        if not files:
            ctk.CTkLabel(frame, text="Noch keine Dateien vorhanden.").pack(pady=30)
            return

        for path in files:
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", padx=4, pady=4)
            ctk.CTkLabel(row, text=os.path.basename(path), anchor="w").pack(
                side="left", fill="x", expand=True, padx=12, pady=11)

            if kind == "sounds":
                ctk.CTkButton(
                    row, text="▶ Anhören", width=86,
                    command=lambda p=path: self._preview_sound(p)
                ).pack(side="right", padx=3)
                ctk.CTkButton(
                    row, text="⏹ Stop", width=70,
                    command=self._stop_preview_sound
                ).pack(side="right", padx=3)
            else:
                ctk.CTkButton(
                    row, text="👁 Vorschau", width=95,
                    command=lambda p=path: self._preview_background(p, win)
                ).pack(side="right", padx=3)

            ctk.CTkButton(
                row, text="Entfernen", width=90, fg_color="#4A1414", hover_color="#711D1D",
                command=lambda p=path: self._remove_media_file(kind, category, p, frame, win)
            ).pack(side="right", padx=(3, 8))
    def _add_media_file(self, kind, category, frame, win):
        if kind == "sounds":
            types = [("Audio", "*.mp3 *.wav *.ogg"), ("Alle Dateien", "*.*")]
            selected = filedialog.askopenfilenames(parent=win, title="Sounds auswählen", filetypes=types)
            if not selected:
                return
            target_list = self.settings.setdefault("sounds", {}).setdefault(category, [])
            for source in selected:
                copied = self._copy_media_file(source, "sounds", category)
                if copied not in target_list:
                    target_list.append(copied)
        else:
            types = [("Hintergrund", "*.mp4 *.avi *.mov *.mkv *.png *.jpg *.jpeg *.webp"), ("Alle Dateien", "*.*")]
            selected = filedialog.askopenfilenames(parent=win, title="Hintergründe auswählen", filetypes=types)
            if not selected:
                return
            value = self.settings.setdefault("backgrounds", {}).setdefault(
                category, {"type": "folder", "path": self._managed_media_dir("backgrounds", category)}
            )
            # Eigene Hintergründe werden in einen verwalteten Ordner kopiert.
            folder = value.get("path") if value.get("type") == "folder" else self._managed_media_dir("backgrounds", category)
            if not os.path.isdir(folder) or not os.access(folder, os.W_OK):
                folder = self._managed_media_dir("backgrounds", category)
            os.makedirs(folder, exist_ok=True)
            value["type"] = "folder"
            value["path"] = folder
            for source in selected:
                base = os.path.basename(source)
                target = os.path.join(folder, base)
                stem, ext = os.path.splitext(base)
                n = 2
                while os.path.exists(target):
                    target = os.path.join(folder, f"{stem}_{n}{ext}")
                    n += 1
                shutil.copy2(source, target)

        self.save_settings()
        self._populate_category_files(frame, kind, category, win)
        self.add_log(f"{category}: Medienverwaltung aktualisiert.")

    def _remove_media_file(self, kind, category, path, frame, win):
        if not messagebox.askyesno("Entfernen", f"{os.path.basename(path)} aus der Auswahl entfernen?",
                                   parent=win):
            return
        if kind == "sounds":
            values = self.settings.get("sounds", {}).get(category, [])
            self.settings["sounds"][category] = [p for p in values if p != path]
        else:
            value = self.settings.get("backgrounds", {}).get(category, {})
            # Nur Dateien im Tormentor-Benutzerordner physisch löschen.
            app_dir = os.path.abspath(get_app_directory())
            abs_path = os.path.abspath(path)
            if abs_path.startswith(app_dir + os.sep) and os.path.isfile(abs_path):
                try:
                    os.remove(abs_path)
                except OSError:
                    pass
            elif value.get("type") == "image" and value.get("path") == path:
                value["path"] = ""
        self.save_settings()
        self._populate_category_files(frame, kind, category, win)

    def _rename_category(self, kind, old_name, win, parent_window):
        new_name = simpledialog.askstring("Umbenennen", "Neuer Name:", initialvalue=old_name, parent=win)
        if not new_name:
            return
        new_name = new_name.strip()
        data = self.settings.get(kind, {})
        if not new_name or new_name == old_name:
            return
        if new_name in data:
            messagebox.showinfo("Tormentor", "Dieser Name existiert bereits.", parent=win)
            return
        data[new_name] = data.pop(old_name)
        self.save_settings()
        win.destroy()
        if parent_window is not None and parent_window.winfo_exists():
            parent_window.destroy()
        self.open_media_manager(kind)

    def _stop_preview_sound(self):
        pygame.mixer.music.stop()
        self.add_log("Sound-Vorschau gestoppt.")

    def _preview_background(self, path, parent):
        """Zeigt Bilder groß an; bei Videos wird ein Vorschaubild aus dem Video erzeugt."""
        if not os.path.exists(path):
            messagebox.showerror("Vorschau", "Datei wurde nicht gefunden.", parent=parent)
            return

        preview = ctk.CTkToplevel(self)
        preview.title(f"Vorschau – {os.path.basename(path)}")
        preview.geometry("820x560")
        preview.transient(parent)

        image_label = tk.Label(preview, bg="#090706", borderwidth=0, highlightthickness=0)
        image_label.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        info = ctk.CTkLabel(preview, text=os.path.basename(path), text_color=TEXT_COLOR)
        info.pack(pady=(0, 10))

        ext = os.path.splitext(path)[1].lower()

        def show_pil(pil_image):
            preview.update_idletasks()
            max_w = max(300, preview.winfo_width() - 40)
            max_h = max(250, preview.winfo_height() - 85)
            source = pil_image.convert("RGB")
            scale = min(max_w / source.width, max_h / source.height)
            new_size = (
                max(1, int(source.width * scale)),
                max(1, int(source.height * scale))
            )
            rendered = source.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(rendered)
            image_label.configure(image=photo)
            image_label.image = photo

        try:
            if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                show_pil(Image.open(path))
            elif ext in (".mp4", ".avi", ".mov", ".mkv"):
                cap = cv2.VideoCapture(path)
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total > 1:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total // 3))
                ok, frame = cap.read()
                cap.release()
                if not ok:
                    raise OSError("Kein Videobild lesbar")
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                show_pil(Image.fromarray(frame))
                info.configure(text=f"{os.path.basename(path)}  •  Video-Vorschaubild")
            else:
                info.configure(text="Für dieses Dateiformat ist keine Vorschau verfügbar.")
        except Exception as exc:
            info.configure(text=f"Vorschau konnte nicht geladen werden: {exc}")

    def _preview_sound(self, path):
        if not os.path.exists(path):
            self.add_log(f"Sound nicht gefunden: {os.path.basename(path)}")
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            self.add_log(f"Sound-Test: {os.path.basename(path)}")
        except pygame.error as exc:
            self.add_log(f"Sound konnte nicht abgespielt werden: {exc}")

    def _play_managed_sound(self, category, last_attr):
        sounds = [p for p in self.settings.get("sounds", {}).get(category, []) if os.path.exists(p)]
        if not sounds:
            self.add_log(f"Keine Sounds für '{category}' vorhanden.")
            return
        last = getattr(self, last_attr, None)
        choices = [p for p in sounds if p != last] if len(sounds) > 1 else sounds
        sound = random.choice(choices)
        setattr(self, last_attr, sound)
        pygame.mixer.music.load(sound)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()
        self.add_log(f"{category}-Sound: {os.path.basename(sound)}")

    def _play_managed_background(self, category):
        value = self.settings.get("backgrounds", {}).get(category, {})
        if not isinstance(value, dict):
            return False
        path = value.get("path", "")
        if value.get("type") == "image" and path and os.path.exists(path):
            if category == "Bosskampf":
                try:
                    self.bossfight_background_pil = Image.open(path).convert("RGBA")
                    self._boss_cache_size = None
                    self.bossfight_mode = True
                    self.bossfight_started_at = time.time()
                    return True
                except OSError:
                    return False
        if value.get("type") == "folder" and os.path.isdir(path):
            videos = [os.path.join(path, f) for f in os.listdir(path)
                      if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))]
            if videos:
                if not hasattr(self, "last_managed_background"):
                    self.last_managed_background = {}
                last = self.last_managed_background.get(category)
                choices = [p for p in videos if p != last] if len(videos) > 1 else videos
                selected = random.choice(choices)
                if self._load_background_video(selected, os.path.basename(selected)):
                    self.bossfight_mode = False
                    self.last_managed_background[category] = selected
                    return True
        return False

    def load_settings(self):
        settings_path = get_settings_path()

        # Vorhandene Projekt-settings.json einmalig in den gemeinsamen
        # Tormentor-Ordner übernehmen.
        legacy_settings_path = self.resource_path("settings.json")
        if (
            not os.path.exists(settings_path)
            and os.path.exists(legacy_settings_path)
        ):
            try:
                with open(
                    legacy_settings_path,
                    "r",
                    encoding="utf-8"
                ) as source_file:
                    legacy_settings = json.load(source_file)

                with open(
                    settings_path,
                    "w",
                    encoding="utf-8"
                ) as target_file:
                    json.dump(
                        legacy_settings,
                        target_file,
                        indent=4,
                        ensure_ascii=False
                    )
            except (OSError, json.JSONDecodeError):
                pass

        default_settings = {
            "theme": "dungeon2",
            "volume": "0.70",
            "music_volume": "0.70",
            "voice_volume": "1.00",
            "wakeword": "Cortana",
            "background": "background.mp4"
        }
        try:
            with open(settings_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(settings_path, "w",
                      encoding="utf-8") as file:
                json.dump(default_settings,
                          file,
                          indent=4,
                          ensure_ascii=False)
                return default_settings
            
    def save_settings(self):
        settings_path = get_settings_path()
        with open(settings_path, "w",
                      encoding="utf-8") as file:
            json.dump(
                self.settings,
                file,
                indent=4,
                ensure_ascii=False
            )

    def change_volume(self, value):
        global volume
        volume = float(value)

        self.settings["volume"] = volume
        self.settings["music_volume"] = volume
        self.settings["voice_volume"] = volume
        self.save_settings()

        pygame.mixer.music.set_volume(volume)
        percent = int(volume * 100)
        self.add_log(
            f"Lautstärke: {percent} %"
        )

    def play_tavern(self):
        if not self._play_managed_background("Taverne"):
            self.change_background_random("taverne")
        self._play_managed_sound("Taverne", "last_tavern_sound")
    def play_riddle(self):
        if not self._play_managed_background("Rätsel"):
            self.change_background_random("ratsel")
        self._play_managed_sound("Rätsel", "last_riddle_sound")
    def play_dungeon(self):
        if not self._play_managed_background("Dungeon"):
            self.change_background_random("dungeon")
        self._play_managed_sound("Dungeon", "last_dungeon_sound")
    def play_forest(self):
        if not self._play_managed_background("Wald"):
            self.change_background_random("wald")
        self._play_managed_sound("Wald", "last_forest_sound")
    def play_cave(self):
        if not self._play_managed_background("Höhle"):
            self.change_background_random("hoehle")
        self._play_managed_sound("Höhle", "last_cave_sound")
    def play_bossfight(self):
        if not self._play_managed_background("Bosskampf"):
            if self.bossfight_background_pil is not None:
                self.bossfight_mode = True
                self.bossfight_started_at = time.time()
            else:
                self.change_background_random("bosskampf")
        self._play_managed_sound("Bosskampf", "last_bossfight_sound")
    def stop_music(self):
        pygame.mixer.music.stop()
        self.change_background("background")
        self.add_log("Musik wurde gestoppt.")

def show_intro():
        intro = tk.Tk()
        intro.overrideredirect(True)
        intro.attributes("-topmost", True)

        screen_width = intro.winfo_screenwidth()
        screen_height = intro.winfo_screenheight()
        intro.geometry(f"{screen_width}x{screen_height}+0+0")
        label = tk.Label(
            intro,
            bg="black",
            borderwidth=0)
        label.pack(fill="both", expand=True)
        video_path = resource_path("assets/intro.mp4")
        cap = cv2.VideoCapture(video_path)

        intro_sound = resource_path("sound/Dungeon2.mp3")
        pygame.mixer.music.stop()
        pygame.mixer.music.load(intro_sound)
        pygame.mixer.music.set_volume(0.7)
        pygame.mixer.music.play(-1)

        def close_intro(event=None):
            pygame.mixer.music.stop()
            if cap.isOpened():
                cap.release()
            intro.destroy()

        def play_frame():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if not ret:
                return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (screen_width, screen_height), interpolation=cv2.INTER_LANCZOS4)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image)
            label.configure(image=photo)
            label.image = photo
            intro.after(42, play_frame)

        intro.bind("<Escape>", close_intro)
        intro.bind("<Button-1>", close_intro)

        play_frame()
        intro.mainloop()

if __name__ == "__main__":
    show_intro()
    app = TormentorApp()
    app.mainloop()
