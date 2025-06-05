# Przetwarzanie równoległe i rozproszone projekt
Ciesielski Syzmon 21223
Błażko Jakub 21215

# 🕷️ Web Scraper App

**Web Scraper App** to rozproszona aplikacja służąca do automatycznego pobierania i selekcji danych z witryn internetowych według zdefiniowanego profilu. Projekt wspiera przetwarzanie równoległe, parsowanie z użyciem BeautifulSoup oraz zapis danych do MongoDB. Aplikacja składa się z modułu silnika (`engine`) oraz interfejsu webowego (`web`).

---
![image](https://github.com/user-attachments/assets/acfb1447-bb89-44a4-bfc3-712465de3d28)



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

Uwaga dotycząca pliku .env
Plik .env, zawierający dane konfiguracyjne połączenia z bazą danych MongoDB (np. URI, nazwę bazy, port), nie został dołączony do repozytorium ze względów bezpieczeństwa oraz braku możliwości jego automatycznego zrzutu.
