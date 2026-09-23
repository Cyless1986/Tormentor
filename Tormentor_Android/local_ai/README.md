# Lokale KI und männliche Stimme

Auf diesem Laptop vorbereitet für Tormentor Android. Die bisherige Desktop-App wird nicht verändert.

1. `KI-starten.cmd` im übergeordneten Ordner öffnen. Ollama und die Tormentor-WLAN-Brücke starten ohne zusätzliche Fenster im Hintergrund.
2. Laptop und Tablet ins gleiche **private WLAN** verbinden. Windows-Firewall muss eingehende Verbindungen für die Tormentor-Brücke auf TCP 8765 im privaten Netz erlauben. Kein Portforwarding am Router einrichten.
3. `Tablet-Verbindung.json` aufs Tablet kopieren. In Tormentor **Lokale KI einrichten → Datei importieren**. Alternativ Laptop-Adresse und Verbindungscode aus `Tablet-Verbindung.txt` eintragen. Die App prüft danach die Verbindung und spielt eine männliche Teststimme ab.
4. **Cortana einschalten**. „Cortana, frage Tormentor“ sagen. Die kurze Cortana-Antwort abwarten, **danach** die eigentliche Frage sprechen. Für diese Aufnahme wechselt die App in freie deutsche Offline-Spracherkennung mit Vosk. Beim ersten Versuch die Frage als eigenen Satz sprechen, nicht direkt an den Aktivierungsbefehl anhängen.
5. Die KI-Antwort erscheint als Text und wird mit einer lokalen neuronalen Männerstimme „Thorsten“ vorgelesen. Musik wird währenddessen abgesenkt; die Mikrofonerkennung pausiert, damit Tormentor nicht seine eigene Antwort ausführt.
6. Zum Beenden `KI-stoppen.cmd` öffnen.

Die zusätzliche Taste „Frage Tormentor“ erlaubt eine getippte Frage. „Alles stoppen“ verwirft eine ausstehende Antwort. Bereits begonnene Berechnung auf dem Laptop kann noch bis zum Abschluss laufen.

Es werden keine OpenAI- oder ElevenLabs-APIs aufgerufen. Nach dem erstmaligen Download arbeitet das lokale Modell ohne Internet und ohne Gebühren pro Anfrage. Stromverbrauch bleibt. Ollama läuft ausschließlich an `127.0.0.1:11435`, Cloud-Funktionen sind deaktiviert. Nur die durch einen zufälligen Verbindungscode geschützte Tormentor-Brücke hört im WLAN auf Port 8765. Verbindungscode bzw. Verbindungsdatei privat halten. Die Verbindung verwendet HTTP im privaten WLAN; Fragen und Antworten sind dabei nicht transportverschlüsselt.

Modell: `gemma3:4b`, 2048 Kontexttokens, maximal 180 Antworttokens, zwei CPU-Threads. Das Modell bleibt bis zu 30 Minuten im Speicher. Die Last beim gleichzeitigen Betrieb von Dungeon Alchemist/TV-Streaming muss im tatsächlichen Session-Aufbau geprüft werden. Bei zu langsamen Antworten lässt sich ein kleineres lokales Modell in `connection.json` einstellen, nachdem es heruntergeladen wurde.

`neural_voice.py` verwendet die lokale Piper-Stimme „Thorsten“. Die dunklere Variante ist voreingestellt; mit `"dark_voice": false` in `connection.json` lässt sich die natürliche Variante wählen. „Dungeon Master“ und „Dungeon“ erhalten eine englische Aussprachekorrektur. Nach Änderungen die KI neu starten. Die vorhandene Cortana-Aktivierungsantwort bleibt separat erhalten; Tormentor selbst antwortet männlich.

`connection.json` wird beim ersten Start mit einem zufälligen Verbindungscode erstellt. Es enthält keine Cloud-Zugangsdaten. Temporäre Dateien für die Sprachausgabe werden nach Gebrauch gelöscht. Fragen werden nicht in den Serverlogs protokolliert.

Quellen: [Ollama für Windows](https://docs.ollama.com/windows), [lokaler Betrieb und Netzwerk](https://docs.ollama.com/faq), [Chat-API](https://docs.ollama.com/api/chat).



## Regelfragen

Tormentor erklärt Regelfragen sachlich mit Ablauf und Zahlenbeispiel. Ohne Editionsangabe nimmt es D&D 5e an. Düstere Erzählweise ist für ausdrücklich gewünschte Szenen vorgesehen; die dunkle Thorsten-Stimme bleibt erhalten. Die hinterlegten Grundlagen zu Angriffswürfen orientieren sich an https://www.dndbeyond.com/sources/dnd/basic-rules-2014/combat. Dies ist keine vollständige Regeldatenbank; Antworten können weiterhin Fehler enthalten. Das Antwortlimit beträgt jetzt 320 Tokens bei Temperatur 0,25.

