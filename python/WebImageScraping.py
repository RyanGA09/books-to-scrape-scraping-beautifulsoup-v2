import requests
from bs4 import BeautifulSoup as BfS4
import wget
import os
import re
from pathlib import Path

# Function for folder or file name sanitization (removes invalid characters)
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

#  Function to save images in a category folder
def save_image(title, image_url, category):
    #  Specify folder path by category
    path = f"images/category/{category}/"
    
    # Create a category folder if it doesn't already exist
    Path(path).mkdir(parents=True, exist_ok=True)

    try:
        # Debugging category
        print(f"Category: {category}")  #  Ensure the correct category is taken
        
        #  Sanitize file names to avoid invalid characters
        sanitized_title = sanitize_filename(title)
        image_filename = f"{path}{sanitized_title}.jpg"  # Specify the file name of the saved image
        
        # Check if the image is already in the category folder
        if not os.path.exists(image_filename):
            # Downloading images using wget
            wget.download(image_url, image_filename, bar=None)
            print(f"Image for {sanitized_title} saved in {category} folder.")
        else:
            print(f"Image for {sanitized_title} already exists, skipping download.")
    
    except Exception as e:
        print(f"Error downloading image for {title}: {e}")

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
                    next_page = soup.findAll('ul', class_='pager')
                    # check if for a next page, take the info: page 1 of 2:
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

# Function for scraping data from each book page
def scrape_books_from_category_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

    soup = BfS4(response.text, 'html.parser')  # Using the built-in html.parser

    # Retrieve all the books
    books = soup.find_all('article', class_='product_pod')
    book_data = []

    for book in books:
        # Retrieve the book titles
        title = book.h3.a['title']

        # Retrieve Cover image URL
        image = book.find('img')['src']
        image_url = image.replace("../../", "http://books.toscrape.com/")

        # Retrieve book category (using BeautifulSoup)
        category = soup.find("a", attrs={"href": re.compile("/category/books/")}).string.strip()
        
        # Store book data in dictionary form
        book_data.append({
            'Title': title,
            'Category': category,
            'Image URL': image_url
        })

        # Save the image using the function from ImageScraper.py
        save_image(title, image_url, category)

    return book_data

def category_info(links):
    information = []
    for link in links:
        book_info = scrape_books_from_category_page(link)
        information.append(book_info)
    return information

# Main functions to start the scraping process
def main():
    # start the program:
    # get first all categories with category_scrape:
    all_categories = scraping_category()
    links = scrape_links_of_books_in_category(all_categories)
    category_info(links)

# Run the script.
if __name__ == '__main__':
    main()
