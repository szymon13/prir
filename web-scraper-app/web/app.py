# web/app.py
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import os
from datetime import datetime

app = Flask(__name__)

# --- Konfiguracja Połączenia z MongoDB ---
mongo_uri = os.getenv('MONGO_URI')

if not mongo_uri:
    print("KRYTYCZNY BŁĄD (WEB): Zmienna środowiskowa MONGO_URI nie jest ustawiona!")
    # W rzeczywistej aplikacji można by tu zgłosić wyjątek lub ustawić flagę błędu
    # Dla uproszczenia, aplikacja może próbować działać dalej, ale z problemami.
    client = None # Ustawienie klienta na None, aby uniknąć błędów przy próbie użycia
    db = None
    tasks_collection = None
    results_collection = None
else:
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test połączenia
        client.admin.command('ping')
        print("WEB: Pomyślnie połączono z MongoDB Atlas.")
        
        # Użyj tej samej nazwy bazy danych, co w engine
        # ZASTĄP 'web_scraper_db' RZECZYWISTĄ NAZWĄ SWOJEJ BAZY DANYCH
        db = client['web_scraper_db'] 
        
        # Kolekcje
        tasks_collection = db['tasks_to_scrape']      # Kolekcja na zadania
        results_collection = db['scraped_data_final'] # Kolekcja z wynikami
        print(f"WEB: Wybrano bazę '{db.name}' oraz kolekcje '{tasks_collection.name}' i '{results_collection.name}'.")

    except Exception as e:
        print(f"KRYTYCZNY BŁĄD (WEB): Nie udało się połączyć z MongoDB lub wybrać kolekcji: {e}")
        client = None
        db = None
        tasks_collection = None
        results_collection = None

# --- Trasy Aplikacji ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if tasks_collection is not None: # Sprawdź, czy kolekcja zadań jest dostępna
            url_to_scrape = request.form.get('url_to_scrape')
            if url_to_scrape:
                task = {
                    "url": url_to_scrape,
                    "status": "pending",
                    "submitted_at": datetime.utcnow()
                }
                try:
                    tasks_collection.insert_one(task)
                    print(f"WEB: Dodano nowe zadanie do zescrapowania: {url_to_scrape}")
                except Exception as e:
                    print(f"WEB: Błąd podczas dodawania zadania do MongoDB: {e}")
            else:
                print("WEB: Otrzymano pusty URL w formularzu.")
        else:
            print("WEB: Kolekcja zadań (tasks_collection) nie jest dostępna. Nie można dodać zadania.")
        return redirect(url_for('index'))

    scraped_items = []
    if results_collection is not None: # Sprawdź, czy kolekcja wyników jest dostępna
        try:
            print("WEB: Próba pobrania danych z MongoDB (results_collection)...")
            # Sortowanie po _id malejąco (najnowsze pierwsze), ogranicz do 50
            scraped_items_cursor = results_collection.find().sort("_id", -1).limit(50)
            scraped_items = list(scraped_items_cursor)
            
            print(f"WEB: Pobrano {len(scraped_items)} elementów z MongoDB.")
            if scraped_items:
                # Możesz odkomentować, aby zobaczyć pierwszy element w logach
                # print(f"WEB: Pierwszy pobrany element: {scraped_items[0]}")
                pass
        except Exception as e:
            print(f"WEB: Błąd podczas pobierania danych z MongoDB (results_collection): {e}")
            scraped_items = [] # Ustaw na pustą listę w przypadku błędu
    else:
        print("WEB: Kolekcja wyników (results_collection) nie jest dostępna.")

    return render_template('index.html', items=scraped_items)

if __name__ == '__main__':

    print("WEB: Uruchamianie aplikacji Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)