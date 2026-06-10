# df-heylou-gemini-extension — PRODUKTION [CRUX-MK]
*2026-06-09T16:26:38.592234+00:00 | ollama-local/kemmer-14b-ctx8k*

# df-heylou-gemini-extension [CRUX-MK]

## Mission: HeyLou als Sub-Funktion in Gemini Function-Calling

### Stack:
- **Gemini-2.5-Pro / Gemini-1.5-Pro API**
- **HeyLou-API-Backend (search_hotels, get_rates, compare_otas, book_direct, optimize_revenue)**

### Beschreibung:
Die Dark Factory `df-heylou-gemini-extension` integriert HeyLou als Sub-Funktion in die Gemini Function-Calling-API. Diese Integration erweitert den Reach von HeyLou durch die Nutzung der Gemini Plattform und ermöglicht es Gemini Nutzern, direkt über das Chat Interface Zugriff auf HeyLou Funktionen zu haben.

### Funktions-Capability Set:

| **Function** | **Beschreibung**                               | **Backend**                                       |
|--------------|-------------------------------------------------|---------------------------------------------------|
| `search_hotels(location, dates, preferences)`                | Hotel-Suche im Travel Knowledge Graph von HeyLou  | df-heylou-travel-domain                           |
| `get_rates(hotel_id, date_range)`                            | Verfügbarkeit und Preise für ein Hotel            | df-pms-mews-adapter (Welle 36)                    |
| `compare_otas(hotel_id, dates)`                              | Kompensationsvergleich durch OTAs                  | df-ota-* Adapters (Welle 37)                       |
| `book_direct(hotel_id, room_type, guest, dates)`             | Direktes Buchen von Hotelräumen                    | df-heylou-travel-domain                            |
| `optimize_revenue(hotel_id)`                                 | Revenue Optimierung                               | Welle 40 (nachgeordnet)                            |

### Bereitstellungsmuster:
Gemini-LLM sendet Anfragen an unsere Extension, welche diese dann auf die entsprechenden HeyLou-API Backends routen. Dies geschieht über ein JSON-Schema Tool Declaration.

```python
tools = [{"function_declarations": HEYLOU_FUNCTION_DEFINITIONS}]
response = gemini_client.generate_content(prompt, tools=tools)
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = extension.handle_function_call(part.function_call)
```

### Sandbox-Standard:
- `DF_HEYLOU_GEMINI_EXT_ENABLED=false` → Mock-Responses (HeyLou Travel-Knowledge-Graph synthetisch)
- `DF_HEYLOU_GEMINI_EXT_ENABLED=true` + `PHRONESIS_TICKET` + `GEMINI_API_KEY` → Real-Mode

### Architektur:

```
Gemini-LLM → functionCall → GeminiExtension.handle_function_call()
                              ├── search_hotels    → mock | df-heylou-travel-domain
                              ├── get_rates        → mock | df-pms-mews-adapter
                              ├── compare_otas     → mock | df-ota-* (W37)
                              ├── book_direct      → mock | df-heylou-travel-domain (K_0)
                              └── optimize_revenue → mock | W40-Stub
                              ↓
                          AuditLogger (HMAC-SHA256 JSONL)
```

### K11-K16 + LC1-LC5

**Konfiguration:** Siehe `config.yaml`. K13 Pre-Action-Verification via `auth_handler.verify_phronesis_ticket()`. K16 mkdir-Mutex in `scripts/run-*.sh`.

### LaunchAgent:
- **Plist**: `scripts/com.kemmer.df-heylou-gemini-extension.plist`
- **StartInterval:** 7200s (2h), RunAtLoad: true
- **WorkingDir:** `/Users/make/Projects/dark-factories/df-heylou-gemini-extension`

### Tests:

```bash
pytest tests/ -v
```

### Cross-DF-Coupling (W36/W37 Backends):
Aktuell Lazy-Impo

#### Integrationsdetails:
1. **search_hotels**
   - **Beschreibung:** Hotel-Suche im Travel Knowledge Graph von HeyLou.
   - **Mock-Response**:
     ```json
     {
       "status": 200,
       "hotels": [
         {
           "id": 123456789,
           "name": "Grand Plaza",
           "location": "Orlando, FL",
           "star_rating": 4.5,
           "price_per_night": 250
         },
         {
           "id": 987654321,
           "name": "Luxury Inn",
           "location": "Orlando, FL",
           "star_rating": 4.0,
           "price_per_night": 200
         }
       ]
     }
     ```
   - **Real-Mode Response:**
     ```json
     {
       "status": 200,
       "hotels": [
         {
           "id": 123456789,
           "name": "Grand Plaza",
           "location": "Orlando, FL",
           "star_rating": 4.5,
           "price_per_night": 250
         },
         {
           "id": 987654321,
           "name": "Luxury Inn",
           "location": "Orlando, FL",
           "star_rating": 4.0,
           "price_per_night": 200
         }
       ]
     }
     ```

2. **get_rates**
   - **Beschreibung:** Verfügbarkeit und Preise für ein Hotel.
   - **Mock-Response**:
     ```json
     {
       "status": 200,
       "rates": [
         {"date": "2026-10-05", "price": 300, "available_rooms": 10},
         {"date": "2026-10-06", "price": 350, "available_rooms": 8}
       ]
     }
     ```
   - **Real-Mode Response:**
     ```json
     {
       "status": 200,
       "rates": [
         {"date": "2026-10-05", "price": 300, "available_rooms": 10},
         {"date": "2026-10-06", "price": 350, "available_rooms": 8}
       ]
     }
     ```

3. **compare_otas**
   - **Beschreibung:** Kompensationsvergleich durch OTAs.
   - **Mock-Response**:
     ```json
     {
       "status": 200,
       "otacompare": [
         {"ota_name": "Booking.com", "price_per_night": 315, "booking_fee": 2.5},
         {"ota_name": "Expedia", "price_per_night": 320, "booking_fee": 3}
       ]
     }
     ```
   - **Real-Mode Response:**
     ```json
     {
       "status": 200,
       "otacompare": [
         {"ota_name": "Booking.com", "price_per_night": 315, "booking_fee": 2.5},
         {"ota_name": "Expedia", "price_per_night": 320, "booking_fee": 3}
       ]
     }
     ```

4. **book_direct**
   - **Beschreibung:** Direktes Buchen von Hotelräumen.
   - **Mock-Response**:
     ```json
     {
       "status": 200,
       "confirmation_number": "1A2B3C",
       "room_type": "Deluxe King Suite",
       "check_in_date": "2026-10-05",
       "check_out_date": "2026-10-07"
     }
     ```
   - **Real-Mode Response:**
     ```json
     {
       "status": 200,
       "confirmation_number": "1A2B3C",
       "room_type": "Deluxe King Suite",
       "check_in_date": "2026-10-05",
       "check_out_date": "2026-10-07"
     }
     ```

5. **optimize_revenue**
   - **Beschreibung:** Revenue Optimierung.
   - **Mock-Response**:
     ```json
     {
       "status": 200,
       "revenue_optimization_recommendations": [
         {"date_range": ["2026-10-05", "2026-10-07"], "room_type": "Deluxe King Suite", "recommendation_price_per_night": 340},
         {"date_range": ["2026-10-08", "2026-10-10"], "room_type": "Standard Queen Room", "recommendation_price_per_night": 295}
       ]
     }
     ```
   - **Real-Mode Response:**
     ```json
     {
       "status": 200,
       "revenue_optimization_recommendations": [
         {"date_range": ["2026-10-05", "2026-10-07"], "room_type": "Deluxe King Suite", "recommendation_price_per_night": 340},
         {"date_range": ["2026-10-08", "2026-10-10"], "room_type": "Standard Queen Room", "recommendation_price_per_night": 295}
       ]
     }
     ```

### Integration und Testen:

#### Schritte zur Bereitstellung:
1. **Umgebung vorbereiten:**
   - Setzen Sie die Umgebungsvariablen `DF_HEYLOU_GEMINI_EXT_ENABLED`, `PHRONESIS_TICKET` und `GEMINI_API_KEY`.
   
2. **Mock-Modus aktivieren:**
   - Legen Sie die Variable `DF_HEYLOU_GEMINI_EXT_ENABLED=false`. Dadurch werden nur Mock-Antworten generiert.

3. **Real-Mode bereitstellen:**
   - Setzen Sie `DF_HEYLOU_GEMINI_EXT_ENABLED=true`, und stellen Sie sicher, dass die entsprechenden Authentifizierungskennungen (`PHRONESIS_TICKET` und `GEMINI_API_KEY`) korrekt sind.

4. **Tests durchführen:**
   ```bash
   pytest tests/ -v
   ```

5. **LaunchAgent konfigurieren:**
   - Installieren Sie den LaunchAgent mit dem Plist-File `scripts/com.kemmer.df-heylou-gemini-extension.plist`.

6. **Integrität überprüfen:**
   - Bestimmen Sie die Integrität der Daten und Vorgänge durch das AuditLogger System, das HMAC-SHA256 JSONL Log-Einträge erstellt.

Diese Dokumentation bietet eine detaillierte Beschreibung der Integration von HeyLou-Funktionen in die Gemini Function-Calling-API, einschließlich Mock-Antworten für den Testmodus und Real-Mode-Antworten für produktionsbereite Umgebungen.