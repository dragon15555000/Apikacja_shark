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
        # iPhone / iPad
        m = re.search(r'iPhone(\d+,\d+)', ua)
        if m:
            return "iPhone" + m.group(1)
        m = re.search(r'iPad(\d+,\d+)', ua)
        if m:
            return "iPad" + m.group(1)

        # Samsung (SM-XXXX) — obsługuje 3 i 4-cyfrowe kody, usuwa sufiks regionu
        m = re.search(r'(SM-[A-Z]\d{3,4}[A-Z]?)', ua)
        if m:
            code = m.group(1)
            if len(code) > 7 and code[-1].isalpha():
                code = code[:-1]  # Usuń literę regionu (np. SM-S938B → SM-S938)
            return code[:8]

        # Google Pixel — obsługuje: Pixel 9, Pixel 9a, Pixel 9 Pro, Pixel 9 Pro XL, Pixel 9 Pro Fold, Pixel 9 Fold, Pixel 8a
        m = re.search(r'(Pixel \d+(?:a)?(?:\s+(?:Pro(?:\s+(?:XL|Fold))?|Fold|FE))?)', ua)
        if m:
            return m.group(1)

        # OnePlus / Realme (CPH codes)
        m = re.search(r'(CPH\d{4})', ua)
        if m:
            return m.group(1)

        # OnePlus (LE/IN/NE codes)
        m = re.search(r'((?:LE|IN|NE)\d{4})', ua)
        if m:
            return m.group(1)

        # Sony Xperia (XQ-XXNN)
        m = re.search(r'(XQ-[A-Z]{2}\d{2})', ua)
        if m:
            return m.group(1)

        # ASUS ROG Phone (ASUS_XXXXXX)
        m = re.search(r'(ASUS_[A-Z0-9]+)', ua)
        if m:
            return m.group(1)

        # Nothing Phone (A063, A065, A075)
        if 'nothing' in ua.lower():
            m = re.search(r'\b(A06[359]|A07[5])\b', ua)
            if m:
                return m.group(1)

        # Vivo / iQOO
        if 'vivo' in ua.lower() or 'iqoo' in ua.lower():
            m = re.search(r'\b(V\d{4}[A-Z])\b', ua)
            if m:
                return m.group(1)

        # Realme (RMX codes)
        m = re.search(r'(RMX\d{4})', ua)
        if m:
            return m.group(1)

        # Huawei / Honor
        m = re.search(r'([A-Z]{3}-[A-Z0-9]{3,5})', ua)
        if m and ('HUAWEI' in ua.upper() or 'HONOR' in ua.upper()):
            return m.group(1)

        # Motorola (XT codes)
        m = re.search(r'(XT\d{4})', ua)
        if m:
            return m.group(1)

        # Xiaomi Build code
        m = re.search(r'Build/([A-Z0-9]{10,})', ua)
        if m and 'Xiaomi' in ua:
            return m.group(1)[:12]

    except Exception as e:
        logger.error(f"Error parsing User-Agent: {e}")

    return None


def find_top_3_matches(width, height, refresh_rate, gpu, dpr, ram, cores, user_agent=None, color_gamut=None):
    """
    Znajduje 3 najlepiej pasujące modele, używając ważonego algorytmu punktacji.
    """
    matches = []
    if not gpu: gpu = "" # Zabezpieczenie przed None
    gpu_lower = gpu.lower()

    # Wykryj OS na podstawie UA lub GPU
    ua_lower = (user_agent or "").lower()
    if "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower or "apple" in gpu_lower:
        is_ios = True
    elif "android" in ua_lower:
        is_ios = False
    else:
        is_ios = ram == -1  # fallback: iOS zwraca -1

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

        # 1. GPU match (Android only, waga: 40)
        if not is_ios and specs.get("gpu") and gpu_lower:
            spec_gpu = specs["gpu"].lower()
            spec_parts = [p for p in spec_gpu.split() if len(p) > 2]
            if spec_parts and all(p in gpu_lower for p in spec_parts):
                score += 40
                reasons.append(f"GPU: {specs['gpu']}")
            elif spec_gpu and spec_gpu in gpu_lower:
                score += 40
                reasons.append(f"GPU: {specs['gpu']}")

        # 2. Viewport Width (waga: 50 iOS / 20 Android)
        if width is not None and specs.get("w") is not None:
            if specs["w"] == width:
                score += 50 if is_ios else 20
                reasons.append(f"Width: {specs['w']}px")
            elif not is_ios and abs(specs["w"] - width) <= 40:
                score += 10
                reasons.append(f"Width ~{specs['w']}px")

        # 3. Viewport Height (waga: 30 iOS / 10 Android) z tolerancją paska adresu
        if height is not None and specs.get("h") is not None:
            if specs["h"] == height:
                score += 30 if is_ios else 10
                reasons.append(f"Height: {specs['h']}px")
            elif height < specs["h"] and height > (specs["h"] - 160):
                score += 25 if is_ios else 8
                reasons.append(f"Height ~{specs['h']}px (address bar)")

        # 4. DPR (waga: 20 iOS / 25 Android)
        if dpr is not None and specs.get("dpr") is not None:
            if abs(specs["dpr"] - dpr) < 0.1:
                score += 20 if is_ios else 25
                reasons.append(f"DPR: {specs['dpr']}x")
            elif abs(specs["dpr"] - dpr) < 0.5:
                score += 10
                reasons.append(f"DPR ~{specs['dpr']}x")

        # 5. Hz (bonus/kara)
        if refresh_rate is not None and specs.get("hz") is not None:
            if abs(specs["hz"] - refresh_rate) < 5:
                score += 15 if is_ios else 5
                reasons.append(f"Hz: {specs['hz']}Hz")
            else:
                score -= 20 if is_ios else 10

        # 6. RAM (Android only, waga: 5)
        if not is_ios and ram is not None and ram > 0 and specs.get("ram", -1) > 0:
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