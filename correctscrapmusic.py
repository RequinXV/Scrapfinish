import requests
import base64
import csv
from bs4 import BeautifulSoup
import pandas as pd


# L'url du site que je souhaite Scraper
baseUrl = 'https://fr.audiofanzine.com'
uri = "/basse-electrique-divers"


def getLinks(url, nbPg):
    urls = []
    for i in range(nbPg):
        urls.append(url + "?offset=" + str(i*20))
    return urls

def getEndpoints(soup):
    lis = soup.findAll("li", class_="playlist-item cards-item")
    links = []
    for li in lis:
        try:
            href = li.find('a')['href']
        except TypeError:
            href = base64.b64decode(li.span['data-submit']).decode('utf-8').replace("https://fr.audiofanzine.com", "")

        links.append(href)
    return links

def scrapePage(url, process):
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


    # return other_info

def addBaseUrl(baseUrl, urls):
    res = []
    if isinstance(urls, list):
        for url in urls:
            res.append(baseUrl + url)
    return res

def fileWriter(file, fieldnames, data):
    with open(file, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def getSpecs(soup):
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

    stocki = "Pas d'occasion disponible"
    for li in div.find_all('li'):
        if li.find_all('span', {'class': 'in-stock'}): 
            stock = li.find_all('span', {'class': 'in-stock'})
            stockannonce = li.find_all('a', {'class': 'priceBlock-classifieds'})
            if stockannonce:
                stocki = stockannonce[0].text.strip()

        if li.find_all('span', {'class': 'out-stock'}):
            stock = li.find_all('span', {'class': 'out-stock'})
            
        
        if li.find_all('span', {'class': 'priceBlock-classifieds'}):
            stock = li.find_all('span', {'class': 'priceBlock-classifieds'})
            

        if li.find_all('a', {'class': 'priceBlock-classifieds'}):
            stock = li.find_all('a', {'class': 'priceBlock-classifieds'})
            

        if li.find_all('a', {'class': 'priceBlock-price'}) : 
            price = li.find_all('a', {'class': 'priceBlock-price'})
        
        if li.find_all('a', {'class': 'priceBlock-argus'}) :
            price = li.find_all('a', {'class': 'priceBlock-argus'})
        
        stockannonce = li.find_all('a', {'class': 'priceBlock-classifieds'})
        if stockannonce:
            stocki = "Occasion disponible"

        
        
        stocktab.append(stock)
        pricetab.append(price)



    fabricant = spanstab[0][1].text.strip()
    modele = spanstab[1][1].text.strip()
    serie = spanstab[2][1].text.strip()
    categorie = spanstab[3][1].text.strip()
    stock_span =  stocktab[0][0].text.strip()
    price_span = pricetab[0][0].text.strip()
    urlpetiteannonce =  url + "petites-annonces/"
    nbpetiteanonces = stocki

    fiche = {
        "Fabricant": fabricant,
        "Modèle": modele,
        "Série": serie,
        "Catégorie": categorie,
        "Prix" : price_span,
        "Stock" : stock_span,
        "Lien" : url,
        "Lien petite annonce" :urlpetiteannonce, 
        "Dispo occas" : nbpetiteanonces
        }

    fiche["Lien"] = url

    for cle, valeur in fiche.items():
        valeur_sans_span = valeur.replace('<span>', '').replace('</span>', '').replace(',','.').replace('€','').replace('Argus','').replace(' et plus','')
        ficheSansSpan[cle] = valeur_sans_span
    return ficheSansSpan

def writeDataToCSV(file, data):
    fieldnames = [ "Prix", "Stock", "Fabricant", "Modèle", "Série", "Catégorie", "Lien", "Dispo occas", "Lien petite annonce"]
    with open(file, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


#Choisir le nombre de page a scraper 
urls = []
for link in getLinks(baseUrl + uri, 52):
    print("Checking " + link)
    urls.extend(addBaseUrl(baseUrl, scrapePage(link, getEndpoints)))
    print("You've got actually: " + str(len(urls)) + " links!")
print("loading ...")

rows = []
for url in urls:
    rows.append({'link': url})

data = []
for url in urls:
    fiche = scrapePage(url, getSpecs)
    if fiche is None == 0:
        print("Cet url ne renvoit pas de fiche" + url)
    if fiche:
        data.append(fiche)


df = pd.read_csv("Fichesbasses.csv")
df = df.loc[~((df['Stock'].str.contains('pas de stock|aucune annonce', case=False)) & (df['Dispo occas'] == 'Pas d\'occasion disponible'))]
for i, row in df.iterrows():
    if isinstance(row['Catégorie'], str) and any(c.isdigit() for c in row['Catégorie']):
        df.at[i, 'Catégorie'] = ''.join(filter(lambda x: not x.isdigit(), row['Catégorie']))
mask = df['Série'].str.contains('Basses électriques 5 cordes')
df.loc[mask, 'Catégorie'] = df.loc[mask, 'Série']
mask = df["Série"].str.contains("Basses électriques 5 cordes")
df.loc[mask, "Série"] = " "
df.to_csv("cleanFichesbasses.csv", index=False)

fieldsLinks = ['link']
fileWriter('links.csv', fieldsLinks, rows)
writeDataToCSV('Fichesbasses.csv', data)


print("Done")