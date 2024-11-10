import requests
from bs4 import BeautifulSoup as BfS4
import csv
import time

# Fungsi untuk mengambil data dari halaman detail buku
def scrape_book_details(book_link):
    try:
        response = requests.get(book_link)
        response.raise_for_status()  # Memeriksa apakah permintaan berhasil
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return {'description': 'No description available', 'price_incl_tax': 'N/A', 'price_excl_tax': 'N/A', 'price_tax': 'N/A'}

    soup = BfS4(response.text, 'html.parser')

    # Mengambil deskripsi produk
    description = soup.find('meta', {'name': 'description'})
    description = description['content'] if description else 'No description available'

    # Mengambil harga produk (price including tax, price excluding tax, price tax)
    price_incl_tax = 'N/A'
    price_excl_tax = 'N/A'
    price_tax = 'N/A'

    price_incl_tax_elem = soup.find('th', text='Price (incl. tax)')
    if price_incl_tax_elem:
        price_incl_tax = price_incl_tax_elem.find_next_sibling('td').text.strip()

    price_excl_tax_elem = soup.find('th', text='Price (excl. tax)')
    if price_excl_tax_elem:
        price_excl_tax = price_excl_tax_elem.find_next_sibling('td').text.strip()

    price_tax_elem = soup.find('th', text='Tax')
    if price_tax_elem:
        price_tax = price_tax_elem.find_next_sibling('td').text.strip()

    return {
        'description': description,
        'price_incl_tax': price_incl_tax,
        'price_excl_tax': price_excl_tax,
        'price_tax': price_tax
    }

# Fungsi untuk mengambil link buku dari katalog
def scrape_links_of_books_from_page(page_url):
    books_in_page = []
    response = requests.get(page_url)
    if response.ok:
        soup = BfS4(response.content, "html.parser")
        # Ambil semua artikel dengan kelas "product_pod" yang berisi informasi buku
        articles = soup.find_all("article", class_="product_pod")
        for article in articles:
            a = article.find("a")
            a_link = a["href"]
            # Membuat link lengkap ke halaman detail buku
            books_in_page.append(f'http://books.toscrape.com/catalogue/{a_link.replace("../../../", "")}')
    return books_in_page

# Fungsi untuk mengambil data detail satu buku
def scrape_book_data(book_link):
    print(f"Scraping {book_link} ...")
    response = requests.get(book_link)
    if response.ok:
        soup = BfS4(response.content, "html.parser")
        image = soup.find("img")
        image_url = image["src"].replace("../../", "http://books.toscrape.com/")  # Mengubah url relatif menjadi absolut
        title = image["alt"]
        price = soup.find('p', class_='price_color').text
        availability = soup.find("th", text="Availability").find_next_sibling("td").string.strip()
        rating = soup.find("p", attrs={'class': 'star-rating'}).get("class")[1]
        details = scrape_book_details(book_link)
        
        data = {
            "Title": title,
            "Price": price,
            "Price including tax": details['price_incl_tax'],
            "Price excluding tax": details['price_excl_tax'],
            "Price Tax": details['price_tax'],
            "Availability": availability,
            "Product Description": details['description'],
            "Rating": rating,
            "Image URL": image_url,
            "Link": book_link
        }
        return data
    return None

# Fungsi untuk scraping buku dari beberapa halaman katalog
def scrape_books_from_pages(base_url, total_pages):
    all_books = []
    for page in range(1, total_pages + 1):
        if page == 1:
            url = base_url  # Halaman pertama
        else:
            url = f"{base_url}catalogue/page-{page}.html"  # Halaman berikutnya

        print(f"Scraping page {page}: {url}")
        
        # Ambil semua link buku dari halaman ini
        books_in_page = scrape_links_of_books_from_page(url)
        for book_link in books_in_page:
            book_data = scrape_book_data(book_link)
            if book_data:
                all_books.append(book_data)

        time.sleep(1)  # Memberikan jeda untuk menghindari terlalu banyak request

    return all_books

# Fungsi untuk menyimpan hasil scraping ke file CSV
def save_to_csv(data, filename):
    if not data:
        print("No data to save.")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")

# Fungsi utama untuk memulai proses scraping
def main():
    base_url = 'http://books.toscrape.com/'  # URL dasar untuk katalog buku
    total_pages = 3  # Jumlah halaman yang ingin di-scrape, bisa Anda ubah sesuai kebutuhan
    
    # Scrape buku dari beberapa halaman
    books_data = scrape_books_from_pages(base_url, total_pages)

    # Simpan hasil ke file CSV
    save_to_csv(books_data, 'books_data.csv')

if __name__ == "__main__":
    main()
