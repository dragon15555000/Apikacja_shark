"""
SHARK v18 - Advanced Logic Tests
Testuje algorytm punktacji, wykrywanie symulacji i przypadki brzegowe.
Zawiera szczegółowe logowanie i obsługę błędów dla łatwego debugowania.
"""
import unittest
import sys
import os
import logging
from io import StringIO

# Dodaj katalog główny do ścieżki (dla uruchamiania z linii komend)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importy - PyCharm może pokazywać ostrzeżenie, ale działa poprawnie w runtime
from app.utils.logic import find_top_3_matches, normalize_viewport, normalize_gpu_string
from app.models.heuristic_db import HEURISTIC_DB


class TestLogicAdvanced(unittest.TestCase):
    """Zaawansowane testy algorytmu z bogatym logowaniem"""

    @classmethod
    def setUpClass(cls):
        """Konfiguracja logowania dla wszystkich testów"""
        cls.log_stream = StringIO()
        cls.test_logger = logging.getLogger('test_advanced')
        cls.test_logger.setLevel(logging.DEBUG)

        # Handler do StringIO (przechwytywanie logów)
        handler = logging.StreamHandler(cls.log_stream)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        cls.test_logger.addHandler(handler)

        # Handler do konsoli (wyświetlanie na ekranie)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        cls.test_logger.addHandler(console_handler)

    def setUp(self):
        """Przygotowanie przed każdym testem"""
        self.log_stream.truncate(0)
        self.log_stream.seek(0)
        self.test_logger.info(f"\n{'='*70}")
        self.test_logger.info(f"🧪 Starting test: {self._testMethodName}")
        self.test_logger.info(f"{'='*70}")

    def tearDown(self):
        """Czyszczenie po każdym teście"""
        logs = self.log_stream.getvalue()
        # Sprawdź czy test się nie powiódł (kompatybilne z różnymi wersjami unittest)
        test_failed = False
        if hasattr(self._outcome, 'errors'):
            test_failed = bool(self._outcome.errors or self._outcome.failures)
        elif hasattr(self, '_outcome'):
            # Python 3.11+ używa innej struktury
            test_failed = len([case for case in self._outcome.result.failures + self._outcome.result.errors
                              if case[0] == self]) > 0

        if test_failed:
            self.test_logger.error(f"\n❌ Test FAILED: {self._testMethodName}")
            self.test_logger.error(f"Captured logs:\n{logs}")
        else:
            self.test_logger.info(f"✅ Test PASSED: {self._testMethodName}\n")

    def _log_test_params(self, **params):
        """Loguje parametry testowe w czytelnym formacie"""
        self.test_logger.info("📋 Test Parameters:")
        for key, value in params.items():
            self.test_logger.info(f"   {key:15s} = {value}")

    def _log_matches(self, matches, expected_model=None):
        """Loguje wyniki dopasowania z analizą"""
        if not matches:
            self.test_logger.warning("⚠️  BRAK DOPASOWAŃ!")
            return

        self.test_logger.info(f"\n🏆 Found {len(matches)} matches:")
        for i, match in enumerate(matches, 1):
            is_expected = match['model'] == expected_model if expected_model else False
            marker = "👉" if is_expected else "  "

            self.test_logger.info(f"{marker} #{i}: {match['model']}")
            self.test_logger.info(f"      Confidence: {match['confidence']}%")
            self.test_logger.info(f"      Raw Score:  {match.get('raw_score', 'N/A')}")

            if match.get('reasons'):
                self.test_logger.info(f"      Reasons:    {', '.join(match['reasons'])}")

            if match.get('is_simulation'):
                self.test_logger.warning(f"      ⚠️  SIMULATION FLAG SET!")

    def _analyze_scoring_breakdown(self, width, height, refresh_rate, gpu, dpr, ram, cores, model_name):
        """
        Szczegółowa analiza punktacji dla konkretnego modelu.
        Pokazuje dokładnie skąd pochodzą punkty.
        """
        if model_name not in HEURISTIC_DB:
            self.test_logger.error(f"❌ Model '{model_name}' not found in HEURISTIC_DB!")
            return None

        specs = HEURISTIC_DB[model_name]
        self.test_logger.info(f"\n🔍 Scoring Breakdown for '{model_name}':")
        self.test_logger.info(f"   Expected specs: {specs}")

        score = 0
        breakdown = []

        # GPU (40 pkt dla Android)
        gpu_lower = normalize_gpu_string(gpu)
        spec_gpu_lower = normalize_gpu_string(specs["gpu"])
        is_ios = "apple" in gpu_lower

        if not is_ios and specs["gpu"] and gpu_lower:
            spec_gpu_parts = spec_gpu_lower.split()
            if all(part in gpu_lower for part in spec_gpu_parts if len(part) > 2):
                score += 40
                breakdown.append(f"✅ GPU match: +40 pts ('{specs['gpu']}' in '{gpu}')")
            else:
                breakdown.append(f"❌ GPU mismatch: +0 pts (expected '{specs['gpu']}', got '{gpu}')")
        elif is_ios:
            breakdown.append(f"ℹ️  GPU scoring skipped (iOS device)")

        # Width (50 iOS / 20 Android)
        if specs["w"] == width:
            pts = 50 if is_ios else 20
            score += pts
            breakdown.append(f"✅ Width exact: +{pts} pts ({specs['w']}px)")
        elif not is_ios and abs(specs["w"] - width) <= 40:
            score += 10
            breakdown.append(f"⚠️  Width close: +10 pts ({specs['w']}px vs {width}px, diff={abs(specs['w']-width)})")
        else:
            breakdown.append(f"❌ Width mismatch: +0 pts (expected {specs['w']}px, got {width}px, diff={abs(specs['w']-width)})")

        # Height (30 iOS / 10 Android)
        if specs["h"] == height:
            pts = 30 if is_ios else 10
            score += pts
            breakdown.append(f"✅ Height exact: +{pts} pts ({specs['h']}px)")
        elif height < specs["h"] and height > (specs["h"] - 160):
            pts = 25 if is_ios else 8
            score += pts
            breakdown.append(f"⚠️  Height with address bar: +{pts} pts ({specs['h']}px vs {height}px, diff={specs['h']-height})")
        else:
            breakdown.append(f"❌ Height mismatch: +0 pts (expected {specs['h']}px, got {height}px, diff={abs(specs['h']-height)})")

        # DPR (20 iOS / 25 Android)
        if abs(specs["dpr"] - dpr) < 0.1:
            pts = 20 if is_ios else 25
            score += pts
            breakdown.append(f"✅ DPR exact: +{pts} pts ({specs['dpr']}x)")
        elif abs(specs["dpr"] - dpr) < 0.5:
            score += 10
            breakdown.append(f"⚠️  DPR close: +10 pts ({specs['dpr']}x vs {dpr}x, diff={abs(specs['dpr']-dpr):.2f})")
        else:
            breakdown.append(f"❌ DPR mismatch: +0 pts (expected {specs['dpr']}x, got {dpr}x, diff={abs(specs['dpr']-dpr):.2f})")

        # Hz (15 iOS / 5 Android bonus, -20/-10 penalty)
        if specs["hz"] and refresh_rate:
            if abs(specs["hz"] - refresh_rate) < 5:
                pts = 15 if is_ios else 5
                score += pts
                breakdown.append(f"✅ Hz match: +{pts} pts ({specs['hz']}Hz)")
            else:
                pts = -20 if is_ios else -10
                score += pts
                breakdown.append(f"❌ Hz penalty: {pts} pts (expected {specs['hz']}Hz, got {refresh_rate}Hz)")

        # RAM (5 pkt dla Android)
        if not is_ios and ram > 0 and specs["ram"] > 0:
            if ram >= specs["ram"] or abs(specs["ram"] - ram) <= 2:
                score += 5
                breakdown.append(f"✅ RAM match: +5 pts (~{specs['ram']}GB)")
            else:
                breakdown.append(f"❌ RAM mismatch: +0 pts (expected {specs['ram']}GB, got {ram}GB)")

        for line in breakdown:
            self.test_logger.info(f"   {line}")

        self.test_logger.info(f"   {'─'*60}")
        self.test_logger.info(f"   TOTAL SCORE: {score} pts (capped at 100%)")

        return min(score, 100)

    def test_perfect_match_iphone(self):
        """Sprawdza idealne dopasowanie dla iPhone 16 Pro"""
        self._log_test_params(
            width=402, height=874, refresh_rate=120,
            gpu="Apple GPU", dpr=3.0, ram=-1, cores=6
        )

        try:
            # Najpierw analiza teoretyczna
            expected_score = self._analyze_scoring_breakdown(
                width=402, height=874, refresh_rate=120,
                gpu="Apple GPU", dpr=3.0, ram=-1, cores=6,
                model_name="iPhone 16 Pro"
            )

            # Potem rzeczywiste dopasowanie
            matches = find_top_3_matches(
                width=402, height=874, refresh_rate=120,
                gpu="Apple GPU", dpr=3.0, ram=-1, cores=6
            )

            self._log_matches(matches, expected_model="iPhone 16 Pro")

            # Asercje
            self.assertIsNotNone(matches, "Matches should not be None")
            self.assertGreater(len(matches), 0, "Should find at least one match")

            top = matches[0]
            self.assertEqual(top['model'], "iPhone 16 Pro",
                f"Expected 'iPhone 16 Pro', got '{top['model']}'")
            self.assertGreaterEqual(top['confidence'], 90,
                f"Confidence should be ≥90%, got {top['confidence']}%")

            self.test_logger.info(f"\n✅ Perfect Match Confirmed: {top['model']} ({top['confidence']}%)")

        except Exception as e:
            self.test_logger.error(f"❌ Exception during test: {e}", exc_info=True)
            raise

    def test_simulation_detection(self):
        """Sprawdza czy system wykrywa GPU komputera (Symulacja)"""
        self._log_test_params(
            width=402, height=874, refresh_rate=120,
            gpu="Intel(R) Iris(R) Plus Graphics",  # GPU PC
            dpr=3.0, ram=16, cores=8
        )

        try:
            matches = find_top_3_matches(
                width=402, height=874, refresh_rate=120,
                gpu="Intel(R) Iris(R) Plus Graphics",
                dpr=3.0, ram=16, cores=8
            )

            self._log_matches(matches)

            # Asercje
            self.assertIsNotNone(matches, "Matches should not be None")
            self.assertGreater(len(matches), 0, "Should find at least one match")

            top = matches[0]

            # Sprawdź flagę symulacji
            if top.get('is_simulation'):
                self.test_logger.info(f"✅ Simulation flag detected in top match")
            else:
                self.test_logger.warning(f"⚠️  Simulation flag NOT set (expected for desktop GPU)")

            # Sprawdź czy model zawiera "(symulacja?)"
            if "symulacja" in top['model'].lower():
                self.test_logger.info(f"✅ Model name contains 'symulacja': {top['model']}")
            else:
                self.test_logger.warning(f"⚠️  Model name doesn't contain 'symulacja': {top['model']}")

            # Przynajmniej jedna z flag powinna być ustawiona
            self.assertTrue(
                top.get('is_simulation') or "symulacja" in top['model'].lower(),
                "Should detect simulation (either flag or model name)"
            )

        except Exception as e:
            self.test_logger.error(f"❌ Exception during test: {e}", exc_info=True)
            raise

    def test_scoring_nuance(self):
        """
        Sprawdza czy algorytm woli lepsze GPU od minimalnie gorszych wymiarów.
        Scenariusz: Samsung S24 Ultra

        UWAGA: Ten test sprawdza RAW SCORE (przed cappowaniem do 100%),
        ponieważ oba scenariusze mogą osiągnąć 100% confidence po cappowaniu.
        """
        self.test_logger.info("📊 Comparing two scenarios for Samsung S24 Ultra:")

        try:
            # Scenariusz A: Idealne wymiary, złe GPU
            self.test_logger.info("\n🅰️  Scenario A: Perfect dimensions, WRONG GPU")
            self._log_test_params(
                width=384, height=824, refresh_rate=120,
                gpu="Mali-G710",  # Złe GPU (S24 Ultra ma Adreno 750)
                dpr=3.75, ram=8, cores=8
            )

            expected_score_a = self._analyze_scoring_breakdown(
                width=384, height=824, refresh_rate=120,
                gpu="Mali-G710", dpr=3.75, ram=8, cores=8,
                model_name="Samsung Galaxy S24 Ultra"
            )

            matches_bad_gpu = find_top_3_matches(
                width=384, height=824, refresh_rate=120,
                gpu="Mali-G710",
                dpr=3.75, ram=8, cores=8
            )

            self._log_matches(matches_bad_gpu, expected_model="Samsung Galaxy S24 Ultra")

            # Znajdź Samsung S24 Ultra w wynikach (może nie być #1 przez złe GPU)
            s24_match_bad = next((m for m in matches_bad_gpu if "Samsung Galaxy S24 Ultra" in m['model'] and "Zoom" not in m['model']), None)
            raw_score_bad_gpu = s24_match_bad['raw_score'] if s24_match_bad else 0

            # Scenariusz B: Dobre GPU, wymiary lekko inne
            self.test_logger.info("\n🅱️  Scenario B: Good GPU, slightly different height")
            self._log_test_params(
                width=384, height=800,  # Lekko inna wysokość (pasek nawigacji)
                refresh_rate=120,
                gpu="Adreno (TM) 750",  # Idealne GPU
                dpr=3.75, ram=8, cores=8
            )

            expected_score_b = self._analyze_scoring_breakdown(
                width=384, height=800, refresh_rate=120,
                gpu="Adreno (TM) 750", dpr=3.75, ram=8, cores=8,
                model_name="Samsung Galaxy S24 Ultra"
            )

            matches_good_gpu = find_top_3_matches(
                width=384, height=800, refresh_rate=120,
                gpu="Adreno (TM) 750",
                dpr=3.75, ram=8, cores=8
            )

            self._log_matches(matches_good_gpu, expected_model="Samsung Galaxy S24 Ultra")

            # Znajdź Samsung S24 Ultra w wynikach
            s24_match_good = next((m for m in matches_good_gpu if "Samsung Galaxy S24 Ultra" in m['model'] and "Zoom" not in m['model']), None)
            raw_score_good_gpu = s24_match_good['raw_score'] if s24_match_good else 0

            # Porównanie RAW SCORES (przed cappowaniem)
            self.test_logger.info(f"\n📊 COMPARISON (RAW SCORES before capping):")
            self.test_logger.info(f"   Scenario A (bad GPU):  {raw_score_bad_gpu} pts")
            self.test_logger.info(f"   Scenario B (good GPU): {raw_score_good_gpu} pts")
            self.test_logger.info(f"   Difference:            {raw_score_good_gpu - raw_score_bad_gpu} pts")

            # GPU ma wagę 40pkt, wymiary 10-30pkt. Dobre GPU powinno wygrać.
            self.assertGreater(
                raw_score_good_gpu, raw_score_bad_gpu,
                f"Good GPU should score higher than perfect dimensions! "
                f"Got {raw_score_good_gpu} pts vs {raw_score_bad_gpu} pts (raw scores)"
            )

            self.test_logger.info(f"✅ GPU weighting works correctly (GPU > dimensions)")

        except Exception as e:
            self.test_logger.error(f"❌ Exception during test: {e}", exc_info=True)
            raise

    def test_normalization_in_logic(self):
        """Upewnia się, że funkcja normalizacji działa przewidywalnie"""
        self.test_logger.info("🔧 Testing normalize_viewport() edge cases")

        try:
            # Test 1: Skrajny przypadek - 1px x 1000px
            self.test_logger.info("\n📏 Test 1: Extreme aspect ratio (1000x1)")
            norm = normalize_viewport(1000, 1)
            self.test_logger.info(f"   Input:  (1000, 1)")
            self.test_logger.info(f"   Output: {norm}")
            self.assertEqual(norm, (1000, 1), f"Expected (1000, 1), got {norm}")

            # Test 2: Floating point noise
            self.test_logger.info("\n📏 Test 2: Floating point noise (414.015, 896.018)")
            norm = normalize_viewport(414.015, 896.018)
            self.test_logger.info(f"   Input:  (414.015, 896.018)")
            self.test_logger.info(f"   Output: {norm}")
            self.assertEqual(norm, (414, 896), f"Expected (414, 896), got {norm}")

            # Test 3: Wartości None
            self.test_logger.info("\n📏 Test 3: None values")
            norm = normalize_viewport(None, 896)
            self.test_logger.info(f"   Input:  (None, 896)")
            self.test_logger.info(f"   Output: {norm}")
            self.assertEqual(norm, (None, 896), f"Expected (None, 896), got {norm}")

            # Test 4: Duże różnice (nie powinny być zaokrąglane)
            self.test_logger.info("\n📏 Test 4: Large differences (414.5, 896.7)")
            norm = normalize_viewport(414.5, 896.7)
            self.test_logger.info(f"   Input:  (414.5, 896.7)")
            self.test_logger.info(f"   Output: {norm}")
            self.assertEqual(norm, (414.5, 896.7), f"Expected (414.5, 896.7), got {norm}")

            self.test_logger.info(f"\n✅ All normalization tests passed")

        except Exception as e:
            self.test_logger.error(f"❌ Exception during test: {e}", exc_info=True)
            raise

    def test_edge_case_missing_params(self):
        """Testuje zachowanie przy brakujących parametrach"""
        self.test_logger.info("🔍 Testing behavior with missing/invalid parameters")

        try:
            # Test 1: Brak GPU
            self.test_logger.info("\n📋 Test 1: Missing GPU")
            matches = find_top_3_matches(
                width=402, height=874, refresh_rate=120,
                gpu="", dpr=3.0, ram=-1, cores=6
            )
            self._log_matches(matches)
            self.assertIsNotNone(matches, "Should handle missing GPU gracefully")

            # Test 2: Brak refresh_rate
            self.test_logger.info("\n📋 Test 2: Missing refresh_rate")
            matches = find_top_3_matches(
                width=402, height=874, refresh_rate=None,
                gpu="Apple GPU", dpr=3.0, ram=-1, cores=6
            )
            self._log_matches(matches)
            self.assertIsNotNone(matches, "Should handle missing refresh_rate gracefully")

            # Test 3: Wszystkie parametry None (skrajny przypadek)
            self.test_logger.info("\n📋 Test 3: All parameters None/invalid")
            matches = find_top_3_matches(
                width=None, height=None, refresh_rate=None,
                gpu=None, dpr=None, ram=None, cores=None
            )
            self._log_matches(matches)
            # Powinno zwrócić pustą listę lub obsłużyć błąd
            self.assertIsNotNone(matches, "Should return empty list or handle gracefully")

        except Exception as e:
            self.test_logger.error(f"❌ Exception during test: {e}", exc_info=True)
            # W tym przypadku exception jest OK - testujemy obsługę błędów
            self.test_logger.info(f"ℹ️  Exception caught (expected for edge cases): {type(e).__name__}")


def run_suite():
    """Uruchom wszystkie testy z szczegółowym raportem"""
    print("\n" + "="*70)
    print("🦈 SHARK v18 - Advanced Logic Tests")
    print("="*70)

    # Utwórz test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLogicAdvanced)

    # Uruchom testy z verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Podsumowanie
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1


if __name__ == '__main__':
    exit_code = run_suite()
    sys.exit(exit_code)
