# AI Coding Agent Instructions for SHARK v18

## Project Overview
SHARK v18 is an advanced system for identifying mobile devices (iOS and Android) using AI and browser fingerprinting. It provides accessory codes for identified devices and supports multi-layer detection strategies:
- **User-Agent Parsing**: Primary detection method with 100% accuracy.
- **AI Brain**: Machine learning-based fallback with 85-95% accuracy.
- **Client-side Heuristics**: Additional fallback with 60-80% accuracy.

The system is built with Python (Flask) and includes client-side JavaScript for heuristics.

## Key Components
- **Backend**:
  - `shark_v18.py`: Main entry point for the Flask application.
  - `app/`: Contains modularized components:
    - `routes/`: API endpoints and admin routes.
    - `models/`: Device identification logic.
    - `utils/`: Helper functions for validation and logic.
- **Frontend**:
  - `templates/`: HTML templates for the web interface.
- **Data**:
  - `shark_brain_v18.json`: Stores AI Brain signatures.
  - `shark_logs_v18.csv`: Logs system operations.

## Developer Workflows
### Running the Application
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python shark_v18.py
   ```
3. Access the app at `https://localhost:5000`.

### Testing
- Unit tests are located in `test_setup_database.py`.
- Run tests with:
  ```bash
  python -m unittest test_setup_database.py
  ```

### Debugging
- Use `LOG_FILE` and `RECENT_LOGS` for debugging recent operations.
- Modify `app.run()` in `shark_v18.py` to enable debug mode:
  ```python
  app.run(debug=True)
  ```

## Project-Specific Conventions
- **Device Identification**:
  - Update `ANDROID_IDENTIFIERS` and `ACCESSORY_CODES` for new models.
  - Follow the format in `README.md` for adding new devices.
- **AI Brain**:
  - Signatures are stored in `shark_brain_v18.json`.
  - Ensure thread-safe operations when modifying the file.
- **Rate Limiting**:
  - Defined in `shark_v18.py` using `flask-limiter`.
  - Example limits:
    - `/api/check_brain`: 30 requests/min.
    - `/api/learn`: 10 requests/min.

## Integration Points
- **External Libraries**:
  - `flask`, `flask-cors`, `flask-limiter`: Backend framework and middleware.
  - `qrcode`: Generates QR codes for quick access.
- **Cross-Component Communication**:
  - Routes in `routes/` interact with models in `models/`.
  - Utility functions in `utils/` are shared across components.

## Examples
### Adding a New Device
1. Update `ANDROID_IDENTIFIERS` in `models/heuristic_db.py`:
   ```python
   ANDROID_IDENTIFIERS = {
       "SM-XXXX": "Samsung Galaxy NEW MODEL",
   }
   ```
2. Add accessory codes in `models/identifiers.py`:
   ```python
   ACCESSORY_CODES = {
       "Samsung Galaxy NEW MODEL": {"screen": "SA9U1", "case": "SA9U2"},
   }
   ```
3. (Optional) Add heuristics in `utils/logic.py`:
   ```javascript
   const DB_HEURISTIC = [
       {name:"Samsung Galaxy NEW MODEL",w:412,h:915,hz:120,gpu:"adreno"},
   ];
   ```

### API Example
#### Check Device
Request:
```json
{
  "w": 412,
  "h": 915,
  "hz": 120,
  "gpu": "adreno 740",
  "canvasHash": "a3f2b1c",
  "userAgent": "Mozilla/5.0 ... SM-S928B ..."
}
```
Response:
```json
{
  "found": true,
  "model": "Samsung Galaxy S24 Ultra",
  "confidence": 100,
  "source": "UA_EXACT",
  "codes": {
    "screen": "SA1U1",
    "case": "SA1U2"
  }
}
```