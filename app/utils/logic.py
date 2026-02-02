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
        return ""
    gpu_lower = gpu.lower()
    gpu_lower = gpu_lower.replace("(tm)", "")
    gpu_lower = re.sub(r"[@()/,:]", " ", gpu_lower)
    gpu_lower = re.sub(r"\b(qualcomm|arm|gpu|graphics)\b", " ", gpu_lower)
    gpu_lower = re.sub(r"\s+", " ", gpu_lower).strip()
    return gpu_lower


def normalize_viewport(width, height):
    """Normalize viewport dimensions to reduce minor floating point noise."""
    exact_width = round(width) if abs(width - round(width)) < 0.02 else width
    exact_height = height
    return exact_width, exact_height


def build_signature(width, height, dpr, ram, refresh_rate, gpu, canvas_hash):
    """Build canonical AI signature string."""
    exact_width, exact_height = normalize_viewport(width, height)
    dpr_rounded = round(float(dpr), 2)
    return f"{exact_width}_{exact_height}_{dpr_rounded}_{ram}_{refresh_rate}_{gpu}_{canvas_hash}"


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

        # Samsung (SM-XXXX)
        match_samsung = re.search(r'(SM-[A-Z]\d{3}[A-Z]?)', ua)
        if match_samsung:
            return match_samsung.group(1)[:7]

        # Google Pixel
        match_pixel = re.search(r'(Pixel \d+(?:\s+Pro)?)', ua)
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
    except Exception as e:
        logger.error(f"Error parsing UA: {e}")
    return None

def find_top_3_matches(width, height, refresh_rate, gpu, dpr, ram, cores, user_agent=None):
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

    # Wykryj symulację/emulację (GPU komputera zamiast telefonu)
    is_simulation = any(keyword in gpu_lower for keyword in ["intel", "nvidia", "amd", "angle", "swiftshader", "mesa"])

    logger.info(f"📍 Weighted Scoring - OS: {'iOS' if is_ios else 'Android'}, DPR: {dpr}, RAM: {ram}, GPU: {gpu}")
    if is_simulation:
        logger.warning(f"⚠️ SYMULACJA WYKRYTA! GPU komputera: {gpu[:50]}")

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
        if specs["w"] == width:
            score += 50 if is_ios else 20
            reasons.append(f"Szerokość: {specs['w']}px")
        elif not is_ios and abs(specs["w"] - width) <= 40:
            score += 10
            reasons.append(f"Szerokość ~{specs['w']}px")

        # 3. Viewport Height (Waga: 30 iOS / 10 Android) - z tolerancją na pasek adresu
        if specs["h"] == height:
            score += 30 if is_ios else 10
            reasons.append(f"Wysokość: {specs['h']}px")
        elif height < specs["h"] and height > (specs["h"] - 160):
            # Tolerancja na pasek adresu (100-160px)
            score += 25 if is_ios else 8
            reasons.append(f"Wysokość ~{specs['h']}px (pasek adresu)")

        # 4. DPR (Waga: 20 iOS / 25 Android) - KLUCZOWE!
        if abs(specs["dpr"] - dpr) < 0.1:
            score += 20 if is_ios else 25
            reasons.append(f"DPR: {specs['dpr']}x")
        elif abs(specs["dpr"] - dpr) < 0.5:
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
        if not is_ios and ram > 0 and specs["ram"] > 0:
            # Użyj >= zamiast == bo Chrome zaokrągla RAM w dół
            if ram >= specs["ram"] or abs(specs["ram"] - ram) <= 2:
                score += 5
                reasons.append(f"RAM: ~{specs['ram']}GB")

        if score > 0:
            # Jeśli wykryto symulację, dodaj flagę
            if is_simulation and score >= 100:
                # Idealny match ale GPU komputera = prawdopodobnie symulacja
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

    # Sortuj po confidence i zwróć top 3
    matches.sort(key=lambda x: x["confidence"], reverse=True)

    # Loguj top 3 z PEŁNYMI szczegółami punktacji
    logger.info(f"🏆 TOP 3 MATCHES (z {len(matches)} kandydatów):")
    for i, match in enumerate(matches[:3], 1):
        reasons_str = ', '.join(match['reasons']) if match['reasons'] else 'brak dopasowań'
        logger.info(f"  #{i}: {match['model']} - {match['confidence']}% | Powody: {reasons_str}")

    # Jeśli nie ma dopasowań, zaloguj to
    if not matches:
        logger.warning(f"⚠️ BRAK DOPASOWAŃ! Parametry: W={width}, H={height}, DPR={dpr}, RAM={ram}, Hz={refresh_rate}, GPU={gpu[:30]}")

    return matches[:3]
