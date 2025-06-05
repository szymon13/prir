# engine/main.py
import os
import asyncio
import multiprocessing # Możemy go nadal używać, ale do przetwarzania JEDNEGO zadania na raz
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import math
import time # Potrzebne do time.sleep()
from datetime import datetime # Do oznaczania czasu zadań

# Importy z twoich modułów
from scraper import fetch_all_urls_concurrently # Użyjemy tej lepszej funkcji
from parser import parse

# Globalna nazwa kolekcji
DB_COLLECTION_NAME = 'scraped_data_final'
TASKS_COLLECTION_NAME = 'tasks_to_scrape' # Kolekcja dla zadań od użytkownika

# Zmienne globalne dla połączenia w procesie potomnym (jeśli używamy Pool)
# Jeśli przetwarzamy zadania pojedynczo w głównej pętli engine, to nie będą potrzebne globalne dla workera
worker_db_collection_results = None
# Nie potrzebujemy globalnej kolekcji zadań w workerze, bo główna pętla engine się tym zajmuje

# UWAGA: Poniższy kod z `init_worker_db_connection` i `process_batch_of_urls`
# jest zachowany, jeśli CHCESZ, aby engine nadal używał multiprocessing.Pool
# do przetwarzania każdego zadania (URL-a) w osobnym procesie z puli.
# Dla prostszego modelu "jedno zadanie na raz" przez engine, można by to uprościć.
# Rozważmy na razie, że każde zadanie z kolejki jest małym "batchem" jednego URL-a.

def init_worker_db_connection(worker_mongo_uri, db_name_param, results_collection_name_param):
    global worker_db_collection_results
    print(f"Proces potomny {os.getpid()}: Inicjalizacja połączenia z DB...")
    if not worker_mongo_uri:
        worker_db_collection_results = None
        return
    try:
        client = MongoClient(worker_mongo_uri, connectTimeoutMS=10000, serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        db = client[db_name_param]
        worker_db_collection_results = db[results_collection_name_param]
        print(f"Proces potomny {os.getpid()}: Pomyślnie połączono i wybrano kolekcję '{results_collection_name_param}'.")
    except Exception as e:
        print(f"Proces potomny {os.getpid()}: Błąd inicjalizacji DB: {e}")
        worker_db_collection_results = None

def process_single_url_task(url_to_scrape): # Zmieniona funkcja, przyjmuje jeden URL
    """
    Przetwarza pojedynczy URL. Ta funkcja będzie wywoływana przez Pool.map
    dla każdego zadania z kolejki.
    """
    if worker_db_collection_results is None:
        print(f"Proces potomny {os.getpid()}: Brak połączenia z DB (results). Pomijanie {url_to_scrape}")
        return {"url": url_to_scrape, "status": "failed", "error": "DB connection not initialized in worker"}

    print(f"Proces potomny {os.getpid()}: Przetwarzanie URL: {url_to_scrape}")
    
    try:
        html_contents = asyncio.run(fetch_all_urls_concurrently([url_to_scrape])) # Pobierz jeden URL
        if html_contents and html_contents[0]: # Sprawdź czy lista nie jest pusta i czy pierwszy element istnieje
            html_content = html_contents[0]
            parsed_data = parse(html_content, url_source=url_to_scrape)
            if parsed_data:
                # parsed_data['url'] jest już dodawane przez parser lub możemy to robić tutaj
                # Jeśli parser nie dodaje 'url', odkomentuj:
                # if 'url' not in parsed_data:
                #    parsed_data['url'] = url_to_scrape
                
                worker_db_collection_results.insert_one(parsed_data.copy())
                print(f"Proces potomny {os.getpid()}: Zapisano dane dla {url_to_scrape}.")
                return {"url": url_to_scrape, "status": "completed", "data": parsed_data}
            else:
                print(f"Proces potomny {os.getpid()}: Parser nie zwrócił danych dla {url_to_scrape}.")
                return {"url": url_to_scrape, "status": "failed", "error": "Parser returned no data"}
        else:
            print(f"Proces potomny {os.getpid()}: Nie udało się pobrać HTML dla {url_to_scrape}.")
            return {"url": url_to_scrape, "status": "failed", "error": "Failed to fetch HTML"}
    except Exception as e:
        print(f"Proces potomny {os.getpid()}: Błąd podczas przetwarzania {url_to_scrape}: {e}")
        return {"url": url_to_scrape, "status": "failed", "error": str(e)}


def main_engine_service():
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("SILNIK: Krytyczny błąd - MONGO_URI nie jest ustawione. Zakończenie pracy.")
        exit(1)

    db_name = 'web_scraper_db' # Upewnij się, że to ta sama nazwa bazy co w web/app.py

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("SILNIK: Połączenie z MongoDB Atlas udane.")
        db = client[db_name]
        tasks_collection = db[TASKS_COLLECTION_NAME]
        # results_collection jest używana przez procesy potomne
    except Exception as e:
        print(f"SILNIK: Nie udało się połączyć z MongoDB lub wybrać kolekcji: {e}")
        exit(1)

    print(f"SILNIK: Uruchomiono. Nasłuchiwanie na zadania w kolekcji '{TASKS_COLLECTION_NAME}' w bazie '{db_name}'.")
    
    # Ustawienie Poola - można go zainicjować raz i używać wielokrotnie,
    # lub tworzyć dla każdego zadania (mniej wydajne).
    # Dla prostoty, Pool będzie obsługiwał jedno zadanie (URL) na raz.
    # Można by też zrezygnować z Poola, jeśli zadania są lekkie i przetwarzać je w głównej pętli.
    num_processes_for_pool = 1 # Przetwarzamy jedno zadanie (URL) na raz w puli
                               # Możesz zwiększyć, jeśli zadania z kolejki chcesz przetwarzać równolegle przez engine

    with multiprocessing.Pool(
            processes=num_processes_for_pool, 
            initializer=init_worker_db_connection, 
            initargs=(mongo_uri, db_name, DB_COLLECTION_NAME)
    ) as pool:
        while True:
            try:
                # Atomowo znajdź zadanie "pending" i zmień jego status na "processing"
                task_to_process = tasks_collection.find_one_and_update(
                    {"status": "pending"},
                    {"$set": {"status": "processing", "processing_started_at": datetime.utcnow()}},
                    sort=[("submitted_at", 1)] # Przetwarzaj najstarsze zadania pierwsze (FIFO)
                )

                if task_to_process:
                    url = task_to_process.get("url")
                    task_id = task_to_process.get("_id")
                    print(f"SILNIK: Pobrano zadanie {task_id} dla URL: {url}. Przekazywanie do puli...")

                    # Przetwórz ten jeden URL używając Pool.map (który przyjmuje iterowalny obiekt)
                    # Wynik będzie listą z jednym elementem (słownikiem statusu)
                    processing_results = pool.map(process_single_url_task, [url])
                    
                    # Sprawdź wynik przetwarzania
                    if processing_results and len(processing_results) > 0:
                        result_status = processing_results[0]
                        if result_status.get("status") == "completed":
                            tasks_collection.update_one(
                                {"_id": task_id},
                                {"$set": {"status": "completed", 
                                          "completed_at": datetime.utcnow(),
                                          # "scraped_data_summary": result_status.get("data",{}).get("title") # Opcjonalnie
                                          }}
                            )
                            print(f"SILNIK: Zadanie {task_id} (URL: {url}) ukończone pomyślnie.")
                        else: # status "failed"
                            tasks_collection.update_one(
                                {"_id": task_id},
                                {"$set": {"status": "failed", 
                                          "error_message": result_status.get("error", "Unknown error"), 
                                          "failed_at": datetime.utcnow()}}
                            )
                            print(f"SILNIK: Zadanie {task_id} (URL: {url}) zakończone niepowodzeniem: {result_status.get('error')}")
                    else:
                        # To nie powinno się zdarzyć jeśli pool.map działa poprawnie
                        tasks_collection.update_one(
                            {"_id": task_id},
                            {"$set": {"status": "failed", "error_message": "Pool returned no result", "failed_at": datetime.utcnow()}}
                        )
                        print(f"SILNIK: Zadanie {task_id} (URL: {url}) - Pool nie zwrócił wyniku.")

                else:
                    # print("SILNIK: Brak nowych zadań, czekam...")
                    time.sleep(5) # Poczekaj 5 sekund przed ponownym sprawdzeniem

            except Exception as e:
                print(f"SILNIK: Wystąpił błąd w głównej pętli: {e}. Próbuję kontynuować...")
                time.sleep(10) # Dłuższy sen w przypadku ogólnego błędu pętli

if __name__ == "__main__":
    # Usunęliśmy starą funkcję main() z predefiniowaną listą URLi
    main_engine_service()