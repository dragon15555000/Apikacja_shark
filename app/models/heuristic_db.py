"""
SHARK v18 - Baza Heurystyczna
Zawiera sprawdzone parametry dla rzeczywistych urządzeń.
"""

HEURISTIC_DB = {
    # iPhone - SPRAWDZONE (z JSON) - iOS nie ma Display Zoom, więc tylko domyślne wartości
    # gamut: "p3" = Display P3 (iPhone 12+), brak = sRGB (iPhone 11 i starsze)
    "iPhone 16 Pro Max": {"w": 440, "h": 956, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 16 Pro": {"w": 402, "h": 874, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 16": {"w": 393, "h": 852, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 15 Pro Max": {"w": 430, "h": 932, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 15 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 14 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 13": {"w": 390, "h": 844, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 13 Pro": {"w": 390, "h": 844, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 13 Pro Max": {"w": 428, "h": 926, "hz": 120, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 12": {"w": 390, "h": 844, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 12 Pro": {"w": 390, "h": 844, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 12 Pro Max": {"w": 428, "h": 926, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1, "gamut": "p3"},
    "iPhone 11": {"w": 414, "h": 896, "hz": 60, "gpu": "apple gpu", "dpr": 2.0, "ram": -1},
    "iPhone 11 Pro": {"w": 375, "h": 812, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},
    "iPhone 11 Pro Max": {"w": 414, "h": 896, "hz": 60, "gpu": "apple gpu", "dpr": 3.0, "ram": -1},

    # Samsung S24 Ultra - DOMYŚLNY + Display Zoom variants
    "Samsung Galaxy S24 Ultra": {"w": 384, "h": 824, "hz": 120, "gpu": "adreno 750", "dpr": 3.75, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S24 Ultra (Zoom -1)": {"w": 411, "h": 882, "hz": 120, "gpu": "adreno 750", "dpr": 3.5, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S24 Ultra (Zoom +1)": {"w": 360, "h": 772, "hz": 120, "gpu": "adreno 750", "dpr": 4.0, "ram": 8, "gamut": "p3"},

    # Samsung S24+ - DOMYŚLNY + Display Zoom variants
    "Samsung Galaxy S24+": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 750", "dpr": 2.8125, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S24+ (Zoom -1)": {"w": 411, "h": 891, "hz": 120, "gpu": "adreno 750", "dpr": 2.625, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S24+ (Zoom +1)": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno 750", "dpr": 3.0, "ram": 8, "gamut": "p3"},

    # Samsung S24 - DOMYŚLNY + Display Zoom variants
    "Samsung Galaxy S24": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno 750", "dpr": 3.0, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S24 (Zoom -1)": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 750", "dpr": 2.8125, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S24 (Zoom +1)": {"w": 340, "h": 736, "hz": 120, "gpu": "adreno 750", "dpr": 3.2, "ram": 8, "gamut": "p3"},

    # Samsung S23 Ultra - DOMYŚLNY + Display Zoom variants
    "Samsung Galaxy S23 Ultra": {"w": 384, "h": 824, "hz": 120, "gpu": "adreno 740", "dpr": 3.75, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S23 Ultra (Zoom -1)": {"w": 411, "h": 882, "hz": 120, "gpu": "adreno 740", "dpr": 3.5, "ram": 8, "gamut": "p3"},
    "Samsung Galaxy S23 Ultra (Zoom +1)": {"w": 360, "h": 772, "hz": 120, "gpu": "adreno 740", "dpr": 4.0, "ram": 8, "gamut": "p3"},

    # Google Pixel - SPRAWDZONE (z JSON)
    "Google Pixel 8 Pro": {"w": 448, "h": 998, "hz": 120, "gpu": "mali-g715", "dpr": 3.0, "ram": 8, "gamut": "p3"},
    "Google Pixel 8 Pro (Zoom -1)": {"w": 480, "h": 1070, "hz": 120, "gpu": "mali-g715", "dpr": 2.8, "ram": 8, "gamut": "p3"},
    "Google Pixel 8 Pro (Zoom +1)": {"w": 420, "h": 936, "hz": 120, "gpu": "mali-g715", "dpr": 3.2, "ram": 8, "gamut": "p3"},

    "Google Pixel 7 Pro": {"w": 412, "h": 892, "hz": 120, "gpu": "mali-g710", "dpr": 3.5, "ram": 8, "gamut": "p3"},
    "Google Pixel 7 Pro (Zoom -1)": {"w": 440, "h": 953, "hz": 120, "gpu": "mali-g710", "dpr": 3.3, "ram": 8, "gamut": "p3"},
    "Google Pixel 7 Pro (Zoom +1)": {"w": 384, "h": 832, "hz": 120, "gpu": "mali-g710", "dpr": 3.75, "ram": 8, "gamut": "p3"},

    # Xiaomi - SPRAWDZONE (z JSON)
    "Xiaomi 14 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 750", "dpr": 3.5, "ram": 8, "gamut": "p3"},
    "Xiaomi 14 Pro (Zoom -1)": {"w": 440, "h": 978, "hz": 120, "gpu": "adreno 750", "dpr": 3.3, "ram": 8, "gamut": "p3"},
    "Xiaomi 14 Pro (Zoom +1)": {"w": 384, "h": 853, "hz": 120, "gpu": "adreno 750", "dpr": 3.75, "ram": 8, "gamut": "p3"},

    "Xiaomi 13 Ultra": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 740", "dpr": 3.5, "ram": 8, "gamut": "p3"},
    "Xiaomi 13 Ultra (Zoom -1)": {"w": 440, "h": 978, "hz": 120, "gpu": "adreno 740", "dpr": 3.3, "ram": 8, "gamut": "p3"},
    "Xiaomi 13 Ultra (Zoom +1)": {"w": 384, "h": 853, "hz": 120, "gpu": "adreno 740", "dpr": 3.75, "ram": 8, "gamut": "p3"},

    # Motorola - dodatkowe modele
    "Motorola Edge 50 Pro": {"w": 412, "h": 915, "hz": 144, "gpu": "adreno 735", "dpr": 2.625, "ram": 12, "gamut": "p3"},
    "Motorola Edge 50": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 732", "dpr": 2.625, "ram": 8},
    "Motorola Edge 40 Pro": {"w": 412, "h": 915, "hz": 165, "gpu": "adreno 740", "dpr": 2.625, "ram": 12, "gamut": "p3"},
    "Motorola Moto G84": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 619", "dpr": 2.4, "ram": 8},

    # Samsung Galaxy S25 series (Snapdragon 8 Elite - Adreno 830)
    "Samsung Galaxy S25 Ultra": {"w": 384, "h": 824, "hz": 120, "gpu": "adreno 830", "dpr": 3.75, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25 Ultra (Zoom -1)": {"w": 411, "h": 882, "hz": 120, "gpu": "adreno 830", "dpr": 3.5, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25 Ultra (Zoom +1)": {"w": 360, "h": 772, "hz": 120, "gpu": "adreno 830", "dpr": 4.0, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25+": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 830", "dpr": 2.8125, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25+ (Zoom -1)": {"w": 411, "h": 891, "hz": 120, "gpu": "adreno 830", "dpr": 2.625, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25+ (Zoom +1)": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno 830", "dpr": 3.0, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno 830", "dpr": 3.0, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25 (Zoom -1)": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 830", "dpr": 2.8125, "ram": 12, "gamut": "p3"},
    "Samsung Galaxy S25 (Zoom +1)": {"w": 340, "h": 736, "hz": 120, "gpu": "adreno 830", "dpr": 3.2, "ram": 12, "gamut": "p3"},

    # Samsung Galaxy S24 FE (Exynos 2500 / Xclipse 950)
    "Samsung Galaxy S24 FE": {"w": 360, "h": 780, "hz": 120, "gpu": "xclipse 950", "dpr": 3.0, "ram": 8, "gamut": "p3"},

    # Samsung Galaxy S21 FE / S20 FE
    "Samsung Galaxy S21 FE": {"w": 360, "h": 800, "hz": 120, "gpu": "adreno 660", "dpr": 2.8125, "ram": 6, "gamut": "p3"},
    "Samsung Galaxy S20 FE": {"w": 360, "h": 800, "hz": 120, "gpu": "adreno 650", "dpr": 2.8125, "ram": 6, "gamut": "p3"},

    # Samsung Galaxy A55 / A35
    "Samsung Galaxy A55": {"w": 384, "h": 832, "hz": 120, "gpu": "xclipse 530", "dpr": 2.8125, "ram": 8},
    "Samsung Galaxy A35": {"w": 360, "h": 780, "hz": 120, "gpu": "mali-g68", "dpr": 3.0, "ram": 6},

    # Google Pixel 9 series (Tensor G4 - Mali-G715)
    "Google Pixel 9 Pro XL": {"w": 448, "h": 998, "hz": 120, "gpu": "mali-g715", "dpr": 3.0, "ram": 16, "gamut": "p3"},
    "Google Pixel 9 Pro": {"w": 412, "h": 915, "hz": 120, "gpu": "mali-g715", "dpr": 2.625, "ram": 16, "gamut": "p3"},
    "Google Pixel 9": {"w": 412, "h": 915, "hz": 120, "gpu": "mali-g715", "dpr": 2.625, "ram": 12, "gamut": "p3"},

    # Google Pixel 8a
    "Google Pixel 8a": {"w": 412, "h": 892, "hz": 120, "gpu": "mali-g715", "dpr": 2.625, "ram": 8, "gamut": "p3"},

    # Google Pixel 7a
    "Google Pixel 7a": {"w": 412, "h": 892, "hz": 90, "gpu": "mali-g710", "dpr": 2.9, "ram": 8},

    # OnePlus 12
    "OnePlus 12": {"w": 412, "h": 919, "hz": 120, "gpu": "adreno 750", "dpr": 3.0, "ram": 12, "gamut": "p3"},

    # Realme
    "Realme 12 Pro+": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 695", "dpr": 2.625, "ram": 8, "gamut": "p3"},

    # Nothing Phone
    "Nothing Phone 2": {"w": 412, "h": 915, "hz": 120, "gpu": "adreno 730", "dpr": 2.625, "ram": 8, "gamut": "p3"},
    "Nothing Phone 2a": {"w": 412, "h": 892, "hz": 120, "gpu": "mali-g610", "dpr": 2.625, "ram": 8},
    "Nothing Phone 1": {"w": 393, "h": 851, "hz": 120, "gpu": "adreno 730", "dpr": 2.625, "ram": 8},

    # Sony Xperia
    "Sony Xperia 1 VI": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 750", "dpr": 2.625, "ram": 12, "gamut": "p3"},
    "Sony Xperia 1 V": {"w": 384, "h": 832, "hz": 120, "gpu": "adreno 740", "dpr": 2.625, "ram": 12, "gamut": "p3"},
    "Sony Xperia 5 IV": {"w": 360, "h": 780, "hz": 120, "gpu": "adreno 730", "dpr": 2.625, "ram": 8, "gamut": "p3"},

    # ASUS ROG Phone
    "ASUS ROG Phone 8": {"w": 402, "h": 874, "hz": 165, "gpu": "adreno 750", "dpr": 3.0, "ram": 12, "gamut": "p3"},
    "ASUS ROG Phone 7": {"w": 393, "h": 851, "hz": 165, "gpu": "adreno 740", "dpr": 3.0, "ram": 12, "gamut": "p3"},

    # Vivo / iQOO
    "Vivo X100 Pro": {"w": 393, "h": 852, "hz": 120, "gpu": "adreno 750", "dpr": 3.0, "ram": 12, "gamut": "p3"},
    "iQOO 12": {"w": 393, "h": 851, "hz": 144, "gpu": "adreno 750", "dpr": 3.0, "ram": 12, "gamut": "p3"},
}