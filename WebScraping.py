import requests
import wget
import csv
import time
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Fungsi untuk mengambil data buku dari satu halaman kategori
def scrape_books_from_category_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memeriksa apakah permintaan berhasil
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')  # Menggunakan built-in html.parser

    # Mengambil semua buku pada halaman kategori
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

        # Mengambil product description dan product information
        product_details = scrape_product_details(book_link)

        # Menyimpan data buku dalam bentuk dictionary
        book_data.append({
            'Title': title,
            'Price': price,
            'Availability': availability,
            'Rating': rating,
            'Image URL': image_url,
            'Product Description': product_details['description'],
            'Product Information': product_details['product_info'],
            'Link': book_link,
            'Category': category
        })

        # Menyimpan gambar
        save_image(image_url, title, category)

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

# Fungsi untuk mengambil deskripsi produk dan informasi produk dari halaman detail
def scrape_product_details(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memeriksa apakah permintaan berhasil
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return {'description': '', 'product_info': {}}

    soup = BeautifulSoup(response.text, 'html.parser')  # Menggunakan html.parser (built-in)

    # Mengambil deskripsi produk
    description = soup.find('meta', {'name': 'description'})
    description = description['content'] if description else 'No description available'

    # Mengambil informasi produk (UPC, Product Type, Price, Tax, Number of Reviews)
    product_info = {}
    table = soup.find('table', class_='table table-striped')
    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 1:
                product_info[cols[0].text.strip()] = cols[1].text.strip()

    # Menambahkan Availability ke Product Information
    product_info['Availability'] = soup.find('p', class_='instock availability').text.strip()

    return {'description': description, 'product_info': product_info}

# Fungsi untuk sanitasi nama folder atau file (menghilangkan karakter yang tidak valid)
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# Fungsi untuk menyimpan gambar ke dalam folder berdasarkan kategori (menggunakan wget)
def save_image(image_url, title, category):
    try:
        # Sanitasi nama kategori dan judul buku
        sanitized_category = sanitize_filename(category)
        sanitized_title = sanitize_filename(title)

        # Tentukan path folder berdasarkan kategori yang sudah disanitasi
        category_folder = os.path.join("images", sanitized_category)

        # Buat folder kategori jika belum ada
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)

        # Tentukan nama file gambar
        image_filename = os.path.join(category_folder, f"{sanitized_title}.jpg")

        # Menyimpan gambar menggunakan wget
        wget.download(image_url, image_filename)

        print(f"Image saved for {sanitized_title} in category {sanitized_category}")
    except Exception as e:
        print(f"Error saving image for {title}: {e}")

# Fungsi untuk mengambil URL kategori dan memproses halaman kategori secara keseluruhan
def scrape_category_pages(base_url, category_name, total_pages):
    all_books = []

    for page in range(1, total_pages + 1):
        # Membentuk URL berdasarkan format kategori dan halaman
        category_url = f"{base_url}catalogue/category/books/{category_name}_{page}/index.html"
        print(f"Scraping page {page}: {category_url}")
        books = scrape_books_from_category_page(category_url)
        if books:
            all_books.extend(books)
        time.sleep(1)  # Memberikan jeda untuk menghindari terlalu banyak request

    return all_books

# Fungsi untuk menyimpan hasil scraping ke file CSV
def save_to_csv(all_books_data, filename):
    if not all_books_data:
        print("No data to save.")
        return

    keys = all_books_data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_books_data)
    print(f"Data saved to {filename}")

# Fungsi untuk mengambil semua kategori secara otomatis
def get_all_categories(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Menemukan elemen <ul class="nav nav-list"> dan mengambil kategori
    category_section = soup.find('ul', class_='nav nav-list')
    categories = []
    for li in category_section.find_all('li'):
        a_tag = li.find('a')
        if a_tag:
            category_name = a_tag.text.strip().lower().replace(' ', '_')
            categories.append(category_name)

    return categories

if __name__ == "__main__":
    base_url = 'https://books.toscrape.com/'  # URL dasar dari website
    total_pages = 3  # Ubah sesuai jumlah halaman yang ingin di-scrape

    all_books_data = []  # Daftar untuk menyimpan semua data buku

    # Ambil daftar kategori secara otomatis
    categories = get_all_categories(base_url)

    # Scrape setiap kategori dan gabungkan hasilnya
    for category in categories:
        print(f"Scraping category: {category}")
        books_data = scrape_category_pages(base_url, category, total_pages)  # Scrape kategori
        all_books_data.extend(books_data)  # Menambahkan hasil scrape ke daftar global

    # Simpan semua data yang sudah di-scrape ke CSV
    save_to_csv(all_books_data, 'all_books_data.csv')  # Simpan ke file CSV
