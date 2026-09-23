# Sicherheit und private Daten

Keine Kennwörter, API-Schlüssel, Einladungs- oder Sitzungstokens, Datenbankkopien, Spielerprofile oder Kampagneninhalte in öffentliche Issues, Pull Requests oder Commits aufnehmen.

Bei einem Sicherheitsproblem zunächst nur eine allgemeine Problembeschreibung ohne Geheimnisse oder personenbezogene Daten bereitstellen und mit dem Repository-Inhaber einen geeigneten vertraulichen Kanal abstimmen.

Das Portal lokal zunächst nur an Loopback betreiben. Internetbetrieb benötigt die vorgesehene HTTPS-Origin-Konfiguration, aktuelle Abhängigkeiten, eigene Konten und getestete Backups. Das Repository enthält keine produktiven Zugangsdaten oder Datenbank.

Die Dateiliste in `.gitignore` und `tools/check_publication.py` helfen bei der Veröffentlichung; sie ersetzen keine inhaltliche Prüfung neuer Dateien. Insbesondere kein `git add -f` für private Dateien verwenden.
