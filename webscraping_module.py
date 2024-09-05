import requests
from bs4 import BeautifulSoup
import random
import time

class webscraping:
    def __init__(self, assignment_desc,filepath) -> None:
        self.user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        ]

        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US, en;q=0.5'
        }
        
        self.filepath = filepath
        self.query = assignment_desc
        self.num_results = 10
        self.search_results = []

    def get_links(self):
        query = requests.utils.quote(self.query)
        search_url = f"https://www.google.com/search?q={query}&num={self.num_results}"

        try:
            time.sleep(random.uniform(2, 5))  # Random delay between 2 and 5 seconds

            response = requests.get(search_url, headers=self.headers)

            if response.status_code != 200:
                print(f"Failed to retrieve search results. Status code: {response.status_code}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')

            for a_tag in soup.find_all('a', href=True):
                link = a_tag['href']

                if "google.co" not in link and link.startswith("https://"):
                    self.search_results.append(link)

        except Exception as e:
            print(f"An error occurred: {e}")

    def scrape_data(self):
        pass

if __name__ == '__main__':
    obj = webscraping("graph code in c") #test case
    obj.get_links()
    obj.scrape_data()
