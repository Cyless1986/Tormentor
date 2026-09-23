# Tormentor für Galaxy Tab A (2016), Android 8.1.0

Die Android-App ist eine eigenständige Umsetzung der Laptop-Version. Alle neuen Dateien liegen in diesem Ordner. Die ursprünglichen Python-Dateien, Sounds und Assets werden nicht verändert. Die kopierten Desktop-Quellen liegen in `desktop_reference`.

## Update 1.1

Cortana ist blau, Würfeln grün und Frage Tormentor violett. Die APK als Update installieren, ohne Tormentor vorher zu deinstallieren. Danach unter **Medien verwalten → Laptop-Medienpaket importieren (.zip)** die Datei **Tablet-Videos.zip** (rund 56 MB) auswählen. Das Paket ersetzt in den jeweiligen Kategorien alle gleichnamigen Videos; andere Videos, Sounds, Bilder und Sprachnamen bleiben erhalten. Ein erneuter Reparaturimport erzeugt keine Videoduplikate. Bei einem Speicherfehler vor dem Speichern bleibt der vorherige Index erhalten.

Alle 15 Paketvideos sowie das Intro wurden als stumme H.264-Baseline-Videos, Level 3.1, bis 1280 × 720 Pixel und 30 Bilder/s erzeugt. Sämtliche Frames wurden am Laptop decodiert; die Wiedergabe auf dem Tablet muss nach dem Update geprüft werden. Die Laptop-Originale bleiben unverändert. Das vollständige Medienpaket enthält ebenfalls diese kompatiblen Kopien.

## Installation

1. `Tormentor-Android.apk` auf das Tablet kopieren, zum Beispiel per USB in „Download“.
2. Auf dem Tablet die APK unter „Eigene Dateien“ antippen. Falls Android fragt, die Installation aus dieser Quelle erlauben, dann installieren.
3. Tormentor öffnen. Das übernommene Intro läuft mit dem ursprünglichen Dungeon2-Sound. Mit „Abenteuer starten“ überspringen.
4. Optional auch `Medienpaket.zip` auf das Tablet kopieren. In der App **Medien verwalten → Laptop-Medienpaket importieren (.zip)** wählen. Das Paket enthält 35 vorhandene Medien in sechs Kategorien und ist rund 1,17 GB groß. Für Paket und importierte Kopien zusammen etwa 2,5 GB freien Speicher vorsehen. Nach erfolgreichem Import kann die ZIP auf dem Tablet gelöscht werden.

Die APK ist ein signierter persönlicher Testbuild, kein Play-Store-Release. Android 8.1 ist die Mindestversion. ARM mit 32 und 64 Bit wird unterstützt. Installation, Darstellung, Videocodecs und Mikrofonverhalten müssen auf dem tatsächlichen Tablet getestet werden.

## Sounds und Hintergründe verwalten

- **Medien verwalten → Kategorie → Sounds hinzufügen** bzw. **Bilder / MP4 hinzufügen**. Mehrfachauswahl ist möglich. Die Dateien werden in den privaten App-Speicher kopiert und bleiben nach einem Neustart verfügbar.
- Eine Datei antippen, um sie vorzuhören/anzusehen oder aus der App zu löschen. Originale auf dem Tablet bzw. Laptop bleiben erhalten.
- Kategorien können angelegt, umbenannt und gelöscht werden. Jede Kategorie ordnet ihre Sounds und Hintergründe gemeinsam einer Szene zu.
- Pro Szene wird ein zufälliger Sound und ein zufälliger Hintergrund gewählt; bei mehreren Dateien wird die letzte Auswahl vermieden. Sound-Schleife ist abschaltbar. MP4-Hintergründe laufen stumm in Schleife.
- Für dieses ältere Tablet empfehlen sich MP3, JPG/PNG und H.264-MP4 bis 1080p. Die Endung MP4 allein garantiert keinen unterstützten Videocodec.
- Beim Deinstallieren bzw. Löschen der App-Daten werden die App-Kopien entfernt. Originaldateien und das Laptop-Medienpaket als Sicherung behalten. Erneuter ZIP-Import fügt weitere Kopien hinzu.

## Freihändig mit Cortana

**Cortana einschalten** einmal antippen und das Mikrofon freigeben. Das mitgelieferte deutsche Vosk-Modell erkennt danach lokal ohne Internet, solange Tormentor geöffnet ist. Der Bildschirm bleibt währenddessen an.

- „Cortana, spiele Taverne“
- „Cortana, spiele Wald“ / „Höhle“ / „Rätsel“ / „Bosskampf“
- „Cortana, spiele Verlies“ für Dungeon; zusätzlich ist eine lautliche Zuordnung für „Dungeon“ enthalten.
- „Cortana, Stopp“
- Oder zunächst „Cortana“ sagen, die vorhandene Antwort „Ja, Dungeonmaster?“ abwarten und innerhalb von zehn Sekunden den Befehl sprechen.

Der Befehlsfilter akzeptiert Cortana, Cotana, Contana, Kortana und Katana. Das kleine deutsche Modell enthält das Wort Cortana selbst nicht: Die Offline-Erkennung verwendet **Katana als lautliche Näherung** innerhalb eines begrenzten Befehlswortschatzes. Synthetische deutsche Sprachbeispiele werden im Ordner `verification` geprüft; das ersetzt keinen Test mit deiner Stimme, dem Tablet-Mikrofon und laufender Musik.

Unter **Medien verwalten → Kategorie → Sprachname** kann ein einfaches deutsches Wort für schwer erkennbare Namen hinterlegt werden. Namen außerhalb des Modellwortschatzes können weiter Schwierigkeiten machen. Kategorie und Bild-/Soundzuordnung bleiben dabei erhalten.

Musik und die übernommene Cortana-Antwort laufen über separate Audioplayer mit eigenen Lautstärken. Während der Antwort wird Musik auf 25 Prozent ihrer eingestellten Lautstärke abgesenkt und die Erkennung pausiert; danach wird beides wiederhergestellt. Die physische Schallübertragung vom Lautsprecher zum Mikrofon bleibt bestehen. Für zuverlässige Erkennung Musik moderat einstellen bzw. einen externen Lautsprecher mit Abstand zum Tablet nutzen.

Beim Wechsel in eine andere App oder beim Sperren stoppen Wiedergabe und Mikrofon. Bei der Rückkehr wird ein zuvor aktivierter Zuhörmodus wieder gestartet. Mit „Cortana ausschalten“ wird das Mikrofon freigegeben. Die zusätzliche Taste **Sprachbefehl einmal** verwendet den installierten Android-Sprachdienst, der je nach Einstellung eine Internetverbindung benötigt.

## Umfang

Enthalten: Intro, Szenen, Medienverwaltung mit eigenen Kopien, Bilder und MP4, Sounds, getrennte Musik-/Stimmenlautstärke, Offline-Wakeword, manuelle Würfel und Import der Laptop-Mediensammlung.

Zusätzlich vorbereitet: freie Fragen über die lokale KI auf dem Laptop und gesprochene Antworten mit der neuronalen Männerstimme Thorsten, auch in einer dunkleren Variante. Einrichtung siehe `local_ai/README.md`. Dafür müssen Laptop und Tablet im gleichen privaten WLAN sein. Nach „Cortana, frage Tormentor“ wird die Frage mit dem mitgelieferten Vosk-Modell offline erkannt. Alternativ kann die Frage eingetippt werden. Nur die zusätzliche Taste „Sprachbefehl einmal“ verwendet den Android-Sprachdienst.

Noch nicht enthalten: OpenAI- und ElevenLabs-Anbindung sowie vollständige Übernahme aller Desktop-Animationen. Die vorhandene Cortana-Aktivierungsantwort ist als Audiodatei übernommen. Keine API-Schlüssel oder `.env`-Dateien werden in die APK kopiert.

## Erneut bauen

In PowerShell aus dem Projektordner: `./build.ps1`. Das Skript verwendet Java, Gradle und SDK unter `tools`, baut die APK und führt Unit-Tests sowie Android Lint aus. Ergebnis: `Tormentor-Android.apk`. Beim ersten Build werden Bibliotheken aus Google Maven und Maven Central benötigt.

`prepare_tablet_videos.py` erzeugt die kompatiblen Videokopien, das Reparaturpaket und das vollständige Importpaket. Es verwendet das lokale FFmpeg unter `tools/video-python`. `export_media.py` erzeugt dagegen ein unverändertes Original-Importpaket aus der gespeicherten Desktop-Medienliste unter `%LOCALAPPDATA%/Tormentor/settings.json`, mit den Standardkategorien als Rückfall. Es liest die Originaldateien ausschließlich. Fehlende Dateien erscheinen in `Medienpaket.json`.

Abhängigkeiten: Vosk Android 0.3.75, deutsches Modell `vosk-model-small-de-0.15` von Alpha Cephei (Apache 2.0), JNA 5.18.1 (Apache 2.0 / LGPL). Offizielle Quellen: https://alphacephei.com/vosk/android und https://alphacephei.com/vosk/models. Lizenztexte liegen unter `app/src/main/assets/licenses`.




## Update 1.2

Das Originalintro stammt wieder aus assets/Intro.mp4. Der separate animierte Startbildschirm stammt aus assets/background.mp4 und erscheint nach dem Intro sowie nach Alles stoppen. Ein eingebautes Standbild dient als Ladehintergrund. Für dieses Update nur die APK installieren; das Videopaket muss nicht erneut importiert werden.


## Update 1.3

Das App-Symbol verwendet jetzt das vorhandene TC-Logo aus assets/Tormentor.ico in fünf Android-Auflösungen. Nur die APK aktualisieren.


## Update 1.4

Der Hauptbildschirm füllt das Hintergrundfeld proportional bis an die Bedienelemente aus; überstehende Ränder werden mittig beschnitten. Intro und Szenenkarten behalten ihre vollständige Darstellung. Die Hilfe beschreibt jetzt die integrierte lokale KI mit Thorsten-Sprachausgabe. Nur die APK aktualisieren.


## Update 1.5

Nach Cortanas Aktivierungsantwort und der kurzen Mikrofonpause zeigt die App: Jetzt deine Frage sprechen. Erst dann startet das 60-Sekunden-Fenster. Frage ohne erneutes Aktivierungswort sprechen und danach kurz schweigen. Für eine weitere Frage erneut Cortana, frage Tormentor sagen. Die dunkle KI-Stimme allein bedeutet nicht, dass die App gerade eine Folgefrage aufnimmt. Nur APK aktualisieren.


## Update 1.6

Freigegebenes Steinplatten-Layout: Wald/Dungeon, Bosskampf/Höhle und Taverne/Rätsel im Rahmen, Alles stoppen mittig darunter. Zusätzliche Kategorien erscheinen im gleichen scrollbaren Feld. Cortana, Sprache, KI-Fragen, Hilfe, Würfeln und Verwaltung stehen links. Beim Szenenstart wird das Menü ausgeblendet; Szenen / Stopp links blendet es erneut ein. Musik und Stimme liegen gemeinsam in der unteren Leiste. Nur die APK aktualisieren.


## Update 2.3 · Smartphone und Tablet

Das Intro füllt Hoch- und Querformat proportional aus; überstehende Bildränder werden mittig beschnitten. Der Startknopf liegt über dem Video. Auf schmalen Displays ersetzt **Funktionen** die feste Seitenleiste. Szenen nutzen die verfügbare Breite; bei sehr schmalen Displays oder großer Schrift erscheinen sie untereinander. Musik und Stimme stehen im Hochformat in eigenen Zeilen. Beim Drehen wird die Oberfläche neu angeordnet; laufende Szenenwiedergabe wird dabei beendet. Das Intro startet nach dem Drehen erneut.

Als Update installieren, ohne vorherige Deinstallation. APK-Version 2.3, Versionscode 11. Build, Unit-Tests und Android Lint geprüft; Der Nutzer hat die Funktion auf dem Poco X4 Pro 5G bestätigt; die Smartphone-Darstellung ist für ihn ausreichend. Persönliche Einstellungen und importierte Medien bleiben im App-Speicher.
