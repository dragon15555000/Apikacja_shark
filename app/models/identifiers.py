"""
SHARK v18 - Device Identifiers
Słowniki identyfikatorów urządzeń i kodów akcesoriów
"""

# Identyfikatory iPhone (z User-Agent)
STATIC_IDENTIFIERS = {
    "iPhone18,1": "iPhone 17 Pro", "iPhone18,2": "iPhone 17 Pro Max",
    "iPhone18,3": "iPhone 17", "iPhone18,4": "iPhone Air",
    "iPhone17,1": "iPhone 16 Pro", "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,3": "iPhone 16", "iPhone17,4": "iPhone 16 Plus", "iPhone17,5": "iPhone 16e",
    "iPhone16,1": "iPhone 15 Pro", "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone15,4": "iPhone 15", "iPhone15,5": "iPhone 15 Plus",
    "iPhone15,2": "iPhone 14 Pro", "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone14,7": "iPhone 14", "iPhone14,8": "iPhone 14 Plus",
    "iPhone14,5": "iPhone 13", "iPhone14,2": "iPhone 13 Pro", "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone13,2": "iPhone 12", "iPhone13,3": "iPhone 12 Pro", "iPhone13,4": "iPhone 12 Pro Max",
    "iPhone12,1": "iPhone 11", "iPhone12,3": "iPhone 11 Pro", "iPhone12,5": "iPhone 11 Pro Max"
}

# Identyfikatory Android (z User-Agent lub Build Model)
ANDROID_IDENTIFIERS = {
    # Samsung Galaxy S25 series
    "SM-S938": "Samsung Galaxy S25 Ultra", "SM-S936": "Samsung Galaxy S25+", "SM-S931": "Samsung Galaxy S25",
    # Samsung Galaxy S24 series
    "SM-S928": "Samsung Galaxy S24 Ultra", "SM-S926": "Samsung Galaxy S24+", "SM-S921": "Samsung Galaxy S24",
    # Samsung Galaxy S23 series
    "SM-S918": "Samsung Galaxy S23 Ultra", "SM-S916": "Samsung Galaxy S23+", "SM-S911": "Samsung Galaxy S23",
    # Samsung Galaxy S22 series
    "SM-S908": "Samsung Galaxy S22 Ultra", "SM-S906": "Samsung Galaxy S22+", "SM-S901": "Samsung Galaxy S22",
    # Samsung Galaxy S21 series
    "SM-G998": "Samsung Galaxy S21 Ultra", "SM-G996": "Samsung Galaxy S21+", "SM-G991": "Samsung Galaxy S21",
    "SM-G990": "Samsung Galaxy S21 FE",
    # Samsung Galaxy S20 series
    "SM-G988": "Samsung Galaxy S20 Ultra", "SM-G986": "Samsung Galaxy S20+", "SM-G981": "Samsung Galaxy S20",
    "SM-G780": "Samsung Galaxy S20 FE",
    # Samsung Galaxy S10 series
    "SM-G975": "Samsung Galaxy S10+", "SM-G973": "Samsung Galaxy S10", "SM-G970": "Samsung Galaxy S10e",
    # Samsung Galaxy A series (nowsze modele)
    "SM-A566": "Samsung Galaxy A55", "SM-A556": "Samsung Galaxy A55",
    "SM-A546": "Samsung Galaxy A54", "SM-A536": "Samsung Galaxy A53", "SM-A526": "Samsung Galaxy A52",
    "SM-A366": "Samsung Galaxy A35", "SM-A356": "Samsung Galaxy A35",
    "SM-A346": "Samsung Galaxy A34", "SM-A336": "Samsung Galaxy A33",
    "SM-A256": "Samsung Galaxy A25", "SM-A246": "Samsung Galaxy A24",
    "SM-A156": "Samsung Galaxy A15", "SM-A146": "Samsung Galaxy A14",
    # Samsung Galaxy Z series (składane)
    "SM-F958": "Samsung Galaxy Z Fold 6", "SM-F946": "Samsung Galaxy Z Fold 5",
    "SM-F936": "Samsung Galaxy Z Fold 4", "SM-F926": "Samsung Galaxy Z Fold 3",
    "SM-F751": "Samsung Galaxy Z Flip 6", "SM-F741": "Samsung Galaxy Z Flip 5",
    "SM-F721": "Samsung Galaxy Z Flip 4", "SM-F711": "Samsung Galaxy Z Flip 3",
    # Google Pixel 9 series
    "Pixel 9 Pro Fold": "Google Pixel 9 Pro Fold", "Pixel 9 Pro XL": "Google Pixel 9 Pro XL",
    "Pixel 9 Pro": "Google Pixel 9 Pro", "Pixel 9": "Google Pixel 9",
    # Google Pixel 8 series
    "Pixel 8 Pro": "Google Pixel 8 Pro", "Pixel 8": "Google Pixel 8", "Pixel 8a": "Google Pixel 8a",
    # Google Pixel 7 series
    "Pixel 7 Pro": "Google Pixel 7 Pro", "Pixel 7": "Google Pixel 7", "Pixel 7a": "Google Pixel 7a",
    # Google Pixel 6 series
    "Pixel 6 Pro": "Google Pixel 6 Pro", "Pixel 6": "Google Pixel 6", "Pixel 6a": "Google Pixel 6a",
    "Pixel 5": "Google Pixel 5", "Pixel 4a": "Google Pixel 4a",
    # Xiaomi
    "2311DRK48C": "Xiaomi 14 Pro", "23117PN0CC": "Xiaomi 14", "2304FPN6DC": "Xiaomi 13 Ultra",
    "2211133C": "Xiaomi 13 Pro", "2211133G": "Xiaomi 13", "2206123SC": "Xiaomi 12 Pro",
    "2201123G": "Xiaomi 12", "M2102K1G": "Xiaomi Mi 11", "M2007J20CG": "Xiaomi Mi 10T Pro",
    # OnePlus
    "CPH2581": "OnePlus 12", "CPH2449": "OnePlus 11", "NE2213": "OnePlus 10 Pro",
    "LE2123": "OnePlus 9 Pro", "LE2121": "OnePlus 9", "IN2023": "OnePlus 8 Pro", "IN2020": "OnePlus 8",
    # Huawei / Honor
    "ALN-L29": "Huawei P40 Pro", "ANA-NX9": "Huawei P40", "VOG-L29": "Huawei P30 Pro",
    "ELE-L29": "Huawei P30", "MAR-LX1A": "Huawei P Smart 2019",
    # Realme
    "RMX3771": "Realme 12 Pro+", "RMX3686": "Realme 11 Pro+", "RMX3581": "Realme 10 Pro+",
    # OPPO
    "CPH2551": "OPPO Find X6 Pro", "CPH2305": "OPPO Find X5 Pro",
    # Sony Xperia
    "XQ-EC54": "Sony Xperia 1 VI", "XQ-EC72": "Sony Xperia 1 VI",
    "XQ-DE54": "Sony Xperia 1 V", "XQ-DE72": "Sony Xperia 1 V",
    "XQ-CC54": "Sony Xperia 1 IV", "XQ-BC72": "Sony Xperia 1 III",
    "XQ-BT52": "Sony Xperia 5 IV", "XQ-CT54": "Sony Xperia 10 VI",
    # ASUS ROG Phone
    "ASUS_AI2401": "ASUS ROG Phone 8", "ASUS_AI2401_C": "ASUS ROG Phone 8",
    "ASUS_AI2301": "ASUS ROG Phone 7", "ASUS_AI2301_C": "ASUS ROG Phone 7",
    # Nothing Phone
    "A065": "Nothing Phone 2", "A063": "Nothing Phone 1",
    "A075": "Nothing Phone 2a",
    # Vivo / iQOO
    "V2306A": "Vivo X100 Pro", "V2324A": "Vivo X100",
    "V2307A": "iQOO 12",
}