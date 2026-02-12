"""
SHARK v18 - Główna logika biznesowa
Zawiera algorytm dopasowania i parsowanie User-Agent.
"""
import re

from .config import logger
from .database import db # Importujemy połączenie
from .models.heuristic_db import HEURISTIC_DB # Importujemy bazę heurystyczną


def parse_device_from_ua(ua: str) -> str | None:
    """
    Parsuje identyfikator urządzenia z ciągu User-Agent.
    Obsługuje iOS i popularne urządzenia z Androidem.
    """
    if not ua or not isinstance(ua, str):
        return None
    # Ochrona przed atakami ReDoS
    if len(ua) > 1000:
        ua = ua[:1000]

    try:
        # Wzorce Regex w kolejności od najbardziej specyficznych
        patterns = {
            "iPhone": r'iPhone(\d+,\d+)',
            "iPad": r'iPad(\d+,\d+)',
            "Samsung": r'(SM-[A-Z]\d{3}[A-Z]?)',
            "Pixel": r'(Pixel \d+(?:\s+Pro)?)',
            "OnePlus": r'((?:CPH|LE|IN|NE)\d{4})',
            "Huawei": r'([A-Z]{3}-[A-Z0-9]{3,5})',
            "Xiaomi": r'Build/([A-Z0-9]{10,})', # Mniej specyficzny, na końcu
        }

        for device_type, pattern in patterns.items():
            match = re.search(pattern, ua)
            if match:
                # Dodatkowe warunki dla mniej jednoznacznych wzorców
                if device_type == "Huawei" and not ('HUAWEI' in ua.upper() or 'HONOR' in ua.upper()):
                    continue
                if device_type == "Xiaomi" and 'Xiaomi' not in ua:
                    continue
                
                # Zwróć dopasowany identyfikator
                return f"{device_type}{match.group(1)}" if device_type in ["iPhone", "iPad"] else match.group(1)

    except Exception as e:
        logger.error(f"Error parsing User-Agent: {e}")

    return None


def find_top_3_matches(width, height, refresh_rate, gpu, dpr, ram, cores):
    """
    Znajduje 3 najlepiej pasujące modele, używając ważonego algorytmu punktacji.
    """
    matches = []
    if not gpu: gpu = "" # Zabezpieczenie przed None
    gpu_lower = gpu.lower()

    is_ios = "apple" in gpu_lower or ram == -1
    is_simulation = any(keyword in gpu_lower for keyword in ["intel", "nvidia", "amd", "angle", "swiftshader", "mesa"])

    if is_simulation:
        logger.warning(f"⚠️ SIMULATION DETECTED! Desktop GPU: {gpu[:50]}")

    # Pobierz zweryfikowane modele z MongoDB, jeśli dostępne
    verified_models = {}
    if db and 'verified_models' in db.list_collection_names():
        try:
            for model_doc in db['verified_models'].find({}):
                name = model_doc.get('system_name') or model_doc.get('name')
                if name:
                    verified_models[name] = {k: v for k, v in model_doc.items() if k != '_id'}
        except Exception as e:
            logger.warning(f"Could not load verified models from DB: {e}")

    all_models = {**HEURISTIC_DB, **verified_models}
    logger.info(f"🔍 Searching in {len(all_models)} models ({len(HEURISTIC_DB)} built-in + {len(verified_models)} verified).")

    for model_name, specs in all_models.items():
        score = 0
        reasons = []

        # Sprawdzanie 'None' przed porównaniem
        if width is not None and specs.get("w") is not None:
            if specs["w"] == width:
                score += 50 if is_ios else 20
                reasons.append(f"Width: {specs['w']}px")
            elif not is_ios and abs(specs["w"] - width) <= 40:
                score += 10
                reasons.append(f"Width ~{specs['w']}px")

        if height is not None and specs.get("h") is not None:
            if specs["h"] == height:
                score += 30 if is_ios else 10
                reasons.append(f"Height: {specs['h']}px")
            elif height < specs["h"] and height > (specs["h"] - 160):
                score += 25 if is_ios else 8
                reasons.append(f"Height ~{specs['h']}px (address bar)")

        if dpr is not None and specs.get("dpr") is not None:
            if abs(specs["dpr"] - dpr) < 0.1:
                score += 20 if is_ios else 25
                reasons.append(f"DPR: {specs['dpr']}x")
            elif abs(specs["dpr"] - dpr) < 0.5:
                score += 10
                reasons.append(f"DPR ~{specs['dpr']}x")

        if refresh_rate is not None and specs.get("hz") is not None:
            if abs(specs["hz"] - refresh_rate) < 5:
                score += 5
                reasons.append(f"Hz: {specs['hz']}Hz")
            else:
                score -= 10

        if not is_ios and ram is not None and ram > 0 and specs.get("ram", -1) > 0:
            if ram >= specs["ram"] or abs(specs["ram"] - ram) <= 2:
                score += 5
                reasons.append(f"RAM: ~{specs['ram']}GB")

        if score > 0:
            match_data = {
                "model": model_name,
                "confidence": min(score, 100),
                "reasons": reasons,
                "raw_score": score,
                "is_simulation": is_simulation
            }
            if is_simulation:
                match_data["model"] += " (symulacja?)"
                match_data["reasons"].append("⚠️ Desktop GPU")
            
            matches.append(match_data)

    matches.sort(key=lambda x: x["raw_score"], reverse=True)

    if not matches:
        gpu_str = gpu[:30] if gpu else "None"
        logger.warning(f"No heuristic matches found! Params: W={width}, H={height}, DPR={dpr}, Hz={refresh_rate}, GPU={gpu_str}")

    return matches[:3]