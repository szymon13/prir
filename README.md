# Przetwarzanie równoległe i rozproszone projetk
Ciesielski Syzmon 21223
Błażko Jakub 21215

# 🕷️ Web Scraper App

**Web Scraper App** to rozproszona aplikacja służąca do automatycznego pobierania i selekcji danych z witryn internetowych według zdefiniowanego profilu. Projekt wspiera przetwarzanie równoległe, parsowanie z użyciem BeautifulSoup oraz zapis danych do MongoDB. Aplikacja składa się z modułu silnika (`engine`) oraz interfejsu webowego (`web`).

---

## 📁 Struktura projektu

web-scraper-app/
├── engine/ # Moduł do pobierania i analizy danych
│ ├── main.py
│ ├── parser.py
│ ├── scraper.py
│ ├── Dockerfile
│ └── requirements.txt
│
├── web/ # Moduł interfejsu webowego (Flask)
│ ├── app.py
│ ├── templates/
│ │ └── index.html
│ ├── Dockerfile
│ ├── requirements.txt
│ └── README.txt
│
├── docker-compose.yml # Plik do uruchamiania kontenerów
└── requirements.txt # Wymagania ogólne



---

## ⚙️ Technologie

- **Python 3.10+**
- **BeautifulSoup4** – parsowanie HTML
- **asyncio + multiprocessing** – przetwarzanie współbieżne i wieloprocesowe
- **Flask** – interfejs użytkownika
- **MongoDB** – baza danych
- **Docker + Docker Compose** – konteneryzacja i orkiestracja

---

## 📌 Główne funkcje

- Pobieranie danych z wielu stron jednocześnie
- Profilowanie danych (np. e-maile, adresy, schematy)
- Parsowanie z wykorzystaniem BeautifulSoup
- Zapisywanie danych do MongoDB
- Interfejs webowy do uruchamiania i monitorowania procesów
- Architektura rozproszona: silnik, web, baza danych jako osobne kontenery

---

🚀 Uruchamianie aplikacji
Upewnij się, że Docker i Docker Compose są zainstalowane i uruchomione.

Otwórz terminal w głównym katalogu projektu i wpisz:

bash
Kopiuj
Edytuj
docker-compose up --build -d --remove-orphans
Następnie otwórz przeglądarkę i wejdź na:

arduino
Kopiuj
Edytuj
http://localhost:5000

---
