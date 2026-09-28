import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("laptops_scraper.log")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
file_handler.setFormatter(file_formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

list_of_laptops=[]
url = "https://webscraper.io"
second_url="/test-sites/e-commerce/static/computers/laptops"

while second_url is not None:
    try: 
            headers={"User-Agent" : "Mozilla/5.0 (windows NT 10.0; win64; x64) Applewebkit/537.36"}
            response = requests.get(url=url+second_url , headers=headers , timeout=(5,10))
            response.raise_for_status()
            response.encoding = "utf-8"
            soup = BeautifulSoup (response.text , "lxml")
            logger.info(f"Scraping: {url+second_url}")
            laptops=soup.find_all("div", class_="product-wrapper card-body")
            for laptop in laptops:
                name=laptop.select_one("h4>a")
                if name:
                    laptop_name=name.get_text(strip=True)
                else:
                    laptop_name="Doesn't exist"
                price=laptop.select_one("h4>span")
                if price:
                    laptop_price=price.get_text(strip=True)
                else:
                    laptop_price="Doesn't exist"
                reviews=laptop.select_one("p.review-count.float-end > span")
                if reviews:
                    laptop_reviews=reviews.get_text(strip=True)
                else:
                    laptop_reviews="Doesn't exist"
                stars = laptop.select_one("p[data-rating]")   #stars=(laptop.find("p",class_="review-count")).next_sibling => false  
                if stars:                                     #stars = laptop.find("p", class_="review-count").find_next_sibling("p") => true
                    laptop_stars=stars.get("data-rating")
                else:
                    laptop_stars="Doesn't exist"
                description=laptop.select_one("p.description.card-text")
                if description:
                    laptop_description=description.get_text(strip=True)
                else:
                    laptop_description="Doesn't exist"
                laptop_dict={"Laptop_name":laptop_name , "Price":laptop_price , "Reviews":laptop_reviews , "Stars":laptop_stars , "Description":laptop_description}
                list_of_laptops.append(laptop_dict)

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        break
    except requests.exceptions.Timeout:
        logger.error("Server response delay — please try again")
        break
    except requests.exceptions.ConnectionError:
        logger.error("Internet outage or server not available")
        break
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        break
    except Exception as e : 
        logger.error(f"Error found: {e}")
        break

    else:
        next_page_link=soup.select_one("a.page-link.next")
        if next_page_link:
            second_url=next_page_link.get("href")
        else:
            second_url=None
            logger.debug("The scraping process is completed")

# print(list_of_laptops)
logger.info(f"Number of laptops in this website is: {len(list_of_laptops)}")

df = pd.DataFrame(list_of_laptops)
# print(df)
# df.info()
# print(df.sample(8))
# print(f"Type of each column: {df.dtypes}")
# print(f"The number of different laptops: {df['Laptop_name'].nunique()}")
# print(f"The number of different laptops: {df['Description'].nunique()}")
# print(f"Number of repeated rows (equal in all cells): {df.duplicated().sum()}")
# print(f"Number of empty cells in each column: {df.isnull().sum()}")
df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
df["Price"]=df["Price"].str.replace("$" , "")
df.rename(columns={"Price":"Price ($)"} , inplace=True)
df["Price ($)"] = pd.to_numeric(df["Price ($)"], errors="coerce")
df=df.sort_values(["Price ($)" , "Laptop_name"] , ascending=[True,True]).reset_index(drop=True)
logger.info(f"Some lines of the final version of data after cleaning: \n{df.sample(5)}")

with pd.ExcelWriter("Laptops_scraping.xlsx", engine="openpyxl") as writer:  #for two sheets in excel file sheet for data and sheet for statistics
    df.to_excel(writer, sheet_name="Laptops", index=False) 
    df.describe().to_excel(writer, sheet_name="Statistics")

logger.info("You can go to Excel file to see all the data with its statistics...")

