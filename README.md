# Tormentor

Deutschsprachiger Begleiter für Pen-and-Paper-Runden: Android-App, Desktop-Werkzeuge und ein Python-Spielerportal.

## Bestandteile

- **Spielerportal:** Konten mit Einladungscodes, Charakterbogen, private Nachrichten, gezielt freigegebene Handouts und vom DM verwaltete Inspirationspunkte.
- **Android:** Szenen und Medien, Würfeln, Sprachsteuerung und Zugang zum Kampagnenportal. Quellcode unter `Tormentor_Android/`.
- **Desktop:** Mediensteuerung sowie Werkzeuge für lokale Aufnahmen, Transkription und die geprüfte Veröffentlichung einer Chronik.
- **Codex:** deutschsprachige Regelhilfen und Quellenangaben, getrennt nach Edition und Homebrew.

Dieses Repository enthält **keine echten Spielerprofile, Kampagnen, Handouts, Nachrichten, Aufnahmen, Datenbanken oder Zugangsdaten**. Daten werden bei der Nutzung lokal erzeugt. In den Tests verwendete Konten und Inhalte sind synthetische Testdaten.

## Portal lokal starten

Voraussetzung: Python 3.12 oder neuer.

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-portal.txt
python portal.py init-dm
python portal.py
```

Danach `http://127.0.0.1:8787` öffnen. Das DM-Konto wird interaktiv angelegt; es gibt keine voreingestellten Zugangsdaten. Die neue `portal.sqlite3` bleibt lokal und wird von Git ignoriert.

Für Internetbetrieb sind HTTPS, eine korrekt gesetzte `TORMENTOR_PUBLIC_ORIGIN` und eine eigene Serverkonfiguration erforderlich. Allgemeine Vorlagen liegen unter `deploy/`. Die Einrichtung des produktiven Servers und dessen Daten sind nicht Teil des Repositorys.

## Tests

```sh
python -m unittest test_portal_access test_portal_handouts test_portal_session test_portal_security
```

Diese Tests prüfen unter anderem Einladungscodes, Handout-Empfänger, Kontentrennung und DM-Inspiration mit temporären Datenbanken. Weitere Tests liegen unter `test_*.py`; einige Medien- und Drucktests benötigen zusätzliche lokale Dateien.

## Android und Desktop

Die Android-App setzt Android 8.1 oder neuer voraus. Für den Build werden Java 17, Gradle 8.9 und das Android-SDK benötigt; die Projektdateien liegen unter `Tormentor_Android/`. Die lokale Build-Anleitung beschreibt die bisherige Werkzeugstruktur. SDK, Gradle, Sprachmodelle und Medien müssen separat eingerichtet werden.

Die Desktop-Oberfläche startet über `gui.py`. Ihre optionalen Abhängigkeiten stehen in `requirements-desktop.txt`. Für Cloud-Funktionen werden eigene Schlüssel benötigt; `.env.example` enthält ausschließlich leere Vorlagen.

## Nicht enthaltene Dateien

Der öffentliche Quellcode ist kein vollständiges Installationspaket. Die lokale Szenen-Mediensammlung, Sprachmodelle und fertige Druck-PDFs sind nicht in Git enthalten. Android-Oberflächenressourcen sind enthalten; Offline-Sprachmodell und Intro-Medien werden für einen eigenen Build zusätzlich benötigt. Quellen und vorhandene Lizenzhinweise sind in `THIRD_PARTY_NOTICES.md` und den jeweiligen Komponenten dokumentiert.

Die lokale mehrseitige Charakterbogen-Weiterentwicklung ist im Quellcode enthalten. Ein Commit entspricht nicht automatisch dem Stand einer produktiven Installation.

## Beiträge und Datenschutz

Die `.gitignore` verwendet eine ausdrückliche Dateiliste. Neue Quelldateien müssen bewusst ergänzt werden. Vor jedem Upload kann `python tools/check_publication.py` die bereitgestellten Git-Dateien auf ausgeschlossene Dateitypen und typische Geheimnisse prüfen.

Bitte keine echten Kampagnendaten, Zugangsdaten oder ungeschwärzten Spielerprofile in Issues oder Pull Requests veröffentlichen. Siehe `SECURITY.md`.

## Lizenzen

Für den eigenen Projektcode wurde noch keine allgemeine Open-Source-Lizenz festgelegt. Die Veröffentlichung ist keine pauschale Neulizenzierung fremder Inhalte. Bestehende SRD- und Abhängigkeitslizenzen sowie Namensnennungen bleiben erhalten; siehe `THIRD_PARTY_NOTICES.md`.

## Installationsdateien

Android-APK und erster Windows-EXE-Build werden separat unter **Releases** angeboten. Der historische Windows-Build ist älter als der Quellcode und enthält noch nicht die späteren Portal-Erweiterungen. Eigene API-Schlüssel werden nicht mitgeliefert.
