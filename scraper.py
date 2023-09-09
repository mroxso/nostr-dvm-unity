# scraper.py
from bs4 import BeautifulSoup
import requests

def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    text = ""
    for paragraph in soup.find_all('p'):  # assuming we are getting all the paragraph tags
        text += paragraph.get_text()

    return text