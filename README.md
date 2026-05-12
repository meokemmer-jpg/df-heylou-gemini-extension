# df-heylou-gemini-extension [CRUX-MK]

Welle-39 LLM Sub-Funktion Extension: **HeyLou als Sub-Funktion in Gemini Function-Calling**.

Stack: Gemini-2.5-Pro / Gemini-1.5-Pro Function-Calling API.

## HeyLou-Capability-Set (5 Functions)

| Function | Beschreibung | Backend |
|---|---|---|
| `search_hotels(location, dates, preferences)` | Hotel-Search im HeyLou Travel-Knowledge-Graph | df-heylou-travel-domain |
| `get_rates(hotel_id, date_range)` | PMS/RMS-Rates pro Hotel | df-pms-mews-adapter (W36) |
| `compare_otas(hotel_id, dates)` | OTA-Spread (Booking/Expedia/HRS) | df-ota-* (W37) |
| `book_direct(hotel_id, room_type, guest, dates)` | Direct-Booking via HeyLou (kommissions-frei) | df-heylou-travel-domain |
| `optimize_revenue(hotel_id)` | Revenue-Optimizer Stub | W40 (Pending) |

## Provider-API-Pattern

Gemini Function-Calling: Tool-Declaration als JSON-Schema, Modell ruft `functionCall` → unsere Extension routet zu HeyLou-API-Backend.

```python
tools = [{"function_declarations": HEYLOU_FUNCTION_DEFINITIONS}]
response = gemini_client.generate_content(prompt, tools=tools)
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = extension.handle_function_call(part.function_call)
```

## Sandbox-Default

- `DF_HEYLOU_GEMINI_EXT_ENABLED=false` → Mock-Responses (HeyLou Travel-Knowledge-Graph synthetisch)
- `DF_HEYLOU_GEMINI_EXT_ENABLED=true` + `PHRONESIS_TICKET` + `GEMINI_API_KEY` → Real-Mode

## Architektur

```
Gemini-LLM → functionCall → GeminiExtension.handle_function_call()
                              ├── search_hotels    → mock | df-heylou-travel-domain
                              ├── get_rates        → mock | df-pms-mews-adapter
                              ├── compare_otas     → mock | df-ota-booking-adapter
                              ├── book_direct      → mock | df-heylou-travel-domain (K_0)
                              └── optimize_revenue → mock | W40-Stub
                              ↓
                          AuditLogger (HMAC-SHA256 JSONL)
```

## K11-K16 + LC1-LC5

Siehe `config.yaml`. K13 Pre-Action-Verification via `auth_handler.verify_phronesis_ticket()`. K16 mkdir-Mutex in `scripts/run-*.sh`.

## LaunchAgent

- Plist: `scripts/com.kemmer.df-heylou-gemini-extension.plist`
- StartInterval: 7200s (2h), RunAtLoad: true
- WorkingDir: `/Users/make/Projects/dark-factories/df-heylou-gemini-extension`

## Tests

```bash
pytest tests/ -v
```

## Cross-DF-Coupling (W36/W37 Backends)

Aktuell Lazy-Import-Stubs: Backends sind import-safe-mockable. Live-Wiring per W40 (Real-Backend-Connector).

[CRUX-MK]
