#!/usr/bin/env python3
import os
import smtplib
import logging
from email.message import EmailMessage

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    sender = os.environ.get("SMTP_USER")
    pwd = os.environ.get("SMTP_PASS")

    if not sender or not pwd:
        logging.error("Przerwano. Brak zmiennych środowiskowych SMTP_USER lub SMTP_PASS.")
        return

    targets = [
        {"company": "Ekoenergetyka", "email": "test-eko@example.com"},
        {"company": "Mera Systemy", "email": "test-mera@example.com"},
        {"company": "Pixel Sp. z o.o.", "email": "test-pixel@example.com"}
    ]

    subject = "Doświadczony Inżynier Systemów i Utrzymania (Biletomaty, e-mobility, infrastruktura IT)"

    body_template = """Dzień dobry,

Piszę do Państwa bezpośrednio, ponieważ szukam nowych wyzwań zawodowych w sektorze nowoczesnych systemów pokładowych i infrastruktury IT.

Przez kilkanaście lat odpowiadałem za utrzymanie infrastruktury sieciowo-serwerowej oraz systemów biletomatów, płatności zbliżeniowych i informacji pasażerskiej (doświadczenie m.in. z systemami MZK Gorzów).
Projektuję rozwiązania automatyzujące (Python, Bash, PowerShell), wdrażam i zarządzam klastrami Proxmox oraz diagnozuję sprzętowy hardware bezpośrednio w terenie.

Chętnie porozmawiam o możliwości wsparcia działu technicznego w {company}. W załączniku przesyłam swoje CV.

Z poważaniem,
Marcin Miśtak
IT Manager & Automation Engineer
Gorzów Wielkopolski
"""

    try:
        logging.info("Nawiązywanie połączenia SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, pwd)
            for target in targets:
                msg = EmailMessage()
                msg.set_content(body_template.format(company=target["company"]))
                msg["Subject"] = subject
                msg["From"] = sender
                msg["To"] = target["email"]

                # Odkomentuj poniższą linię, gdy dodasz załącznik i poprawne maile
                # server.send_message(msg)

                logging.info(f"Pomyślnie wygenerowano szkic wiadomości dla: {target['company']} -> {target['email']}")

    except smtplib.SMTPAuthenticationError:
        logging.error("Błąd uwierzytelniania SMTP. Sprawdź hasło aplikacji.")
    except Exception as e:
        logging.error(f"Wystąpił nieoczekiwany błąd: {e}")

if __name__ == "__main__":
    main()
