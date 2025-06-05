# engine/scraper.py
import aiohttp
import asyncio

async def fetch_single_url(session, url, timeout_seconds=10):
    """
    Asynchronicznie pobiera zawartość pojedynczego URL.
    Zwraca tekst odpowiedzi lub None w przypadku błędu.
    """
    headers = {
        'User-Agent': 'MyCoolScraper/1.0 (Mozilla/5.0 compatible; YourBotName; +http://yourdomain.com/botinfo)'
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as response:
            if response.status == 200:
                print(f"Scraper: Pomyślnie pobrano {url} (status: {response.status})")
                return await response.text()
            else:
                print(f"Scraper: Błąd dla {url} - status: {response.status}")
                return None
    except asyncio.TimeoutError:
        print(f"Scraper: Timeout podczas pobierania {url}")
        return None
    except aiohttp.ClientError as e: # Łapie różne błędy klienta aiohttp
        print(f"Scraper: Błąd klienta aiohttp dla {url}: {e}")
        return None
    except Exception as e:
        print(f"Scraper: Nieoczekiwany błąd podczas pobierania {url}: {e}")
        return None

async def fetch_all_urls_concurrently(urls, concurrent_requests=5, request_timeout=10):
    """
    Pobiera listę URLi asynchronicznie, z ograniczeniem liczby jednoczesnych żądań.
    Zwraca listę zawartości HTML (lub None dla nieudanych).
    """
    # Użycie aiohttp.TCPConnector do ograniczenia liczby jednoczesnych połączeń
    # limit_per_host=0 oznacza brak limitu na hosta, ale limit ogólny działa
    connector = aiohttp.TCPConnector(limit=concurrent_requests, limit_per_host=0, ssl=False) # ssl=False jeśli masz problemy z certyfikatami, inaczej usuń
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for url in urls:
            tasks.append(fetch_single_url(session, url, timeout_seconds=request_timeout))
        
        # asyncio.gather z return_exceptions=True, aby błąd w jednym tasku nie zatrzymał innych
        # Wynikiem będzie lista, gdzie udane żądania mają string HTML, a nieudane mają obiekt wyjątku.
        html_pages_or_errors = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Przetwórzmy wyniki, aby zwrócić HTML lub None
        processed_results = []
        for i, result in enumerate(html_pages_or_errors):
            if isinstance(result, Exception):
                print(f"Scraper: Błąd (z gather) dla URL {urls[i]}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result) # To jest HTML string lub None z fetch_single_url
        
        return processed_results

# Stara funkcja fetch_all dla kompatybilności, jeśli main.py jej używa,
# ale nowa fetch_all_urls_concurrently jest lepsza.
async def fetch_all(urls):
    print("Scraper: Używam starej funkcji fetch_all. Rozważ użycie fetch_all_urls_concurrently.")
    return await fetch_all_urls_concurrently(urls)