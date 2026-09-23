"""Desktop Lore editor: ordinary text fields, shared audio input and DM publication."""
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog

import lore
import lore_workflow


class LoreWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Tormentor Lore · DM-Prüfung")
        self.geometry("850x780")
        self.minsize(650, 580)
        self.session = None
        self.recorder = None
        self.recording_lock = None
        self.worker = None
        self.status = ctk.CTkLabel(self, text="Sitzung aufnehmen, importieren oder vom Android-Gerät übertragen")
        self.status.pack(pady=8)
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=18)
        self.chooser = ctk.CTkOptionMenu(row, values=["Keine Sitzungen"], command=self.select_session)
        self.chooser.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        ctk.CTkButton(row, text="Neu laden", width=100, command=lambda: self.execute(self.reload)).pack(side="right", padx=6)
        self.title_field = ctk.CTkEntry(self, placeholder_text="Sitzungstitel, zum Beispiel Session 4")
        self.title_field.pack(fill="x", padx=18, pady=8)
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=18)
        actions.grid_columnconfigure((0, 1, 2), weight=1)
        self.record_button = ctk.CTkButton(actions, text="● Aufnahme starten", command=lambda: self.execute(self.toggle_recording))
        self.record_button.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        for index, (label, command) in enumerate((("Neue Sitzung", self.create), ("Audio importieren", self.import_audio), ("Aufnahme auswerten", lambda: self.process(True)), ("Transkript auswerten", lambda: self.process(False)), ("Transkript speichern", self.save_transcript)), 1):
            ctk.CTkButton(actions, text=label, command=lambda fn=command: self.execute(fn)).grid(row=index // 3, column=index % 3, sticky="ew", padx=4, pady=4)
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=18, pady=8)
        review = tabs.add("DM-Prüfung")
        transcript = tabs.add("Privates Transkript")
        self.transcript = ctk.CTkTextbox(transcript)
        self.transcript.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(review)
        scroll.pack(fill="both", expand=True)
        self.fields = {}
        for key, label, height in (("summary", "Zusammenfassung für Spieler", 130), ("npcs", "NPCs · ein Eintrag pro Zeile", 80), ("places", "Orte · ein Eintrag pro Zeile", 80), ("quests", "Quests · ein Eintrag pro Zeile", 80), ("level_ups", "Levelvorschläge · pro Zeile Name | Stufe, etwa Arin | 3", 75)):
            ctk.CTkLabel(scroll, text=label, anchor="w").pack(fill="x", padx=5, pady=(10, 2))
            field = ctk.CTkTextbox(scroll, height=height)
            field.pack(fill="x", padx=5)
            self.fields[key] = field
        self.publish = ctk.CTkCheckBox(self, text="Geprüfte Inhalte für Spieler freigeben")
        self.publish.pack(pady=6)
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkButton(bottom, text="KI-Entwurf laden", command=lambda: self.execute(self.load_draft)).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(bottom, text="DM-Prüfung speichern", command=lambda: self.execute(self.save_review)).pack(side="right", padx=6, pady=6)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Destroy>", self.on_destroy, add="+")
        self.reload()
        self.after(500, self.poll)

    def execute(self, action):
        try:
            action()
        except Exception as error:
            messagebox.showerror("Tormentor Lore", str(error), parent=self)

    def ensure_idle(self):
        if self.recorder or self.worker and self.worker.is_alive():
            raise ValueError("Bitte zuerst die Aufnahme beenden oder die Auswertung abwarten.")

    def reload(self):
        self.ensure_idle()
        self.items = {item["title"] + " · " + item["id"][:8]: item for item in lore.list_sessions()}
        self.chooser.configure(values=list(self.items) or ["Keine Sitzungen"])
        if self.session:
            self.show(lore.load(self.session["id"]))

    def select_session(self, label):
        self.execute(lambda: (self.ensure_idle(), self.show(lore.load(self.items[label]["id"]))))

    def show(self, item):
        self.session = item
        self.revision = json.dumps(item, sort_keys=True, ensure_ascii=False)
        self.title_field.delete(0, "end")
        self.title_field.insert(0, item["title"])
        self.chooser.set(item["title"] + " · " + item["id"][:8])
        self.transcript.delete("1.0", "end")
        self.transcript.insert("1.0", item.get("transcript", ""))
        edited = item.get("approved", {}) if item.get("reviewed_at") or item.get("published") else item.get("draft", {})
        self.show_review(edited)
        if item.get("published"):
            self.publish.select()
        else:
            self.publish.deselect()
        self.status.configure(text=item.get("processing", {}).get("message", "Sitzung geladen · nur geprüfte Inhalte freigeben"))

    def show_review(self, edited):
        for key, value in lore.review_fields(edited).items():
            self.fields[key].delete("1.0", "end")
            self.fields[key].insert("1.0", value)

    def create(self):
        self.ensure_idle()
        title = self.title_field.get().strip()
        if not title:
            title = simpledialog.askstring("Neue Sitzung", "Sitzungstitel, zum Beispiel Session 4:", parent=self)
        if title and title.strip():
            self.show(lore.new_session(title))
            self.reload()

    def load_draft(self):
        self.ensure_idle()
        if self.session:
            self.show_review(self.session.get("draft", {}))

    def current(self):
        item = lore.load(self.session["id"])
        if json.dumps(item, sort_keys=True, ensure_ascii=False) != self.revision:
            raise ValueError("Die Sitzung wurde an anderer Stelle geändert. Bitte zuerst Neu laden wählen.")
        return item

    def import_audio(self):
        self.ensure_idle()
        if not self.session:
            self.create()
        if not self.session:
            return
        filename = filedialog.askopenfilename(parent=self, filetypes=[("Audio", "*.wav *.mp3 *.m4a *.ogg *.flac *.aac *.mp4 *.audio")])
        if filename:
            with lore_workflow.session_lock(self.session["id"]):
                item = self.current()
                lore.import_audio(item, filename)
                self.show(item)
            self.status.configure(text="Aufnahme importiert · bereit zur Auswertung")

    def toggle_recording(self):
        if self.recorder:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.ensure_idle()
        title = simpledialog.askstring("Neue Aufnahme", "Sitzungstitel, zum Beispiel Session 4:", initialvalue=self.title_field.get().strip(), parent=self)
        if not title or not title.strip():
            return
        self.show(lore.new_session(title))
        self.reload()
        lock = lore_workflow.session_lock(self.session["id"])
        lock.__enter__()
        try:
            self.recorder = lore.Recorder(self.session)
            self.recording_lock = lock
        except Exception:
            lock.__exit__(None, None, None)
            raise
        self.record_button.configure(text="■ Aufnahme beenden")
        self.chooser.configure(state="disabled")
        self.status.configure(text="● Aufnahme läuft: " + self.session["title"])

    def stop_recording(self, update_ui=True):
        if not self.recorder:
            return
        current = self.recorder
        self.recorder = None
        try:
            current.stop()
        finally:
            self.recording_lock.__exit__(None, None, None)
            self.recording_lock = None
            if update_ui:
                self.record_button.configure(text="● Aufnahme starten")
                self.chooser.configure(state="normal")
                self.show(lore.load(current.session["id"]))
                self.status.configure(text="Aufnahme gespeichert: " + current.session["title"])

    def save_transcript(self):
        self.ensure_idle()
        if not self.session:
            raise ValueError("Bitte zuerst eine Sitzung anlegen.")
        with lore_workflow.session_lock(self.session["id"]):
            item = self.current()
            item["transcript"] = self.transcript.get("1.0", "end").strip()
            lore.save(item)
            self.session = item
            self.revision = json.dumps(item, sort_keys=True, ensure_ascii=False)
        self.status.configure(text="Privates Transkript gespeichert")

    def save_review(self):
        self.ensure_idle()
        if not self.session:
            raise ValueError("Bitte zuerst eine Sitzung anlegen.")
        edited = lore.review_from_fields({key: field.get("1.0", "end").strip() for key, field in self.fields.items()})
        title = self.title_field.get().strip()
        if not title:
            raise ValueError("Bitte einen Sitzungstitel eingeben.")
        with lore_workflow.session_lock(self.session["id"]):
            item = self.current()
            item["title"] = title[:200]
            lore.approve(item, edited, bool(self.publish.get()))
            self.show(item)
        self.status.configure(text="Prüfung gespeichert · " + ("für Spieler freigegeben" if item["published"] else "nur DM"))

    def process(self, transcribe):
        self.ensure_idle()
        if not self.session:
            raise ValueError("Bitte zuerst eine Sitzung auswählen.")
        if not transcribe:
            self.save_transcript()
        self.worker = lore_workflow.start_processing(self.session["id"], transcribe)
        self.chooser.configure(state="disabled")
        for field in [self.transcript, self.title_field, *self.fields.values()]:
            field.configure(state="disabled")

    def poll(self):
        if self.worker:
            current = lore.load(self.session["id"])
            self.status.configure(text=current.get("processing", {}).get("message", "Auswertung läuft …"))
            if not self.worker.is_alive():
                self.worker = None
                self.chooser.configure(state="normal")
                for field in [self.transcript, self.title_field, *self.fields.values()]:
                    field.configure(state="normal")
                self.show(current)
                self.show_review(current.get("draft", {}))
        self.after(500, self.poll)

    def close(self):
        try:
            self.stop_recording(False)
        except Exception as error:
            messagebox.showerror("Aufnahme", str(error), parent=self)
        self.destroy()

    def on_destroy(self, event):
        if event.widget is self and self.recorder:
            self.stop_recording(False)
