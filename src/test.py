import requests
from bs4 import BeautifulSoup

url = "https://mycocosm.jgi.doe.gov/fungi/fungi.info.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}

try:
    with requests.Session() as session:
        session.headers.update(headers)
        response = session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        print("Successfully retrieved the page content.")
        # Proceed with parsing the table.

except requests.exceptions.RequestException as e:
    print(f"Error downloading table: {e}")