import requests
from bs4 import BeautifulSoup
import csv
import time
from selenium import webdriver
import pandas as pd



HOST = "https://yacht-parts.ru"
base_url = "https://yacht-parts.ru/catalog/"
HEADERS = {
"accept": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 YaBrowser/24.10.0.0 Safari/537.36"
}

book = {}

# Функция для парсинга страницы товара
def parse_product_page(url, book_category):
    response = requests.get(url, headers=HEADERS)
    print(response)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Ищем и извлекаем данные
    category = soup.select_one("div.catalog_section_list")
    span_category = category.find_all("span")
    n_o_cat = list(map(lambda x: x.get_text(), span_category))
    # name_all_category = category.select("li.sect > a")
    category_not_n = list(map(lambda x: x.get_text().split("\n"), category))
    res_category = [elem for sub_list in category_not_n for elem in sub_list]

    def remove_empty_strings(string):
        return string != ""
     
    fil_l_cat = list(filter(remove_empty_strings, res_category))
    for i in range(len(n_o_cat) - 1):
        book_category[n_o_cat[i]] = fil_l_cat[fil_l_cat.index(n_o_cat[i]) + 1:fil_l_cat.index(n_o_cat[i+1])]
    book_category[n_o_cat[-1]] = fil_l_cat[fil_l_cat.index(n_o_cat[-1]) + 1:]
    hrefs = list(map(lambda x: (x.get_text(), x['href']), category.find_all("a", href=True)))
    return book_category, hrefs, n_o_cat


book, hrefs, n_o_cat = parse_product_page(base_url, book)

def parse_product_page_a(url, hrefs_a, n_o_cat_a):
     
    books_a_names = {}
    for name, a in hrefs_a:
        if name not in n_o_cat_a:
            response = requests.get(f"{url}{a}", headers=HEADERS)
            print(response)
            soup = BeautifulSoup(response.text, "html.parser")
            category = soup.select("div.item-title")
            page_end_soup = soup.select("span.nums")
            page_end = list(map(lambda x: x.get_text().split('\n'), page_end_soup))
            if page_end:
                page_end = page_end[0][-2]
                books_a_names[name] = []
                for i in range(1, int(page_end)):
                    response2 = requests.get(f"{url}{a}?PAGEN_1={i}", headers=HEADERS)
                    print(response2)
                    soup2 = BeautifulSoup(response2.text, "html.parser")
                    category_p = soup2.select("div.item-title")
                    if category_p:                
                        books_a_names[name] = books_a_names[name] + (\
                            list(map(lambda x: x['href'], category_p[0].find_all("a", href=True))))

    return books_a_names

a_names_tovar = parse_product_page_a(HOST, hrefs, n_o_cat)


def parse_product_page_a_desc(url, book_a):
     
    books_a_names = {}

    def tovar_none(tovar):
        if tovar == None:
            return "Не указано"
        return tovar

    def convert_list(list_html):
        if list_html != "Не указано":
            return list(map(lambda x: x.get_text(strip=True), list_html))[0]
        return list_html

    for name, list_a in book_a.items():
        book_a = {}
        for a in list_a:
            response = requests.get(f"{url}{a}", headers=HEADERS)
            print(response)
            soup = BeautifulSoup(response.text, "html.parser")
            category_name = convert_list(tovar_none(soup.select_one("h1")))
            category_brand = tovar_none(soup.select_one("a.brand_picture"))
            category_articul = convert_list(tovar_none(soup.select_one("span.value")))
            category_price = convert_list(tovar_none(soup.select_one("div.price")))
            category_preview_text = convert_list(tovar_none(soup.select_one("div.preview_text")))
            if category_brand != "Не указано":
                category_brand = category_brand.find_all("img", alt=True)
                category_brand = category_brand[0]["alt"]

            category_img = tovar_none(soup.select("div.slides"))
            if category_img != "Не указано":
                try:
                    category_img = category_img[0].find_all("img", src=True)
                    category_img = list(map(lambda x: x["src"], category_img))
                except:
                    category_img = []
                    
            book_a[category_name] = {
            "Артикуль": category_articul,
            "Бренд": category_brand,
            "Цена": category_price,
            "Изображения": category_img,
            "Описание": category_preview_text,
            }

        books_a_names[name] = book_a

    return books_a_names


book_pages_category = parse_product_page_a_desc(HOST, a_names_tovar)


def result(book_osn, book_a):
    for key, value in book_osn.items():
        for elem in range(len(value)):
            try:
                value[elem] = {value[elem]: book_a[value[elem]]}
            except:
                value[elem] = {value[elem]: {}}


    rows = []
    for category, subcategories in book_osn.items():
        for subcategory_dict in subcategories:
            for subcategory, products in subcategory_dict.items():
                for product_name, product_info in products.items():
                    row = {
                        "Категория": category,
                        "Подкатегория": subcategory,
                        "Наименование товара": product_name,
                        "Артикул": product_info.get("Артикуль", ""),
                        "Бренд": product_info.get("Бренд", ""),
                        "Цена": product_info.get("Цена", ""),
                        "Описание": product_info.get("Описание", ""),
                        "Изображения": ", ".join(product_info.get("Изображения", []))
                    }
                    rows.append(row)

    df = pd.DataFrame(rows)

    df.to_excel("yacht_parts_catalog2.xlsx", index=False)
    return "Каталог товаров успешно сохранен в файл yacht_parts_catalog2.xlsx"


print(result(book, book_pages_category))


