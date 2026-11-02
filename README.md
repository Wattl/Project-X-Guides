# Project X · Guides

**Downloads und aktueller Prüfstand:** https://wattl.github.io/Project-X-Guides/

Diese feste Adresse kann weitergegeben werden. Downloads brauchen kein GitHub-Konto.

Hier erscheinen ausschließlich eigene Project-X-Guides, deren exakte PDF-Dateien fachlich geprüft, im angegebenen DCS-Build praktisch getestet, zur Veröffentlichung freigegeben und hinsichtlich der Verteilungsrechte geklärt sind. Pro Guide wird nur die jüngste dafür geeignete Ausgabe angeboten.

**Startstand am 02.11.2026:** Noch kein Guide erfüllt alle Veröffentlichungskriterien. F/A-18C Navigation und BFM/ACM befinden sich in der Prüfung. Das Portal und die Automatik werden unabhängig davon eingerichtet; Entwürfe erhalten dadurch keine fachliche Freigabe.

## Automatische Aktualisierung

- Nach einer freigegebenen Veröffentlichung, bei Änderungen am Katalog und planmäßig alle vier Stunden wird die offizielle DCS-Version abgefragt.
- Nur exakt dazu passende Testnachweise schalten Downloads frei. Neue DCS-Builds übernehmen keine alte Testfreigabe.
- Die aktuellen PDF-Kopien werden aus den unveränderten GitHub-Releaseassets geladen und anhand von Größe und SHA-256 kontrolliert.
- Bei unbekanntem DCS-Build oder ungeklärten Nachweisen bleibt die aktuelle Auswahl leer. Ist die Versionsabfrage älter als acht Stunden, blendet die Webseite Downloadlinks aus.
- Frühere Releases bleiben als nachvollziehbares Archiv erhalten. Direkte Archivlinks sind keine Aussage über aktuelle Kompatibilität.

GitHub kann Dateien verteilen und Nachweise prüfen. Die fachliche Arbeit, den praktischen DCS-Test und Andys Freigabe kann es nicht selbst durchführen. Änderungen auf einem lokalen Laufwerk werden nicht automatisch zu Veröffentlichungen.

## Pflege

[Veröffentlichungsverfahren](PUBLISHING.md) · [Katalog](catalog/releases.json) · [Automatik](../../actions/workflows/publish.yml)

Die Prüfung läuft in GitHub Actions, auch wenn der lokale Rechner ausgeschaltet ist. Ein erfolgreicher Versionsabgleich wird einmal pro Kalenderwoche sowie bei einem DCS-Wechsel im Repository protokolliert. Das hält den öffentlichen Prüfverlauf nachvollziehbar und vermeidet reguläre Inaktivität des Zeitplans. Nach Ausfällen oder einer manuellen Deaktivierung muss die Automatik gegebenenfalls erneut gestartet werden.

Es werden keine fremden Handbücher, Bibliotheksoriginale oder privaten Control-Dateien gespiegelt. Dieses Community-Projekt ist kein offizielles Angebot von Eagle Dynamics.
