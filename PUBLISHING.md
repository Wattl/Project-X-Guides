# Einen geprüften Guide veröffentlichen

Dieses Verfahren setzt den bestehenden Project-X-Guide-Workflow für den öffentlichen Downloadbereich um. Ein Entwurf, ein erfolgreicher PDF-Build oder die Erlaubnis, dieses Repository einzurichten, ist keine fachliche Freigabe.

## 1. Paket fertig prüfen

Research → Source Matrix → Glossary → Concept Model → Outline → Draft → DCS Translation → Scenarios → Red Team → Technical Audit → Layout → Release Candidate → Release.

Alle zwölf Vorstufen müssen für das konkrete Paket abgeschlossen sein. Runtime-Tests beziehen sich auf den exakten aktuellen DCS-Build, das Modul und die beschriebenen Verfahren. Die Prüfung umfasst das tatsächliche Verhalten; reine Handbuch-/Codelektüre genügt nicht. Rechte aller enthaltenen Bilder, Zitate und sonstigen Fremdinhalte separat klären. Bei neuer DCS-Version erneut prüfen; keinen Status automatisch übertragen.

## 2. Öffentlichen Prüfnachweis erstellen

Unter `evidence/<guide-id>-<version>.md` einen kleinen, eigens für die Öffentlichkeit verfassten Nachweis ablegen: Guide-ID, Titel, Modul, Version, Scope, Testdatum, exakter DCS-Build, ausgeführte Fälle, Ergebnis/Grenzen, Prüfer, bestätigte Rechte und Andys ausdrückliche Freigabe. Jeden PDF-Dateinamen mit Bytes und SHA-256 aufführen. Die Freigabe wird mit dem Repository-Besitzer `Wattl` gekennzeichnet. Keine privaten Pfade oder Bibliotheksinhalte kopieren.

## 3. Unveränderliche Releaseassets bereitstellen

Auf GitHub einen Release mit eindeutigem Tag, zum Beispiel `fa18c-navigation-v1.0.0`, für das freigegebene Paket anlegen. Bildschirm-PDF, Druck-PDF und gegebenenfalls Kurzkarten hochladen. Dateien niemals überschreiben; Korrekturen erhalten eine neue Dokumentversion. Pro PDF maximal 80 MB; größere Dateien vor der Freigabe optimieren. In den Release Notes steht gut sichtbar: **Archivfassung, geprüft für DCS <build>; aktuelle Auswahl immer auf der Downloadseite.**

Die Download-URLs müssen diesem Repository und diesem Muster entsprechen:

`https://github.com/Wattl/Project-X-Guides/releases/download/<tag>/<dateiname.pdf>`

## 4. Freigegebenen Katalogeintrag ergänzen

`catalog/releases.json` enthält `schema_version: 1` und eine Liste `releases`. Ein Eintrag hat:

- `guide_id`: stabiler Kleinbuchstaben-Slug; `title`, `module`; `version`: drei Zahlen, etwa `1.0.0`.
- `artifacts`: je Datei `filename`, `label`, `bytes`, `sha256` (klein geschrieben), `url`.
- `verification`: `status: "passed"`, `runtime_tested: true`, `dcs_build`, `tested_at`, `report: {path, sha256}`.
- `rights`: `status: "cleared"`, `reviewed_by`, `reviewed_at`.
- `gates`: `research`, `source_matrix`, `glossary`, `concept_model`, `outline`, `draft`, `dcs_translation`, `scenarios`, `red_team`, `technical_audit`, `layout`, `release_candidate`, jeweils `"passed"`.
- `approval`: `status: "approved"`, `approved_by: "Wattl"`, `approved_at`, `release_fingerprint`.

Datumswerte sind ISO-Daten oder ISO-Zeitpunkte mit Zeitzone. Der Fingerprint wird mit `tools/release_gate.py:release_fingerprint(record)` über den vollständigen Eintrag ohne `approval` berechnet. Er bindet die Freigabe an genau diese Artefakte, Tests, Rechte und Gate-Metadaten. Er ist eine Konsistenzprüfung, keine kryptografische Signatur und kein Ersatz für die tatsächliche Freigabe. Schreibberechtigte Maintainer tragen die Verantwortung für wahrheitsgemäße Nachweise.

Katalog und Nachweis gemeinsam committen. Tests ausführen, dann nach `main` übertragen. Der Workflow übernimmt Versionsabgleich, Binärdownload, Hashprüfung und Veröffentlichung der aktuellen Auswahl. Alte Einträge bleiben nachvollziehbar. Pro Guide-ID gewinnt die höchste geeignete Dokumentversion, Bildschirm/Druck/Kurzkarten bilden ein zusammengehöriges Paket. Widersprüchliche doppelte IDs/Versionen werden ausgeschlossen.

## Betrieb und Grenzen

- Automatische Abfrage: alle vier Stunden um Minute 17 (UTC), zusätzlich nach Änderungen und veröffentlichten Releases.
- Versionsquelle: https://updates.digitalcombatsimulator.com/ — ausschließlich die eindeutig bezeichnete aktuelle stabile DCS-Version; keine DCS-Updater-Versionsnummer.
- Bei Abruf-/Parsefehlern wird eine leere Auswahl veröffentlicht. Fehlerhafte PDF-Downloads schließen das ganze betroffene Guide-Paket aus.
- Bei neuen Builds wird nach der nächsten erfolgreichen Abfrage keine alte Buildfreigabe mehr auf der Startseite angeboten. Zwischen zwei Abfragen kann ein DCS-Update erscheinen; der Zeitpunkt der Abfrage bleibt sichtbar.
- Die Webseite blendet Links nach acht Stunden ohne frischen Nachweis aus. Ohne JavaScript zeigt sie keine Downloadlinks. Dies schützt die aktuelle Auswahl; bereits heruntergeladene Dateien und Archiv-URLs können nicht zurückgerufen werden. Während eines Deployment-Ausfalls können auch zuvor bekannte direkte /downloads/-URLs noch erreichbar bleiben, bis eine erfolgreiche Veröffentlichung die alten Kopien ersetzt.
- GitHub-Zeitpläne können verspätet starten oder ausfallen. Ein wöchentlicher erfolgreicher Versionsbeleg erzeugt Repository-Aktivität; nach längerem Ausfall/deaktivierten Workflows muss der Besitzer eingreifen.
- Es gibt keinen lokalen Ordner-Watcher: Erst abgeschlossene Prüfung und exakte Freigabe berechtigen zur Aufnahme in diesen öffentlichen Kanal.

Technische Grundlage: [GitHub Pages mit Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [Release-Links](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases), [Zeitplan-Deaktivierung](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).
