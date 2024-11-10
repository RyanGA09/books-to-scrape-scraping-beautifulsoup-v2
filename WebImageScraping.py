import requests
from bs4 import BeautifulSoup as BfS4
import wget
import os
import re
import time
from pathlib import Path

# scrape all links of the categories even for multiple pages:
def scraping_category():
    print("----------start category----------")
    print(" Please wait ... ")
    url = "http://books.toscrape.com/"
    response = requests.get(url)
    if response.ok:
        # create a list for all links of the categories:
        links_of_categories_all = []
        soup = BfS4(response.content, "html.parser")
        # take information for the sidebar: categories
        categories = soup.select(".side_categories a")
        for category in categories:
            href = category["href"]
            link = f"http://books.toscrape.com/{href}"
            # create one link of each book:
            links_of_categories_all.append(link)

            # start from the second link, start with Travel:
            if not href == "catalogue/category/books_1/index.html":
                response = requests.get(link)
                if response.ok:
                    soup = BfS4(response.content, "html.parser")
                    # check if for a next page, take the info: page 1 of 2:
                    next_page = soup.findAll('ul', class_='pager')
                    if next_page:
                        for page in next_page:
                            all_num_page = page.find("li", class_="current").text
                            # get the last number of info, to know how many pages will be there:
                            num_page = int(all_num_page.strip()[10:])

                            counter = 2
                            while num_page > 1:
                                link_next_page = f"{link.replace('index.html', '')}page-{counter}.html"
                                links_of_categories_all.append(link_next_page)
                                num_page -= 1
                                counter += 1

        # start from the second link in the list:
        links_of_categories = links_of_categories_all[1:]
        # all links including multiple pages
        return links_of_categories

# get all links of the books in one category:
def scrape_links_of_books_in_category(category_links):
    print("----------start books in category----------")
    print(" Please wait ... ")
    # read information to get the book link of each book in one category:
    # create a list for all links of books inside a category:
    books_in_category = []
    for link in category_links:
        book_url = link.strip()
        response = requests.get(book_url)
        if response.ok:
            soup = BfS4(response.content, "html.parser")
            # find all <article class="product_pod">:
            articles = soup.find_all("article", class_="product_pod")
            for article in articles:
                a = article.find("a")
                a_link = a["href"]
                # create link of each book:
                books_in_category.append(
                    f'http://books.toscrape.com/catalogue/{a_link.replace("../../../", "")}'
                )

    return books_in_category


# Fungsi untuk sanitasi nama folder atau file (menghilangkan karakter yang tidak valid)
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# Fungsi untuk menyimpan gambar dalam folder kategori
def save_image(image_url, category, title):
    # Tentukan path folder berdasarkan kategori
    path = f"images/category/{category}/"
    
    # Membuat folder kategori jika belum ada
    Path(path).mkdir(parents=True, exist_ok=True)

    try:
        # Debugging kategori
        print(f"Category: {category}")  # Memastikan kategori yang diambil benar
        
        # Mengunduh gambar ke folder kategori
        sanitized_title = sanitize_filename(title)  # Sanitasi nama file jika perlu
        image_filename = f"{path}{sanitized_title}.jpg"  # Menentukan nama file gambar yang disimpan
        
        # Mengunduh gambar menggunakan wget
        wget.download(image_url, image_filename, bar=None)
        
        print(f"Image for {sanitized_title} saved in {category} folder.")
    
    except Exception as e:
        print(f"Error downloading image for {title}: {e}")
        

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

        # Mengambil URL gambar sampul
        image = book.find('img')['src']
        image_url = image.replace("../../", "http://books.toscrape.com/")

        # Mengambil URL halaman detail buku
        book_link = 'https://books.toscrape.com/catalogue/' + book.h3.a['href'].replace('../../../', '')

        # # Mengambil kategori buku (menggunakan BeautifulSoup)
        # category = book.find_previous('ul', class_='breadcrumb').find_all('li')[-2].text.strip()

        # category
        category = soup.find("a", attrs={"href": re.compile("/category/books/")}).string
        
        # Menyimpan data buku dalam bentuk dictionary
        book_data.append({
            'Title': title,
            'Category': category,
            'Image URL': image_url
        })

        # # Menyimpan gambar menggunakan fungsi dari ImageScraper.py
        # save_image(image_url, title, category)

    return book_data

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

def category_info(links):
    information = []
    for link in links:
        book_info = scrape_books_from_page(link)
        information.append(book_info)
        save_image(book_info['image_url'], book_info['category'])
        
    return information

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # start the program:
    # get first all categories with category_scrape:
    all_categories = scraping_category()
    
    # Menyimpan gambar menggunakan fungsi dari ImageScraper.py
    # save_image(image_url, title, category)
    
    links = scrape_links_of_books_in_category(all_categories)
    
    category_info(links)
