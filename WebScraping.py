import requests
from bs4 import BeautifulSoup
import csv
import time
import os

# Fungsi untuk scraping data dari setiap halaman
def scrape_books_from_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memeriksa apakah permintaan berhasil
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

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

    soup = BeautifulSoup(response.text, 'html.parser')

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

# Fungsi untuk menyimpan gambar ke dalam folder berdasarkan kategori
def save_image(image_url, title, category):
    try:
        img_data = requests.get(image_url).content
        category_folder = f"images/category/{category}"

        # Buat folder kategori jika belum ada
        if not os.path.exists(category_folder):
            os.makedirs(category_folder)

        # Menggunakan nama buku sebagai nama file gambar
        image_filename = os.path.join(category_folder, f"{title}.jpg")

        # Menyimpan gambar
        with open(image_filename, 'wb') as img_file:
            img_file.write(img_data)

        print(f"Image saved for {title} in category {category}")
    except Exception as e:
        print(f"Error saving image for {title}: {e}")

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
    base_url = 'https://books.toscrape.com/'
    total_pages = 5  # Ubah ini sesuai dengan jumlah halaman yang ingin di-scrape
    books_data = scrape_multiple_pages(base_url, total_pages)
    save_to_csv(books_data, 'books_data.csv')