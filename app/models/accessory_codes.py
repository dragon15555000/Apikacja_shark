"""
SHARK v18 - Kody Akcesoriów
Mapowanie model → kody akcesoriów (szkło, etui)
"""

ACCESSORY_CODES = {
    # iPhone 17 series
    "iPhone 17 Pro Max": {"screen": "A1U1", "case": "A1U2"}, "iPhone 17 Pro": {"screen": "A2U1", "case": "A2U2"},
    "iPhone 17": {"screen": "A3U1", "case": "A3U2"}, "iPhone Air": {"screen": "A4U1", "case": "A4U2"},
    # iPhone 16 series
    "iPhone 16 Pro Max": {"screen": "B1U1", "case": "B1U2"}, "iPhone 16 Pro": {"screen": "B2U1", "case": "B2U2"},
    "iPhone 16": {"screen": "B3U1", "case": "B3U2"}, "iPhone 16 Plus": {"screen": "B4U1", "case": "B4U2"},
    "iPhone 16e": {"screen": "B5U1", "case": "B5U2"},
    # iPhone 15 series
    "iPhone 15 Pro Max": {"screen": "C1U1", "case": "C1U2"}, "iPhone 15 Pro": {"screen": "C2U1", "case": "C2U2"},
    "iPhone 15": {"screen": "C3U1", "case": "C3U2"}, "iPhone 15 Plus": {"screen": "C4U1", "case": "C4U2"},
    # iPhone 14 series
    "iPhone 14 Pro Max": {"screen": "D1U1", "case": "D1U2"}, "iPhone 14 Pro": {"screen": "D2U1", "case": "D2U2"},
    "iPhone 14": {"screen": "D3U1", "case": "D3U2"}, "iPhone 14 Plus": {"screen": "D4U1", "case": "D4U2"},
    # iPhone 13 series
    "iPhone 13 Pro Max": {"screen": "E1U1", "case": "E1U2"}, "iPhone 13 Pro": {"screen": "E2U1", "case": "E2U2"},
    "iPhone 13": {"screen": "E3U1", "case": "E3U2"},
    # iPhone 12 series
    "iPhone 12 Pro Max": {"screen": "F1U1", "case": "F1U2"}, "iPhone 12 Pro": {"screen": "F2U1", "case": "F2U2"},
    "iPhone 12": {"screen": "F3U1", "case": "F3U2"},
    # iPhone 11 series
    "iPhone 11 Pro Max": {"screen": "G1U1", "case": "G1U2"}, "iPhone 11 Pro": {"screen": "G2U1", "case": "G2U2"},
    "iPhone 11": {"screen": "G3U1", "case": "G3U2"},
    # Samsung Galaxy S25 series
    "Samsung Galaxy S25 Ultra": {"screen": "SS1U1", "case": "SS1U2"},
    "Samsung Galaxy S25+": {"screen": "SS2U1", "case": "SS2U2"},
    "Samsung Galaxy S25": {"screen": "SS3U1", "case": "SS3U2"},
    # Samsung Galaxy S24 series
    "Samsung Galaxy S24 Ultra": {"screen": "SA1U1", "case": "SA1U2"},
    "Samsung Galaxy S24+": {"screen": "SA2U1", "case": "SA2U2"},
    "Samsung Galaxy S24": {"screen": "SA3U1", "case": "SA3U2"},
    # Samsung Galaxy S23 series
    "Samsung Galaxy S23 Ultra": {"screen": "SB1U1", "case": "SB1U2"},
    "Samsung Galaxy S23+": {"screen": "SB2U1", "case": "SB2U2"},
    "Samsung Galaxy S23": {"screen": "SB3U1", "case": "SB3U2"},
    # Samsung Galaxy S22 series
    "Samsung Galaxy S22 Ultra": {"screen": "SC1U1", "case": "SC1U2"},
    "Samsung Galaxy S22+": {"screen": "SC2U1", "case": "SC2U2"},
    "Samsung Galaxy S22": {"screen": "SC3U1", "case": "SC3U2"},
    # Samsung Galaxy S21 series
    "Samsung Galaxy S21 Ultra": {"screen": "SD1U1", "case": "SD1U2"},
    "Samsung Galaxy S21+": {"screen": "SD2U1", "case": "SD2U2"},
    "Samsung Galaxy S21": {"screen": "SD3U1", "case": "SD3U2"},
    "Samsung Galaxy S21 FE": {"screen": "SD4U1", "case": "SD4U2"},
    # Samsung Galaxy S20 series
    "Samsung Galaxy S20 Ultra": {"screen": "SE1U1", "case": "SE1U2"},
    "Samsung Galaxy S20+": {"screen": "SE2U1", "case": "SE2U2"},
    "Samsung Galaxy S20": {"screen": "SE3U1", "case": "SE3U2"},
    "Samsung Galaxy S20 FE": {"screen": "SE4U1", "case": "SE4U2"},
    # Samsung Galaxy S10 series
    "Samsung Galaxy S10+": {"screen": "SF1U1", "case": "SF1U2"},
    "Samsung Galaxy S10": {"screen": "SF2U1", "case": "SF2U2"},
    "Samsung Galaxy S10e": {"screen": "SF3U1", "case": "SF3U2"},
    # Samsung Galaxy A series
    "Samsung Galaxy A55": {"screen": "AA0U1", "case": "AA0U2"},
    "Samsung Galaxy A54": {"screen": "AA1U1", "case": "AA1U2"},
    "Samsung Galaxy A53": {"screen": "AA2U1", "case": "AA2U2"},
    "Samsung Galaxy A52": {"screen": "AA3U1", "case": "AA3U2"},
    "Samsung Galaxy A35": {"screen": "AB0U1", "case": "AB0U2"},
    "Samsung Galaxy A34": {"screen": "AA4U1", "case": "AA4U2"},
    "Samsung Galaxy A33": {"screen": "AA5U1", "case": "AA5U2"},
    "Samsung Galaxy A25": {"screen": "AC0U1", "case": "AC0U2"},
    "Samsung Galaxy A24": {"screen": "AC1U1", "case": "AC1U2"},
    "Samsung Galaxy A15": {"screen": "AD0U1", "case": "AD0U2"},
    "Samsung Galaxy A14": {"screen": "AD1U1", "case": "AD1U2"},
    # Samsung Galaxy Z series
    "Samsung Galaxy Z Fold 6": {"screen": "ZF0U1", "case": "ZF0U2"},
    "Samsung Galaxy Z Fold 5": {"screen": "ZF1U1", "case": "ZF1U2"},
    "Samsung Galaxy Z Fold 4": {"screen": "ZF2U1", "case": "ZF2U2"},
    "Samsung Galaxy Z Fold 3": {"screen": "ZF3U1", "case": "ZF3U2"},
    "Samsung Galaxy Z Flip 6": {"screen": "ZP0U1", "case": "ZP0U2"},
    "Samsung Galaxy Z Flip 5": {"screen": "ZP1U1", "case": "ZP1U2"},
    "Samsung Galaxy Z Flip 4": {"screen": "ZP2U1", "case": "ZP2U2"},
    "Samsung Galaxy Z Flip 3": {"screen": "ZP3U1", "case": "ZP3U2"},
    # Google Pixel 9 series
    "Google Pixel 9 Pro Fold": {"screen": "GP0U1", "case": "GP0U2"},
    "Google Pixel 9 Pro XL": {"screen": "GP0U3", "case": "GP0U4"},
    "Google Pixel 9 Pro": {"screen": "GP0U5", "case": "GP0U6"},
    "Google Pixel 9": {"screen": "GP0U7", "case": "GP0U8"},
    # Google Pixel 8 series
    "Google Pixel 8 Pro": {"screen": "GP1U1", "case": "GP1U2"},
    "Google Pixel 8": {"screen": "GP2U1", "case": "GP2U2"},
    "Google Pixel 8a": {"screen": "GP2U3", "case": "GP2U4"},
    # Google Pixel 7 series
    "Google Pixel 7 Pro": {"screen": "GP3U1", "case": "GP3U2"},
    "Google Pixel 7": {"screen": "GP4U1", "case": "GP4U2"},
    "Google Pixel 7a": {"screen": "GP4U3", "case": "GP4U4"},
    # Google Pixel 6 series
    "Google Pixel 6 Pro": {"screen": "GP5U1", "case": "GP5U2"},
    "Google Pixel 6": {"screen": "GP6U1", "case": "GP6U2"},
    "Google Pixel 6a": {"screen": "GP6U3", "case": "GP6U4"},
    "Google Pixel 5": {"screen": "GP7U1", "case": "GP7U2"},
    "Google Pixel 4a": {"screen": "GP8U1", "case": "GP8U2"},
    # Xiaomi
    "Xiaomi 14 Pro": {"screen": "XM1U1", "case": "XM1U2"}, "Xiaomi 14": {"screen": "XM2U1", "case": "XM2U2"},
    "Xiaomi 13 Ultra": {"screen": "XM3U1", "case": "XM3U2"}, "Xiaomi 13 Pro": {"screen": "XM4U1", "case": "XM4U2"},
    "Xiaomi 13": {"screen": "XM5U1", "case": "XM5U2"}, "Xiaomi 12 Pro": {"screen": "XM6U1", "case": "XM6U2"},
    "Xiaomi 12": {"screen": "XM7U1", "case": "XM7U2"}, "Xiaomi Mi 11": {"screen": "XM8U1", "case": "XM8U2"},
    "Xiaomi Mi 10T Pro": {"screen": "XM9U1", "case": "XM9U2"},
    # OnePlus
    "OnePlus 12": {"screen": "OP1U1", "case": "OP1U2"}, "OnePlus 11": {"screen": "OP2U1", "case": "OP2U2"},
    "OnePlus 10 Pro": {"screen": "OP3U1", "case": "OP3U2"}, "OnePlus 9 Pro": {"screen": "OP4U1", "case": "OP4U2"},
    "OnePlus 9": {"screen": "OP5U1", "case": "OP5U2"}, "OnePlus 8 Pro": {"screen": "OP6U1", "case": "OP6U2"},
    "OnePlus 8": {"screen": "OP7U1", "case": "OP7U2"},
    # Huawei
    "Huawei P40 Pro": {"screen": "HW1U1", "case": "HW1U2"}, "Huawei P40": {"screen": "HW2U1", "case": "HW2U2"},
    "Huawei P30 Pro": {"screen": "HW3U1", "case": "HW3U2"}, "Huawei P30": {"screen": "HW4U1", "case": "HW4U2"},
    "Huawei P Smart 2019": {"screen": "HW5U1", "case": "HW5U2"},
    # Motorola
    "Motorola Edge 50 Pro": {"screen": "MT1U1", "case": "MT1U2"},
    "Motorola Edge 50": {"screen": "MT2U1", "case": "MT2U2"},
    "Motorola Edge 40 Pro": {"screen": "MT3U1", "case": "MT3U2"},
    "Motorola Moto G84": {"screen": "MT4U1", "case": "MT4U2"},
    # Realme
    "Realme 12 Pro+": {"screen": "RM1U1", "case": "RM1U2"},
    "Realme 11 Pro+": {"screen": "RM2U1", "case": "RM2U2"},
    "Realme 10 Pro+": {"screen": "RM3U1", "case": "RM3U2"},
    # OPPO
    "OPPO Find X6 Pro": {"screen": "OP_X1U1", "case": "OP_X1U2"},
    "OPPO Find X5 Pro": {"screen": "OP_X2U1", "case": "OP_X2U2"},
    # Samsung Galaxy S24 FE
    "Samsung Galaxy S24 FE": {"screen": "SF4U1", "case": "SF4U2"},
    # Sony Xperia
    "Sony Xperia 1 VI": {"screen": "SX1U1", "case": "SX1U2"},
    "Sony Xperia 1 V": {"screen": "SX2U1", "case": "SX2U2"},
    "Sony Xperia 1 IV": {"screen": "SX3U1", "case": "SX3U2"},
    "Sony Xperia 1 III": {"screen": "SX4U1", "case": "SX4U2"},
    "Sony Xperia 5 IV": {"screen": "SX5U1", "case": "SX5U2"},
    "Sony Xperia 10 VI": {"screen": "SX6U1", "case": "SX6U2"},
    # ASUS ROG Phone
    "ASUS ROG Phone 8": {"screen": "AR8U1", "case": "AR8U2"},
    "ASUS ROG Phone 7": {"screen": "AR7U1", "case": "AR7U2"},
    # Nothing Phone
    "Nothing Phone 2": {"screen": "NP2U1", "case": "NP2U2"},
    "Nothing Phone 2a": {"screen": "NP3U1", "case": "NP3U2"},
    "Nothing Phone 1": {"screen": "NP1U1", "case": "NP1U2"},
    # Vivo / iQOO
    "Vivo X100 Pro": {"screen": "VV1U1", "case": "VV1U2"},
    "Vivo X100": {"screen": "VV2U1", "case": "VV2U2"},
    "iQOO 12": {"screen": "IQ1U1", "case": "IQ1U2"},
}
