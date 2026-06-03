# SHARK v18

System do rozpoznawania urządzeń mobilnych przez fingerprinting przeglądarki. Na wejściu: rozdzielczość, DPR, GPU, częstotliwość odświeżania, User-Agent. Na wyjściu: model telefonu + kody magazynowe akcesoriów (szkło ochronne, etui).

*Mobile device identification via browser fingerprinting. Input: resolution, DPR, GPU, refresh rate, User-Agent. Output: device model + warehouse accessory codes (screen protector, case).*

---

Detekcja działa w czterech warstwach. Pierwsza to parsowanie User-Agent — jeśli UA zawiera znany identyfikator (np. `iPhone17,1` albo `SM-S928B`), odpowiedź jest natychmiastowa z 100% pewnością. Jeśli UA nie wystarczy, system sięga do BRAIN — słownika nauczonych sygnatur sprzętowych. Jeśli i tam nie ma trafienia, uruchamia się scoring heurystyczny: każdy model z bazy dostaje punkty za dopasowanie rozdzielczości, DPR, GPU i Hz. Wynik automatyczny jeśli lider ma ≥ 90 punktów i drugi kandydat < 60.

BRAIN przechowuje do 10 000 sygnatur, max 5 modeli na sygnaturę, eksmisja LFU. Zapis przez MongoDB `$set` albo `.tmp` + `os.replace` — bezpieczne przy gunicorn multi-worker.

---

## Obsługiwane urządzenia

iPhone 11–17 Pro Max (27 modeli), Samsung Galaxy S/A/Z, Google Pixel 5–8 Pro, Xiaomi Mi 10T–14 Pro, OnePlus 8–12, Huawei P30–P40. Łącznie 50+ modeli Android.

---

## Stack

Python 3.13, Flask 3.1, MongoDB Atlas (pymongo) z fallbackiem na plik JSON, gunicorn, flask-limiter (opcjonalnie Redis dla multi-worker). Testy: pytest + pytest-mock.

---

## Uruchomienie

```bash
pip install -r requirements.txt
cp .env.example .env
python shark_v18_cloud.py
# produkcja: gunicorn shark_v18_cloud:app
```

Bez `MONGODB_URI` w `.env` — działa na lokalnym pliku JSON.

---

## API

```
POST /api/check_brain   sprawdza urządzenie
POST /api/learn         uczy nowej sygnatury
GET  /admin             panel administracyjny (wymaga MongoDB)
```

---

*Licencja proprietary.*
