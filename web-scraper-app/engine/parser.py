# engine/parser.py
from bs4 import BeautifulSoup
import re # Do wyrażeń regularnych
from urllib.parse import urljoin # Do łączenia URLi

def extract_emails(text_content):
    """Wyciąga adresy email z tekstu."""
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_regex, text_content)))

def parse_website_data(html_content, base_url=None):
    """
    Parsuje zawartość HTML w poszukiwaniu zdefiniowanych grup danych.
    Zwraca słownik z danymi lub None, jeśli nic nie znaleziono.
    """
    if not html_content:
        print("Parser: Otrzymano pusty html_content.")
        return None

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        parsed_data = {}

        if base_url:
            parsed_data['url'] = str(base_url)

        # 1. Tytuł strony
        title_tag = soup.find('title')
        parsed_data['title'] = str(title_tag.string).strip() if title_tag and title_tag.string else "No Title"

        page_text = soup.get_text(separator=' ', strip=True)

        # 2. Adresy Email
        emails = extract_emails(page_text)
        if emails:
            parsed_data['emails'] = emails
        print(f"Parser DEBUG: Znalezione emaile: {emails if emails else 'Brak'}")
        
        # 3. Linki (pierwsze 5)
        links = []
        for a_tag in soup.find_all('a', href=True, limit=5):
            link_href = a_tag.get('href')
            if link_href:
                link_url = str(link_href).strip()
                if base_url and link_url and not link_url.startswith(('http://', 'https://', '#', 'javascript:', 'mailto:')):
                    try:
                        link_url = urljoin(base_url, link_url)
                    except ValueError:
                        print(f"Parser: Nie udało się połączyć base_url '{base_url}' z link_href '{link_href}'")
                links.append({
                    "text": str(a_tag.get_text(strip=True)),
                    "href": link_url
                })
        if links:
            parsed_data['links'] = links
            
        # 4. Nagłówki H1
        h1_tags = [str(tag.get_text(strip=True)) for tag in soup.find_all('h1')]
        if h1_tags:
            parsed_data['h1_headings'] = h1_tags
            
        # 5. Liczba obrazków
        images = soup.find_all('img')
        parsed_data['image_count'] = len(images)
        print(f"Parser DEBUG: Znaleziono {len(images)} tagów <img>. image_count: {parsed_data['image_count']}")

        # Logika zwracania danych (uproszczona)
        # Zwróć dane, jeśli jest coś więcej niż tylko domyślny tytuł i URL, lub jeśli są jakieś inne dane
        if (parsed_data.get('title') != "No Title" or 
            parsed_data.get('emails') or 
            parsed_data.get('links') or 
            parsed_data.get('h1_headings') or
            (parsed_data.get('image_count', 0) > 0 and len(parsed_data) > 2) ): # Jeśli image_count > 0 i mamy też url i title
            print(f"Parser: Pomyślnie sparsowano dane ze strony {base_url if base_url else ''}. Klucze: {list(parsed_data.keys())}")
            print(f"Parser DEBUG: Finalne parsed_data przed zwróceniem: {parsed_data}")
            return parsed_data
        else:
            # Zwracamy podstawowe dane (url i title) nawet jeśli nic więcej nie ma, aby było widać wpis w bazie
            # Jeśli chcesz, aby zapisywały się tylko "bogate" wyniki, zmień to na return None
            print(f"Parser: Nie znaleziono wielu wartościowych danych, zwracam podstawowe info dla {base_url if base_url else ''}.")
            print(f"Parser DEBUG: Finalne parsed_data (podstawowe) przed zwróceniem: {parsed_data}")
            return parsed_data


    except Exception as e:
        print(f"Parser: Błąd podczas parsowania HTML ze strony {base_url if base_url else ''}: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse(html_content, url_source=None):
    return parse_website_data(html_content, base_url=url_source)