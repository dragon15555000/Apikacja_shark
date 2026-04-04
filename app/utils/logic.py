"""
SHARK v18 - Business Logic Module
Główne funkcje logiczne: parsowanie User-Agent i algorytm dopasowania urządzeń
"""
import re
import logging
from app.config import USE_MONGODB, logger
from app.models.heuristic_db import HEURISTIC_DB
from app.database import verified_models_collection


def normalize_gpu_string(gpu):
    """Normalize GPU string for matching."""
    if not gpu:
        logger.warning("⚠️ GPU string missing or empty; using empty normalization")
        return ""
    gpu_lower = gpu.lower()
    gpu_lower = gpu_lower.replace("(tm)", "")
    gpu_lower = re.sub(r"[@()/,:]", " ", gpu_lower)
    gpu_lower = re.sub(r"\b(qualcomm|arm|gpu|graphics)\b", " ", gpu_lower)
    gpu_lower = re.sub(r"\s+", " ", gpu_lower).strip()
    return gpu_lower


def normalize_viewport(width, height):
    """Normalize viewport dimensions to reduce minor floating point noise."""
    if width is None or height is None:
        logger.warning(f"⚠️ Missing viewport dimensions: width={width}, height={height}")
        return width, height
    exact_width = round(width) if abs(width - round(width)) < 0.02 else width
    exact_height = round(height) if abs(height - round(height)) < 0.02 else height
    return exact_width, exact_height


def build_signature(width, height, dpr, ram, refresh_rate, gpu, canvas_hash=None):
    """
    Build canonical AI signature string.

    NOTE: canvas_hash is REMOVED from signature to ensure the same phone
    has the same signature regardless of browser (Chrome, Safari, Firefox, etc.)

    Signature format: width_height_dpr_ram_hz_gpu
    Example: 414_896_2.0_-1_60_apple gpu
    """
    exact_width, exact_height = normalize_viewport(width, height)
    dpr_rounded = round(float(dpr), 2)
    # ✅ USUNIĘTO canvas_hash - ten sam telefon = ta sama sygnatura!
    return f"{exact_width}_{exact_height}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}"


def detect_os(user_agent, gpu_lower):
    """Detect OS family based on user agent or GPU hints."""
    if user_agent:
        ua_lower = user_agent.lower()
        if "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower:
            return "ios"
        if "android" in ua_lower:
            return "android"
    if "apple" in gpu_lower:
        return "ios"
    if user_agent:
        logger.info("ℹ️ OS family unknown from UA and GPU hints")
    return "unknown"

def parse_device_from_ua(ua):
    """Parse device identifier from User-Agent string (iOS and Android)"""
    if not ua or not isinstance(ua, str):
        return None
    if len(ua) > 1000:
        ua = ua[:1000]
    try:
        # iPhone
        match = re.search(r'iPhone(\d+,\d+)', ua)
        if match:
            return "iPhone" + match.group(1)

        # iPad
        match_ipad = re.search(r'iPad(\d+,\d+)', ua)
        if match_ipad:
            return "iPad" + match_ipad.group(1)

        # Samsung (SM-XXXX lub SM-XXXXX) - obsługuje modele z 3 lub 4 cyframi
        match_samsung = re.search(r'(SM-[A-Z]\d{3,4}[A-Z]?)', ua)
        if match_samsung:
            # Normalizuj do 7 znaków (SM-X123) lub 8 (SM-X1234) bez sufiksu regionu
            code = match_samsung.group(1)
            # Usuń trailing literę regionu (np. SM-S928B -> SM-S928)
            if len(code) > 7 and code[-1].isalpha():
                code = code[:-1]
            return code[:8]

        # Google Pixel (obsługuje: Pixel 9, Pixel 8a, Pixel 9 Pro, Pixel 9 Pro XL, Pixel 9 Pro Fold, Pixel 9 Fold)
        match_pixel = re.search(r'(Pixel \d+(?:a)?(?:\s+(?:Pro(?:\s+(?:XL|Fold))?|Fold|FE))?)', ua)
        if match_pixel:
            return match_pixel.group(1)

        # Xiaomi (Build code)
        match_xiaomi = re.search(r'Build/([A-Z0-9]{10,})', ua)
        if match_xiaomi and 'Xiaomi' in ua:
            return match_xiaomi.group(1)[:12]

        # OnePlus
        match_oneplus = re.search(r'((?:CPH|LE|IN|NE)\d{4})', ua)
        if match_oneplus:
            return match_oneplus.group(1)

        # Huawei
        match_huawei = re.search(r'([A-Z]{3}-[A-Z0-9]{3,5})', ua)
        if match_huawei and ('HUAWEI' in ua.upper() or 'HONOR' in ua.upper()):
            return match_huawei.group(1)

        # Motorola - wzorce: XT2xxx, XT21xx, moto g, edge, razr
        match_motorola = re.search(r'(XT\d{4})', ua)
        if match_motorola:
            return match_motorola.group(1)

        if 'motorola' in ua.lower() or 'moto' in ua.lower():
            # Próbuj wyciągnąć nazwę modelu
            match_moto_name = re.search(r'(moto [a-z0-9 ]+|edge [a-z0-9 ]+|razr [a-z0-9 ]+)', ua.lower())
            if match_moto_name:
                return match_moto_name.group(1).strip()

        # Sony Xperia (XQ-XXNN)
        match_sony = re.search(r'(XQ-[A-Z]{2}\d{2})', ua)
        if match_sony:
            return match_sony.group(1)

        # ASUS ROG Phone (ASUS_XXXXXX)
        match_asus = re.search(r'(ASUS_[A-Z0-9]+)', ua)
        if match_asus:
            return match_asus.group(1)

        # Nothing Phone (A063, A065, A075)
        if 'nothing' in ua.lower():
            match_nothing = re.search(r'\b(A06[359]|A07[5])\b', ua)
            if match_nothing:
                return match_nothing.group(1)

        # Vivo / iQOO (Vmodel codes: V2306A, V2307A etc.)
        if 'vivo' in ua.lower() or 'iqoo' in ua.lower():
            match_vivo = re.search(r'\b(V\d{4}[A-Z])\b', ua)
            if match_vivo:
                return match_vivo.group(1)

        # Realme (RMX codes)
        match_realme = re.search(r'(RMX\d{4})', ua)
        if match_realme:
            return match_realme.group(1)

        # OPPO (CPH codes, obsługuje też OnePlus które już wyżej)
        match_oppo = re.search(r'(CPH\d{4})', ua)
        if match_oppo and 'OPPO' in ua.upper():
            return match_oppo.group(1)

        # Xiaomi - rozszerzony pattern (model name w UA)
        if 'xiaomi' in ua.lower() or 'redmi' in ua.lower() or 'poco' in ua.lower():
            match_xiaomi_name = re.search(r'(?:Xiaomi|Redmi|POCO)\s+([A-Za-z0-9 ]+?)(?:\s+Build|\s*\))', ua)
            if match_xiaomi_name:
                brand = 'Xiaomi' if 'xiaomi' in ua.lower() else ('Redmi' if 'redmi' in ua.lower() else 'POCO')
                return f"{brand} {match_xiaomi_name.group(1).strip()}"

    except Exception as e:
        logger.error(f"Error parsing UA: {e}")
    return None

def find_top_3_matches(width, height, refresh_rate, gpu, dpr, ram, cores, user_agent=None, color_gamut=None):
    """
    Find top 3 best matching models using Weighted Scoring Algorithm with OS Segmentation.

    TESTOWANIE:
    - Chrome DevTools (F12) → Tryb responsywny → Edit → Dodaj własne urządzenie
    - Ustaw User Agent, DPR, viewport - możesz symulować dowolny telefon
    - Sprawdź logi w konsoli serwera, aby zobaczyć szczegóły punktacji
    """
    matches = []
    gpu_lower = normalize_gpu_string(gpu)

    # OS Segmentation - wykryj iOS vs Android
    os_family = detect_os(user_agent, gpu_lower)
    is_ios = os_family == "ios"
    if os_family == "unknown":
        logger.info(f"ℹ️ OS family unknown; continuing with neutral scoring. UA={user_agent!r}")

    # Wykryj symulację/emulację (GPU komputera zamiast telefonu)
    is_simulation = any(keyword in gpu_lower for keyword in ["intel", "nvidia", "amd", "angle", "swiftshader", "mesa"])

    logger.info(f"📍 Weighted Scoring - OS: {'iOS' if is_ios else 'Android'}, DPR: {dpr}, RAM: {ram}, GPU: {gpu}")
    if is_simulation:
        logger.warning(f"⚠️ SYMULACJA WYKRYTA! GPU komputera: {gpu[:50]}")
    if refresh_rate in (None, -1, 0):
        logger.warning("⚠️ Refresh rate missing or invalid; Hz-based scoring will be skipped")

    # Pobierz zweryfikowane modele z MongoDB (jeśli dostępne)
    verified_models = {}
    if USE_MONGODB and verified_models_collection is not None:
        try:
            models_cursor = verified_models_collection.find({})
            for model_doc in models_cursor:
                name = model_doc.get('system_name') or model_doc.get('name')
                if name:
                    verified_models[name] = {
                        "w": model_doc.get('w'),
                        "h": model_doc.get('h'),
                        "dpr": model_doc.get('dpr'),
                        "ram": model_doc.get('ram', -1),
                        "hz": model_doc.get('hz'),
                        "gpu": model_doc.get('gpu', '').lower()
                    }
        except Exception as e:
            logger.warning(f"Error loading verified models: {e}")

    # Połącz HEURISTIC_DB z verified_models (verified ma priorytet)
    all_models = {**HEURISTIC_DB, **verified_models}

    logger.info(f"🔍 Searching in {len(all_models)} models ({len(HEURISTIC_DB)} heuristic + {len(verified_models)} verified)")

    try:
        for model_name, specs in all_models.items():
            score = 0
            reasons = []

            # 1. GPU (Waga: 40 Android / 0 iOS)
            # UWAGA: Normalizacja GPU - różne przeglądarki zwracają różne formaty
            # "Adreno (TM) 740" vs "Adreno 740 @ 680 MHz" - szukamy części wspólnej
            if not is_ios and specs["gpu"] and gpu_lower:
                spec_gpu_lower = normalize_gpu_string(specs["gpu"])
                # Wyciągnij kluczowe słowa (np. "adreno 740" → ["adreno", "740"])
                spec_gpu_parts = spec_gpu_lower.split()
                # Sprawdź czy wszystkie kluczowe części są w GPU użytkownika
                if all(part in gpu_lower for part in spec_gpu_parts if len(part) > 2):
                    score += 40
                    reasons.append(f"GPU: {specs['gpu']}")
                # Fallback: prosta zawartość
                elif spec_gpu_lower in gpu_lower:
                    score += 40
                    reasons.append(f"GPU: {specs['gpu']}")

            # 2. Viewport Width (Waga: 50 iOS / 20 Android)
            if width is not None and specs["w"] == width:
                score += 50 if is_ios else 20
                reasons.append(f"Szerokość: {specs['w']}px")
            elif not is_ios and width is not None and abs(specs["w"] - width) <= 40:
                score += 10
                reasons.append(f"Szerokość ~{specs['w']}px")

            # 3. Viewport Height (Waga: 30 iOS / 10 Android) - z tolerancją na pasek adresu
            if height is not None and specs["h"] == height:
                score += 30 if is_ios else 10
                reasons.append(f"Wysokość: {specs['h']}px")
            elif height is not None and height < specs["h"] and height > (specs["h"] - 160):
                # Tolerancja na pasek adresu (100-160px)
                score += 25 if is_ios else 8
                reasons.append(f"Wysokość ~{specs['h']}px (pasek adresu)")

            # 4. DPR (Waga: 20 iOS / 25 Android) - KLUCZOWE!
            if dpr is not None and abs(specs["dpr"] - dpr) < 0.1:
                score += 20 if is_ios else 25
                reasons.append(f"DPR: {specs['dpr']}x")
            elif dpr is not None and abs(specs["dpr"] - dpr) < 0.5:
                score += 10
                reasons.append(f"DPR ~{specs['dpr']}x")

            # 5. Hz (Waga: 5 bonus / -10 kara) - Rozróżnia Pro/Base
            if specs["hz"] and refresh_rate:
                if abs(specs["hz"] - refresh_rate) < 5:
                    score += 15 if is_ios else 5
                    reasons.append(f"Hz: {specs['hz']}Hz")
                else:
                    score -= 20 if is_ios else 10  # Kara za niezgodność (np. iPhone 16 vs 15 Pro)

                # Twarde rozróżnienie kolizji viewportu dla iOS (393x852 @3.0)
                if is_ios and specs["w"] == 393 and specs["h"] == 852 and abs(specs["dpr"] - 3.0) < 0.01:
                    if refresh_rate <= 90 and "pro" in model_name.lower():
                        score -= 30
                        reasons.append("Kara: Hz ~60 dla modelu Pro")
                    elif refresh_rate >= 100 and "pro" not in model_name.lower():
                        score -= 30
                        reasons.append("Kara: Hz ~120 dla modelu bazowego")

            # 6. RAM (Waga: 5 Android / 0 iOS) - słaby sygnał
            # UWAGA: navigator.deviceMemory zaokrągla wartości (12GB → 8GB)
            if not is_ios and ram is not None and ram > 0 and specs["ram"] > 0:
                # Użyj >= zamiast == bo Chrome zaokrągla RAM w dół
                if ram >= specs["ram"] or abs(specs["ram"] - ram) <= 2:
                    score += 5
                    reasons.append(f"RAM: ~{specs['ram']}GB")

            # 7. Color Gamut (+15 match / -10 kara: flagowiec bez P3)
            if color_gamut and specs.get("gamut"):
                spec_gamut = specs["gamut"]
                user_has_p3 = color_gamut in ("p3", "rec2020")
                spec_needs_p3 = spec_gamut in ("p3", "rec2020")
                if spec_needs_p3 and user_has_p3:
                    score += 15
                    reasons.append(f"Gamut: {spec_gamut}")
                elif spec_needs_p3 and not user_has_p3:
                    score -= 10
                    reasons.append("Kara: brak P3 (flagowiec)")

            if score > 0:
                # Jeśli wykryto symulację, dodaj flagę (nawet dla niskiego score)
                if is_simulation:
                    # GPU komputera wykryty = prawdopodobnie symulacja
                    matches.append({
                        "model": model_name + " (symulacja?)",
                        "confidence": min(score, 100),
                        "reasons": reasons + ["⚠️ GPU komputera wykryty"],
                        "raw_score": score,
                        "is_simulation": True
                    })
                else:
                    # Normalne rozpoznanie
                    matches.append({
                        "model": model_name,
                        "confidence": min(score, 100),
                        "reasons": reasons,
                        "raw_score": score,
                        "is_simulation": False
                    })
    except Exception as e:
        logger.error(f"❌ Error during heuristic scoring: {e}", exc_info=True)
        return []

    # Sortuj po confidence i zwróć top 3
    matches.sort(key=lambda x: x["confidence"], reverse=True)

    # Loguj top 3 z PEŁNYMI szczegółami punktacji
    logger.info(f"🏆 TOP 3 MATCHES (z {len(matches)} kandydatów):")
    for i, match in enumerate(matches[:3], 1):
        reasons_str = ', '.join(match['reasons']) if match['reasons'] else 'brak dopasowań'
        logger.info(f"  #{i}: {match['model']} - {match['confidence']}% | Powody: {reasons_str}")

    # Jeśli nie ma dopasowań, zaloguj to
    if not matches:
        gpu_str = gpu[:30] if gpu else "None"
        logger.warning(
            "⚠️ BRAK DOPASOWAŃ! Parametry: "
            f"W={width}, H={height}, DPR={dpr}, RAM={ram}, Hz={refresh_rate}, GPU={gpu_str}"
        )

    return matches[:3]


def calculate_weighted_match(database, target_specs):
    """
    Oblicza dopasowanie modeli z bazy do wymagań użytkownika (Weighted Scoring).
    Zwraca posortowaną listę wyników.
    """
    results = []

    for device in database:
        score = 0

        # 1. Viewport (40 pkt)
        if device.get('viewport') == target_specs.get('viewport'):
            score += 40

        # 2. DPR (30 pkt)
        if device.get('dpr') == target_specs.get('dpr'):
            score += 30

        # 3. RAM (15 pkt) - premia za posiadanie wystarczającej ilości
        # Używamy try/except na wypadek gdyby dane nie były liczbą
        try:
            if int(device.get('ram', 0)) >= int(target_specs.get('ram', 0)):
                score += 15
        except ValueError:
            pass # Ignoruj błędy konwersji

        # 4. Hz (15 pkt)
        try:
            if int(device.get('hz', 0)) >= int(target_specs.get('hz', 0)):
                score += 15
        except ValueError:
            pass

        # Dodajemy wynik do listy
        results.append({"name": device['name'], "sys_name": device['sys_name'], "score": score, "details": device})

    # Sortowanie: najwyższy wynik na górze
    return sorted(results, key=lambda x: x['score'], reverse=True)
