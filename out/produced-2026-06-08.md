# df-heylou-gemini-extension — PRODUKTION [CRUX-MK]
*2026-06-08T23:43:13.450258+00:00 | ollama-local/kemmer-14b-ctx8k*

## df-heylou-gemini-extension [CRUX-MK]

### Übersicht

Die Dark Factory `df-heylou-gemini-extension` integriert die Funktionen von HeyLou in das Gemini Function-Calling-API-Framework, um eine direkte und effiziente Benutzerschnittstelle für Hotelbuchungen und verwandte Dienste zu erstellen. Diese Kombination ermöglicht es Gemini Nutzern, den gesamten Reisevorgang direkt über ein Chat-Interface abzuwickeln.

### Stack

Die Integration verwendet folgende Technologien:
- **Gemini-2.5-Pro API**: Eine fortschrittliche Sprachmodell-API für komplexere Funktionen und Interaktionen.
- **HeyLou APIs**:
  - `search_hotels(location, dates, preferences)`: Sucht Hotels basierend auf gegebener Lokalisierung, Buchungsdaten und Vorlieben im Travel Knowledge Graph von HeyLou.
  - `get_rates(hotel_id, date_range)`: Berechnet Verfügbarkeit und Preise für ein Hotel über den Property Management System (PMS)/Revenue Management System (RMS).
  - `compare_otas(hotel_id, dates)`: Vergleicht die Kompensationsstrategien von verschiedenen Online Travel Agencies (OTAs).
  - `book_direct(hotel_id, room_type, guest, dates)`: Erstellt eine direkte Buchung für ein Hotelzimmer ohne zusätzliche Gebühren.
  - `optimize_revenue(hotel_id)`: Enthält einen Stub für zukünftige Revenue-Optimierungsfunktionen.

### Bereitstellungsmuster

Gemini Function-Calling sendet Anfragen an die `df-heylou-gemini-extension`, welche diese dann auf entsprechende HeyLou-API Backends routet. Das Vorgehen erfolgt über ein JSON-Schema Tool Declaration:
```python
tools = [{"function_declarations": HEYLOU_FUNCTION_DEFINITIONS}]
response = gemini_client.generate_content(prompt, tools=tools)
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = extension.handle_function_call(part.function_call)
```

### Sandbox-Standard

Der Betrieb der Extension läuft standardmäßig im Mock-Modus. Um den echten Modus zu aktivieren, müssen die Umgebungsvariablen `DF_HEYLOU_GEMINI_EXT_ENABLED` auf 'true' gesetzt werden, ein gültiges `PHRONESIS_TICKET` und eine gültige `GEMINI_API_KEY` bereitgestellt sein.

### Architektur

Die Architektur der Integration umfasst mehrere Komponenten:
```
Gemini-LLM → functionCall → GeminiExtension.handle_function_call()
                              ├── search_hotels    → df-heylou-travel-domain
                              ├── get_rates        → df-pms-mews-adapter
                              ├── compare_otas     → df-ota-* adapters
                              ├── book_direct      → df-heylou-travel-domain (K_0)
                              └── optimize_revenue → W40-Stub
                              ↓
                          AuditLogger (HMAC-SHA256 JSONL)
```
Die Komponenten sind für spezifische Funktionen verantwortlich und senden ihre Ergebnisse an einen AuditLogger, um eine detaillierte Überwachung zu ermöglichen.

### K11-K16 + LC1-LC5

Diese Best Practices und Sicherheitsrichtlinien sind in der `config.yaml`-Datei dokumentiert. Insbesondere wird die K13 Pre-Action-Verification via `auth_handler.verify_phronesis_ticket()` verwendet, um sicherzustellen, dass nur berechtigte Anfragen verarbeitet werden.

### Sandbox-Konfiguration

Die Sandbox-Konfiguration kann über folgende Umgebungsvariablen gesteuert werden:
- **DF_HEYLOU_GEMINI_EXT_ENABLED**: Aktiviert die Integration (Standard: `false` für Mock-Modus).
- **PHRONESIS_TICKET**: Ein gültiger Phronesis-Ticket-Wert, um Sicherheit und Authentifizierung zu gewährleisten.
- **GEMINI_API_KEY**: Eine gültige Gemini-API-Schlüssel-ID zur Zugriffsberechtigung.

### Tests

Die Integration kann durch die folgenden Befehle getestet werden:
```bash
pytest tests/ -v
```
Dies führt alle vorhandenen Testfälle aus und liefert eine detaillierte Auswertung.

### Cross-DF-Coupling (W36/W37 Backends)

Die Integration läuft derzeit im Lazy-Import Modus. In den kommenden Welle 40 wird die Revenue Optimization Funktion implementiert, um vollständige Funktionalität zu gewährleisten.

### Sandbox-Dienst

Der LaunchAgent ist konfiguriert, um das System alle zwei Stunden (StartInterval: 7200s) neu zu starten und bei der Initialisierung zu laden. Die Konfiguration wird in der Plist-Datei `scripts/com.kemmer.df-heylou-gemini-extension.plist` gespeichert.

### Fazit

Die Integration von HeyLou-Funktionen in das Gemini Function-Calling-API-Modell erweitert den Funktionsumfang des Chatbots und ermöglicht eine reibungslose Buchung von Reisehotels sowie eine detaillierte Analyse der OTA-Vergleichsmöglichkeiten. Die Kombination unterstützt sowohl die Nutzer in der Entscheidungsfindung als auch in der effizienten Erledigung von Aufgaben im Bereich des B2B Corporate Travel Bookings.

### Anhang: Verwendete Datenquellen und Methodik

- **AllFly.io** (WARGAME-VENDOR-ALLFLY-2026-04-24.md): Informationen über den Markenstandort, die Finanzierung, Produkte sowie Technologie.
- **Welle-19 — 25-Sprachen Lokal Competitive Map** (WELLE-19-25-SPRACHEN-LOKAL-COMPETITIVE-MAP-2026-04-20.md): Lokale Hauptgegner und ihre Strategien in verschiedenen Markten.
- **METHODIK-KATALOG-V10-WELLE-16-MASTER** (METHODIK-KATALOG-V10-WELLE-16-MASTER-2026-05-04.md): Struktur für die Implementierung der Cross-DF-Coupling und weiterer Verbesserungen.

Diese Dokumentation stellt eine umfassende Einführung in die Funktionalität und Integration von `df-heylou-gemini-extension` dar, um sicherzustellen, dass alle Best Practices und Technologien korrekt implementiert sind.