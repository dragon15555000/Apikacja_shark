"""
SHARK v18 - Simple Logic Tests
Tests for core functionality: signature generation, device matching, etc.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.logic import build_signature, normalize_viewport, parse_device_from_ua


def test_build_signature():
    """Test signature generation without canvas_hash"""
    print("\n🧪 Test 1: build_signature()")

    # Test iPhone 11
    sig = build_signature(414, 896, 2.0, -1, 60, "apple gpu")
    expected = "414_896_2.0_-1_60_apple gpu"
    assert sig == expected, f"Expected {expected}, got {sig}"
    print(f"✅ iPhone 11 signature: {sig}")

    # Test Samsung S24
    sig = build_signature(384, 832, 2.8125, 8, 120, "adreno 750")
    expected = "384_832_2.81_8_120_adreno 750"
    assert sig == expected, f"Expected {expected}, got {sig}"
    print(f"✅ Samsung S24 signature: {sig}")

    # Test with canvas_hash (should be ignored)
    sig = build_signature(414, 896, 2.0, -1, 60, "apple gpu", "abc123")
    expected = "414_896_2.0_-1_60_apple gpu"
    assert sig == expected, f"Expected {expected}, got {sig}"
    print(f"✅ Signature ignores canvas_hash: {sig}")

    print("✅ All signature tests passed!")


def test_normalize_viewport():
    """Test viewport normalization"""
    print("\n🧪 Test 2: normalize_viewport()")

    # Test exact values
    w, h = normalize_viewport(414, 896)
    assert w == 414 and h == 896, f"Expected 414x896, got {w}x{h}"
    print(f"✅ Exact values: {w}x{h}")

    # Test small floating point noise (< 0.02) - should round
    w, h = normalize_viewport(414.01, 896.015)
    assert w == 414 and h == 896, f"Expected 414x896, got {w}x{h}"
    print(f"✅ Small noise rounded: {w}x{h}")

    # Test large differences (>= 0.02) - should NOT round
    w, h = normalize_viewport(414.5, 896.7)
    assert w == 414.5 and h == 896.7, f"Expected 414.5x896.7, got {w}x{h}"
    print(f"✅ Large differences preserved: {w}x{h}")

    # Test edge case (exactly 0.02)
    w, h = normalize_viewport(414.019, 896.019)
    assert w == 414 and h == 896, f"Expected 414x896, got {w}x{h}"
    print(f"✅ Edge case (0.019) rounded: {w}x{h}")

    print("✅ All viewport tests passed!")


def test_parse_device_from_ua():
    """Test User-Agent parsing"""
    print("\n🧪 Test 3: parse_device_from_ua()")

    # Test iPhone with identifier
    ua = "Mozilla/5.0 (iPhone14,2; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
    result = parse_device_from_ua(ua)
    assert result is not None, "Should detect iPhone"
    assert "iPhone" in result, f"Expected iPhone in result, got {result}"
    print(f"✅ iPhone detected: {result}")

    # Test Samsung with model code
    ua = "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36"
    result = parse_device_from_ua(ua)
    assert result is not None, "Should detect Samsung"
    assert "SM-S921" in result, f"Expected SM-S921 in result, got {result}"
    print(f"✅ Samsung detected: {result}")

    # Test generic iPhone (no identifier) - should return None
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
    result = parse_device_from_ua(ua)
    print(f"✅ Generic iPhone (no identifier): {result}")

    # Test unknown device
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    result = parse_device_from_ua(ua)
    assert result is None, "Should return None for desktop"
    print(f"✅ Unknown device: {result}")

    print("✅ All UA parsing tests passed!")


def test_browser_independent_signatures():
    """Test that same phone has same signature across browsers"""
    print("\n🧪 Test 4: Browser-independent signatures")

    # iPhone 11 in Chrome
    sig_chrome = build_signature(414, 896, 2.0, -1, 60, "apple gpu", "chrome_hash_123")

    # iPhone 11 in Safari
    sig_safari = build_signature(414, 896, 2.0, -1, 60, "apple gpu", "safari_hash_xyz")

    # iPhone 11 in Firefox
    sig_firefox = build_signature(414, 896, 2.0, -1, 60, "apple gpu", "firefox_hash_abc")

    assert sig_chrome == sig_safari == sig_firefox, \
        f"Signatures should be identical!\nChrome: {sig_chrome}\nSafari: {sig_safari}\nFirefox: {sig_firefox}"

    print(f"✅ Chrome:  {sig_chrome}")
    print(f"✅ Safari:  {sig_safari}")
    print(f"✅ Firefox: {sig_firefox}")
    print("✅ All three signatures are IDENTICAL! 🎉")


def test_desktop_gpu_detection():
    """Test desktop GPU detection patterns"""
    print("\n🧪 Test 5: Desktop GPU detection")

    import re
    desktopGPUs = re.compile(r'intel|nvidia|geforce|radeon|amd|quadro|intel\(r\) uhd|intel\(r\) iris|mesa', re.IGNORECASE)

    # Desktop GPUs (should match)
    desktop_gpus = [
        "Intel(R) UHD Graphics 620",
        "NVIDIA GeForce GTX 1650",
        "AMD Radeon RX 6800",
        "Intel(R) Iris(R) Xe Graphics",
        "ANGLE (Intel, Intel(R) Arc(TM) Graphics",
        "Mesa DRI Intel(R) HD Graphics"
    ]

    for gpu in desktop_gpus:
        assert desktopGPUs.search(gpu), f"Should detect desktop GPU: {gpu}"
        print(f"✅ Desktop GPU detected: {gpu}")

    # Mobile GPUs (should NOT match)
    mobile_gpus = [
        "Apple GPU",
        "Adreno 750",
        "Mali-G715",
        "PowerVR GT7600",
        "Immortalis-G715"
    ]

    for gpu in mobile_gpus:
        assert not desktopGPUs.search(gpu), f"Should NOT detect as desktop GPU: {gpu}"
        print(f"✅ Mobile GPU (not desktop): {gpu}")

    print("✅ All GPU detection tests passed!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🦈 SHARK v18 - Simple Logic Tests")
    print("=" * 60)

    try:
        test_build_signature()
        test_normalize_viewport()
        test_parse_device_from_ua()
        test_browser_independent_signatures()
        test_desktop_gpu_detection()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED! 🎉")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
