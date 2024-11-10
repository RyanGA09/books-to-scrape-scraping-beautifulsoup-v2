import requests
from bs4 import BeautifulSoup as BfS4
import csv
import time
import os
# from WebImageScraping import save_image  # Pastikan ImageScraper.py tersedia dan berfungsi

# Fungsi untuk scraping data dari setiap halaman buku
def scrape_books_from_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memeriksa apakah permintaan berhasil
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    soup = BfS4(response.text, 'html.parser')  # Menggunakan built-in html.parser

    # Mengambil semua buku
    books = soup.find_all('article', class_='product_pod')
    book_data = []

    for book in books:
        # Mengambil judul buku
        title = book.h3.a['title']

        # Mengambil harga buku
        price = book.find('p', class_='price_color').text

        # Mengambil ketersediaan buku
        availability = book.find('p', class_='instock availability').text.strip()

        # Mengambil rating buku dan mengonversinya menjadi angka
        rating_class = book.p['class']
        rating = 0
        if len(rating_class) > 1:
            rating = convert_rating_to_number(rating_class[1])

        # Mengambil URL gambar sampul
        image_url = book.find('img')['src']
        image_url = 'https://books.toscrape.com/' + image_url.replace('../', '')

        # Mengambil URL halaman detail buku
        book_link = 'https://books.toscrape.com/catalogue/' + book.h3.a['href'].replace('../../../', '')

        # Mengambil kategori buku
        category = book.find_previous('ul', class_='breadcrumb').find_all('li')[-2].text.strip()

        # Mengambil deskripsi produk (opsional, jika ada halaman detail)
        description = book.find('meta', {'name': 'description'})
        description = description['content'] if description else 'No description available'

        # Harga produk (harga termasuk pajak, harga tanpa pajak, pajak)
        price_incl_tax = 'N/A'
        price_excl_tax = 'N/A'
        price_tax = 'N/A'
        
        # Menambahkan pengecekan jika elemen harga ada sebelum mencoba mengambil sibling-nya
        price_incl_tax_elem = book.find('th', text='Price (incl. tax)')
        if price_incl_tax_elem:
            price_incl_tax = price_incl_tax_elem.find_next_sibling('td').text.strip()

        price_excl_tax_elem = book.find('th', text='Price (excl. tax)')
        if price_excl_tax_elem:
            price_excl_tax = price_excl_tax_elem.find_next_sibling('td').text.strip()

        price_tax_elem = book.find('th', text='Tax')
        if price_tax_elem:
            price_tax = price_tax_elem.find_next_sibling('td').text.strip()

        # Menyimpan data buku dalam bentuk dictionary
        book_data.append({
            'Title': title,
            'price': price,
            'Price including tax': price_incl_tax,
            'Price excluding tax': price_excl_tax,
            'Price Tax': price_tax,
            'Number available': availability,
            'Category': category,
            'Link': book_link,
            'Rating': rating,
            'Product Description': description,
            'Image URL': image_url
        })

        # Menyimpan gambar menggunakan fungsi dari ImageScraper.py
        # Pastikan ImageScraper.py ada dan fungsi save_image berfungsi dengan benar
        # save_image(image_url, title, category)

    return book_data

# Fungsi untuk mengonversi rating menjadi angka
def convert_rating_to_number(rating_class):
    rating_map = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    return rating_map.get(rating_class, 0)

# Fungsi untuk scraping beberapa halaman
def scrape_multiple_pages(base_url, total_pages):
    all_books = []

    for page in range(1, total_pages + 1):
        if page == 1:
            url = base_url  # Halaman pertama
        else:
            url = f"{base_url}catalogue/page-{page}.html"  # Halaman berikutnya
        print(f"Scraping page {page}: {url}")
        books = scrape_books_from_page(url)
        if books:
            all_books.extend(books)
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

if __name__ == "__main__":
    base_url = 'https://books.toscrape.com/'  # URL dasar dari website
    total_pages = 3  # Ubah sesuai jumlah halaman yang ingin di-scrape
    books_data = scrape_multiple_pages(base_url, total_pages)  # Scrape beberapa halaman
    save_to_csv(books_data, 'books_data.csv')  # Simpan hasil ke CSV
