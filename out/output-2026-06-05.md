# df-heylou-gemini-extension — Output [CRUX-MK]
*Autonom aktiviert 2026-06-05T09:54:43.068523+00:00 | ollama-local/qwen2.5:14b-instruct*

# df-heylou-gemini-extension [CRUX-MK]

## Mission: HeyLou als Sub-Funktion in Gemini Function-Calling

### Stack:
- **Gemini-2.5-Pro / Gemini-1.5-Pro API**
- HeyLou-API-Backend (search_hotels, get_rates, compare_otas, book_direct, 
optimize_revenue)

### Beschreibung:
Die Dark Factory `df-heylou-gemini-extension` integriert HeyLou als Sub-Fun
Sub-Funktion in die Gemini Function-Calling-API. Diese Integration erweiter
erweitert den Reach von HeyLou durch die Nutzung der Gemini Plattform und e
ermöglicht es Gemini Nutzern, direkt über das Chat Interface Zugriff auf He
HeyLou Funktionen zu haben.

### Funktions-Capability Set:

| **Function** | **Beschreibung**                               | **Backend
**Backend**                                       |
|--------------|-------------------------------------------------|---------|--------------|-------------------------------------------------|--------------------------------------------------|
| `search_hotels(location, dates, preferences)`                | Hotel-Such
Hotel-Suche im Travel Knowledge Graph von HeyLou | df-heylou-travel-domain 
                       |
| `get_rates(hotel_id, date_range)`                            | Verfügbark
Verfügbarkeit und Preise für ein Hotel           | df-pms-mews-adapter (Wel
(Welle 36)                  |
| `compare_otas(hotel_id, dates)`                              | Kompensati
Kompensationsvergleich durch OTAs                | df-ota-* Adapters (Welle
(Welle 37)                    |
| `book_direct(hotel_id, room_type, guest, dates)`             | Direktes B
Buchen von Hotelräumen                 | df-heylou-travel-domain           
              |
| `optimize_revenue(hotel_id)`                                 | Revenue Op
Optimierung                              | Welle 40 (nachgeordnet)         
                 |

### Bereitstellungsmuster:
Gemini-LLM sendet Anfragen an unsere Extension, welche diese dann auf die e
entsprechenden HeyLou-API Backends routen. Dies geschieht über ein JSON Sch
Schema Tool Declaration.

```python
tools = [{"function_declarations": HEYLOU_FUNCTION_DEFINITIONS}]
response = gemini_client.generate_content(prompt, tools=tools)
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = extension.handle_function_call(part.function_call)
```

### Sandbox-Standard:
- `DF_HEYLOU_GEMINI_EXT_ENABLED=false`: Mock-Responses (synthetischer Trave
Travel Knowledge Graph)
- `DF_HEYLOU_GEMINI_EXT_ENABLED=true`, `PHRONESIS_TICKET` und `GEMINI_API_K
`GEMINI_API_KEY`: Real-Mode

### Architektur:
Die Gemini LLM sendet eine Function Call, welche von der Extension auf die 
entsprechenden HeyLou-API Backends geroutet wird. Die Response wird durch d
den Audit Logger (HMAC-SHA256) verarbeitet.

```
Gemini-LLM → functionCall → GeminiExtension.handle_function_call()
                              ├── search_hotels    → mock | df-heylou-trave
df-heylou-travel-domain
                              ├── get_rates        → mock | df-pms-mews-ada
df-pms-mews-adapter
                              ├── compare_otas     → mock | df-ota-booking-
df-ota-booking-adapter
                              ├── book_direct      → mock | df-heylou-trave
df-heylou-travel-domain (K_0)
                              └── optimize_revenue → mock | W40-Stub
                              ↓
                          AuditLogger (HMAC-SHA256 JSONL)
```

### Sicherheitsprinzipien:
Für die Bereitstellung der Real-Mode-Möglichkeiten sind K13 Prüfungen und K
K16 mkdir Mutex in den Skripten implementiert.

### Tests:
```bash
pytest tests/ -v
```
Dies führt automatisierte Tests aus, um sicherzustellen, dass alle Funktion
Funktionen korrekt funktionieren.