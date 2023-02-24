import requests
import base64
import csv
from bs4 import BeautifulSoup


class BassScraper:
    def __init__(self, base_url, uri, num_pages):
        self.base_url = base_url
        self.uri = uri
        self.num_pages = num_pages

    def get_links(self):
        urls = []
        for i in range(self.num_pages):
            urls.append(self.base_url + self.uri + "?offset=" + str(i * 20))

        return urls

    def get_endpoints(self, soup):
        lis = soup.findAll("li", class_="playlist-item cards-item")
        links = []
        for li in lis:
            try:
                href = li.find('a')['href']
            except TypeError:
                href = base64.b64decode(li.span['data-submit']).decode('utf-8').replace("https://fr.audiofanzine.com", "")

            links.append(href)
        return links

    def add_base_url(self, urls):
        res = []
        if isinstance(urls, list):
            for url in urls:
                res.append(self.base_url + url)
        return res

    def scrape_page(self, url, process):
        response = requests.get(url)

        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')

            try:
                return process(soup)

            except Exception:
                print("ERROR: Impossible to process! On: " + str(url))
                return None

        else:
            print("ERROR: Failed to connect! On: " + str(url))
            return None


class BassSpecs:
    def get_specs(self, soup):
        ul = soup.find("ul", class_="product-information-header")
        div = soup.find("div", class_="priceBlock-content")

        if ul is None:
            return None

        if div is None:
            return None

        spanstab = []
        pricetab = []
        stocktab = []
        ficheSansSpan = {}

        for uls in ul.find_all("li"):
            spans = uls.find_all("span")
            spanstab.append(spans)

        for li in div.find_all('li'):
            if li.find_all('span', {'class': 'in-stock'}):
                stock = li.find_all('span', {'class': 'in-stock'})

            elif li.find_all('span', {'class': 'out-stock'}):
                stock = li.find_all('span', {'class': 'out-stock'})

            price = li.find_all('a', {'class': 'priceBlock-price'})

            stocktab.append(stock)
            pricetab.append(price)

        fabricant = spanstab[0][1].text.strip()
        modele = spanstab[1][1].text.strip()
        serie = spanstab[2][1].text.strip()
        categorie = spanstab[3][1].text.strip()
        stock_span = stocktab[0][0].text.strip()
        price_span = pricetab[0][0].text.strip()

        fiche = {
            "Fabricant": fabricant,
            "Modèle": modele,
            "Série": serie,
            "Catégorie": categorie,
            "Prix": price_span,
            "Stock": stock_span,
        }

        for cle, valeur in fiche.items():
            valeur_sans_span = valeur.replace('<span>', '').replace('</span>', '').replace(',','.')
            ficheSansSpan[cle] = valeur_sans_span

        return ficheSansSpan


class BassScrapingFacade:
    def __init__(self, base_url, uri, num_pages):
        self.scraper = BassScraper(base_url, uri, num_pages)
        self.specs = BassSpecs()

    def get_specs(self, url):
        return self.scraper.scrape_page(url, self.specs.get_specs)

    def get_all_specs(self):
        urls = self.scraper.add_base_url(self.scraper.get_endpoints())

        with open('basses.csv', 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Fabricant', 'Modèle', 'Série', 'Catégorie', 'Prix', 'Stock'])

            for url in urls:
                specs = self.get_specs(url)
                if specs:
                    writer.writerow([
                        specs['Fabricant'],
                        specs['Modèle'],
                        specs['Série'],
                        specs['Catégorie'],
                        specs['Prix'],
                        specs['Stock']
                    ])




# audiofanzine = BassScraper( 'https://fr.audiofanzine.com',"/basse-electrique-divers", 1)
# a = audiofanzine.get_links()
# print(a)

scraper = BassScrapingFacade('https://fr.audiofanzine.com', '/basse-electrique-divers', 1)
url = scraper.get_all_specs()
bass_specs = BassSpecs()
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
regh= BassScraper(soup)
t = regh.get_links()
specs = bass_specs.get_specs(soup)


print(specs)


