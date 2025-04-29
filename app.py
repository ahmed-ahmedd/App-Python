from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
import os
import re
import pandas as pd
from io import BytesIO
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import random
import urllib.parse

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-ulemt-2025')

products = []

# Currency conversion rates (approximate, update as needed)
EGP_TO_USD = 0.0204  # 1 EGP = 0.0204 USD (as of writing)
USD_TO_EGP = 49.0    # 1 USD = 49.0 EGP (as of writing)
GBP_TO_USD = 1.30    # 1 GBP = 1.30 USD (as of writing)
USD_TO_GBP = 0.77    # 1 USD = 0.77 GBP (as of writing)

def get_price(price_str):
    """Extract numeric price from string"""
    try:
        # Remove currency symbols and commas, then convert to float
        cleaned = re.sub(r'[^\d.]', '', str(price_str))
        return float(cleaned) if cleaned else None
    except Exception as e:
        print(f"Error parsing price: {str(e)}")
        return None

def get_user_agent():
    """Return a random user agent to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
    ]
    return random.choice(user_agents)

def scrape_amazon(product_name, country="com"):
    """Scrape Amazon for product prices"""
    print(f"🔍 Searching Amazon {country} for: {product_name}")
    results = []
    headers = {
        'User-Agent': get_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    encoded_name = urllib.parse.quote_plus(product_name)
    url = f"https://www.amazon.{country}/s?k={encoded_name}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('.s-result-item[data-component-type="s-search-result"]')
            # Increased from 10 to 20 products
            for product in products[:20]:
                try:
                    title_element = product.select_one('h2 a span')
                    price_element = product.select_one('.a-price .a-offscreen')
                    link_element = product.select_one('h2 a')
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price_text = price_element.text.strip()
                        link_href = link_element.get('href')
                        if link_href.startswith('/'):
                            link = f"https://www.amazon.{country}{link_href}"
                        else:
                            link = link_href
                        price = get_price(price_text)
                        if price:
                            # Handle currency conversion
                            original_price = price
                            currency = "USD"
                            if country == "eg":
                                price_usd = price * EGP_TO_USD
                                currency = "EGP"
                            elif country == "co.uk":
                                price_usd = price * GBP_TO_USD
                                currency = "GBP"
                            else:
                                price_usd = price
                                
                            results.append({
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "price": price_usd,
                                "original_price": original_price,
                                "currency": currency,
                                "source": f"Amazon ({country.upper()})",
                                "url": link,
                                "time": datetime.now().strftime("%H:%M"),
                                "country": country.upper()
                            })
                except Exception as e:
                    print(f"Error parsing Amazon product: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error scraping Amazon {country}: {str(e)}")
    return results

def scrape_walmart(product_name):
    """Scrape Walmart for product prices"""
    print(f"🔍 Searching Walmart for: {product_name}")
    results = []
    headers = {
        'User-Agent': get_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    encoded_name = urllib.parse.quote_plus(product_name)
    url = f"https://www.walmart.com/search?q={encoded_name}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('div[data-item-id]')
            # Increased from 10 to 20 products
            for product in products[:20]:
                try:
                    title_element = product.select_one('span.ellipsis-2')
                    price_element = product.select_one('div[data-automation-id="product-price"]')
                    link_element = product.select_one('a[link-identifier="linkCard"]')
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price_text = price_element.text.strip()
                        link_href = link_element.get('href')
                        if link_href.startswith('/'):
                            link = f"https://www.walmart.com{link_href}"
                        else:
                            link = link_href
                        price = get_price(price_text)
                        if price:
                            results.append({
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "price": price,
                                "source": "Walmart (US)",
                                "url": link,
                                "time": datetime.now().strftime("%H:%M"),
                                "country": "US"
                            })
                except Exception as e:
                    print(f"Error parsing Walmart product: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error scraping Walmart: {str(e)}")
    return results
def scrape_ebay(product_name, country="com"):
    """Scrape eBay for product prices"""
    print(f"🔍 Searching eBay {country} for: {product_name}")
    results = []
    headers = {
        'User-Agent': get_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    encoded_name = urllib.parse.quote_plus(product_name)
    url = f"https://www.ebay.{country}/sch/i.html?_nkw={encoded_name}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('li.s-item')
            # Increased from 10 to 20 products
            for product in products[:20]:
                try:
                    title_element = product.select_one('div.s-item__title')
                    price_element = product.select_one('span.s-item__price')
                    link_element = product.select_one('a.s-item__link')
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price_text = price_element.text.strip()
                        link = link_element.get('href')
                        if "Shop on eBay" in title:
                            continue
                        price = get_price(price_text)
                        if price:
                            # Handle currency conversion
                            original_price = price
                            currency = "USD"
                            if country == "co.uk":
                                price_usd = price * GBP_TO_USD
                                currency = "GBP"
                            else:
                                price_usd = price
                                
                            results.append({
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "price": price_usd,
                                "original_price": original_price,
                                "currency": currency,
                                "source": f"eBay ({country.upper()})",
                                "url": link,
                                "time": datetime.now().strftime("%H:%M"),
                                "country": country.upper()
                            })
                except Exception as e:
                    print(f"Error parsing eBay product: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error scraping eBay {country}: {str(e)}")
    return results

def scrape_jumia(product_name):
    """Scrape Jumia Egypt for product prices"""
    print(f"🔍 Searching Jumia Egypt for: {product_name}")
    results = []
    headers = {
        'User-Agent': get_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    encoded_name = urllib.parse.quote_plus(product_name)
    url = f"https://www.jumia.com.eg/catalog/?q={encoded_name}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('article.prd')
            # Increased from 10 to 20 products
            for product in products[:20]:
                try:
                    title_element = product.select_one('h3.name')
                    price_element = product.select_one('div.prc')
                    link_element = product.select_one('a.core')
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price_text = price_element.text.strip()
                        link_href = link_element.get('href')
                        if link_href.startswith('/'):
                            link = f"https://www.jumia.com.eg{link_href}"
                        else:
                            link = link_href
                        price = get_price(price_text)
                        if price:
                            price_usd = price * EGP_TO_USD
                            results.append({
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "price": price_usd,
                                "original_price": price,
                                "currency": "EGP",
                                "source": "Jumia (EG)",
                                "url": link,
                                "time": datetime.now().strftime("%H:%M"),
                                "country": "EG"
                            })
                except Exception as e:
                    print(f"Error parsing Jumia product: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error scraping Jumia: {str(e)}")
    return results

def scrape_noon(product_name):
    """Scrape Noon Egypt for product prices"""
    print(f"🔍 Searching Noon Egypt for: {product_name}")
    results = []
    headers = {
        'User-Agent': get_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    encoded_name = urllib.parse.quote_plus(product_name)
    url = f"https://www.noon.com/egypt-en/search?q={encoded_name}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('div[data-qa="product-block"]')
            for product in products[:20]:
                try:
                    title_element = product.select_one('div[data-qa="product-name"]')
                    price_element = product.select_one('div[data-qa="price-wrapper"] span')
                    link_element = product.select_one('a')
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price_text = price_element.text.strip()
                        link_href = link_element.get('href')
                        if link_href.startswith('/'):
                            link = f"https://www.noon.com{link_href}"
                        else:
                            link = link_href
                        price = get_price(price_text)
                        if price:
                            price_usd = price * EGP_TO_USD
                            results.append({
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "price": price_usd,
                                "original_price": price,
                                "currency": "EGP",
                                "source": "Noon (EG)",
                                "url": link,
                                "time": datetime.now().strftime("%H:%M"),
                                "country": "EG"
                            })
                except Exception as e:
                    print(f"Error parsing Noon product: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error scraping Noon: {str(e)}")
    return results

# Add a new scraper for AliExpress
def scrape_aliexpress(product_name):
    """Scrape AliExpress for product prices"""
    print(f"🔍 Searching AliExpress for: {product_name}")
    results = []
    headers = {
        'User-Agent': get_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
    }
    encoded_name = urllib.parse.quote_plus(product_name)
    url = f"https://www.aliexpress.com/wholesale?SearchText={encoded_name}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('.list--gallery--C2f2tvm')
            for product in products[:15]:
                try:
                    title_element = product.select_one('.multi--titleText--nXeOvyr')
                    price_element = product.select_one('.multi--price-sale--U-S0jtj')
                    link_element = product.select_one('a.multi--container--1UZxxHY')
                    
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price_text = price_element.text.strip()
                        link_href = link_element.get('href')
                        if link_href.startswith('//'):
                            link = f"https:{link_href}"
                        elif link_href.startswith('/'):
                            link = f"https://www.aliexpress.com{link_href}"
                        else:
                            link = link_href
                            
                        price = get_price(price_text)
                        if price:
                            results.append({
                                "title": title[:50] + "..." if len(title) > 50 else title,
                                "price": price,
                                "source": "AliExpress",
                                "url": link,
                                "time": datetime.now().strftime("%H:%M"),
                                "country": "CN"
                            })
                except Exception as e:
                    print(f"Error parsing AliExpress product: {str(e)}")
                    continue
    except Exception as e:
        print(f"Error scraping AliExpress: {str(e)}")
    return results

def fetch_prices(product_name, your_price, currency="USD", region="all", selected_marketplaces=None):
    """Fetch prices from multiple sources using web scraping"""
    all_competitors = []
    # Convert price to USD for comparison if needed
    your_price_usd = your_price
    if currency == "EGP":
        your_price_usd = your_price * EGP_TO_USD
    elif currency == "GBP":
        your_price_usd = your_price * GBP_TO_USD
        
    # Define marketplace mappings
    marketplace_functions = {
        'amazon-us': lambda: scrape_amazon(product_name, "com"),
        'amazon-uk': lambda: scrape_amazon(product_name, "co.uk"),
        'amazon-eg': lambda: scrape_amazon(product_name, "eg"),
        'ebay-us': lambda: scrape_ebay(product_name, "com"),
        'ebay-uk': lambda: scrape_ebay(product_name, "co.uk"),
        'walmart': lambda: scrape_walmart(product_name),
        'jumia-eg': lambda: scrape_jumia(product_name),
        'noon-eg': lambda: scrape_noon(product_name),
        'aliexpress': lambda: scrape_aliexpress(product_name)
    }
    
    # Define region mappings to marketplaces
    region_marketplaces = {
        'all': list(marketplace_functions.keys()),
        'us': ['amazon-us', 'ebay-us', 'walmart'],
        'uk': ['amazon-uk', 'ebay-uk'],
        'eg': ['amazon-eg', 'jumia-eg', 'noon-eg'],
        'global': ['amazon-us', 'amazon-uk', 'ebay-us', 'ebay-uk', 'aliexpress']
    }
    
    # Determine which marketplaces to search
    if selected_marketplaces:
        marketplaces_to_search = selected_marketplaces
    else:
        marketplaces_to_search = region_marketplaces.get(region, region_marketplaces['all'])
    
    print(f"🔍 Searching the following marketplaces: {marketplaces_to_search}")
    
    # Iterate through selected marketplaces
    for marketplace in marketplaces_to_search:
        if marketplace in marketplace_functions:
            time.sleep(random.uniform(0.5, 1.5))  # Add random delay to avoid being blocked
            try:
                results = marketplace_functions[marketplace]()
                all_competitors.extend(results)
                print(f"✅ Found {len(results)} results from {marketplace}")
            except Exception as e:
                print(f"❌ Error searching {marketplace}: {str(e)}")
    
    # Calculate price differences
    for competitor in all_competitors:
        # All prices are now in USD for comparison
        competitor["difference"] = round(competitor["price"] - your_price_usd, 2)
        # For display purposes, add original price in local currency if available
        if "original_price" in competitor and "currency" in competitor:
            competitor["display_price"] = f"{competitor['original_price']} {competitor['currency']} (${competitor['price']:.2f} USD)"
        else:
            competitor["display_price"] = f"${competitor['price']:.2f}"
    
    # Sort by price
    all_competitors.sort(key=lambda x: x["price"])
    print(f"✅ Found {len(all_competitors)} competitors across all regions")
    return all_competitors

@app.after_request
def add_no_cache_headers(response):
    """
    Add headers to disable caching for all responses.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        product = request.form.get("product", "").strip()
        price = request.form.get("price", "").strip()
        currency = request.form.get("currency", "USD")
        region = request.form.get("region", "all")
        custom_markets = request.form.get("custom-markets") == "on"
        
        if not product or not price:
            flash("Product and price are required!", "danger")
            return redirect(url_for('home'))
        
        try:
            price = float(price)
            if price <= 0: raise ValueError
        except:
            flash("Price must be a positive number!", "danger")
            return redirect(url_for('home'))
        
        # Handle marketplace selection
        selected_marketplaces = None
        if custom_markets:
            selected_marketplaces_str = request.form.get("selected_marketplaces", "")
            if selected_marketplaces_str:
                selected_marketplaces = selected_marketplaces_str.split(',')
        
        # Fetch prices based on selected marketplaces
        competitors = fetch_prices(product, price, currency, region, selected_marketplaces)
        
        # Display price based on selected currency
        if currency == "USD":
            display_currency = "$"
        elif currency == "EGP":
            display_currency = "£E"  # Egyptian Pound symbol
        elif currency == "GBP":
            display_currency = "£"   # British Pound symbol
        else:
            display_currency = "$"   # Default to USD
            
        products.append({
            "id": len(products) + 1,
            "name": product,
            "your_price": price,
            "your_currency": currency,
            "display_price": f"{display_currency}{price}",
            "competitors": competitors,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "region": region,
            "selected_marketplaces": selected_marketplaces
        })
        
    return render_template("index.html", products=products)

@app.route("/update/<int:product_id>")
def update(product_id):
    found = False
    for product in products:
        if product["id"] == product_id:
            # Use the previously selected region and marketplaces when updating
            region = product.get("region", "all")
            selected_marketplaces = product.get("selected_marketplaces")
            
            product["competitors"] = fetch_prices(
                product["name"], 
                product["your_price"], 
                product.get("your_currency", "USD"),
                region,
                selected_marketplaces
            )
            product["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            flash(f"Updated prices for {product['name']}!", "success")
            found = True
            break
    if not found:
        flash("Product not found!", "danger")
    return redirect(url_for('home'))

@app.route("/redirect/<path:url>")
def safe_redirect(url):
    """
    Safety redirect route that ensures URLs are valid
    """
    # Validate the URL is a proper web URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return redirect(url)

@app.route("/export")
def export():
    try:
        data = []
        for product in products:
            for comp in product.get("competitors", []):
                data.append({
                    "Product": product["name"],
                    "Your Price": product["your_price"],
                    "Your Currency": product.get("your_currency", "USD"),
                    "Competitor": comp["source"],
                    "Price": comp["price"],
                    "Original Price": comp.get("original_price", comp["price"]),
                    "Currency": comp.get("currency", "USD"),
                    "Difference": comp["difference"],
                    "URL": comp["url"],
                    "Country": comp.get("country", "N/A"),
                    "Time": comp["time"]
                })
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="competitor_prices.xlsx"
        )
    except Exception as e:
        flash(f"Export failed: {str(e)}", "danger")
        return redirect(url_for('home'))

@app.route("/clear", methods=["POST"])
def clear():
    """
    Clear all stored products and redirect to the home page.
    """
    global products
    products = []  # Clear the products list
    flash("Search history cleared!", "info")
    return redirect(url_for('home'))
    
if __name__ == "__main__":
    print("🚀 Starting app...")
    app.run(host="0.0.0.0", port=5000)