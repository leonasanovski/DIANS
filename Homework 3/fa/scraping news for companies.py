import os
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import shutil
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pytesseract
from PIL import Image
import os
import win32com.client  # For handling .doc files
import win32com.client as win32
import PyPDF2
import win32com.client as win32
import re
import os
import docx2txt
from win32com import client as wc


def extract_first_ten_sentences_from_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

            return get_first_sentences(text, num_sentences=20)
    except Exception:
        print(f"Error extracting text from PDF.")
        return ""


def extract_first_ten_sentences_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return get_first_sentences(text, num_sentences=20)
    except Exception:
        print(f"Error extracting text from DOCX.")
        return ""


def extract_text_from_doc(doc_path, save_dir):
    try:
        print("vlegov")
        doc_path = os.path.normpath(doc_path)
        save_dir = os.path.normpath(save_dir)
        w = win32.Dispatch('Word.Application')
        print("1")
        doc = w.Documents.Open(doc_path)
        print("2")
        save_file_name = os.path.basename(doc_path).replace(".doc", ".docx")
        save_file_path = os.path.join(save_dir, save_file_name)
        doc.SaveAs(save_file_path, 16)
        print(f'name {save_file_name}')
        print(f'path {save_file_path}')
        doc.Close()
        w.Quit()
        text = extract_first_ten_sentences_from_docx(save_file_path)
        print(text)
        os.remove(save_file_path)
        return text
    except Exception as e:
        print(f"Error extracting text from .doc file")
        return ""


def get_first_sentences(text, num_sentences=7):
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    first_sentences = ' '.join(sentences[:num_sentences])
    return first_sentences


base_dir = "../data"
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.get("https://seinet.com.mk/")
wait = WebDriverWait(driver, 3)

language_button = wait.until(
    EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "#root > nav > div.header-panel-container.w-100 > div > ul > div > button")
    )
)
language_button.click()

english_selector = "#root > nav > div.header-panel-container.w-100 > div > ul > div > div > ul > li:nth-child(2)"
english_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, english_selector)))
english_button.click()

dropdown = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#formIssuerId")))

dropdown_html = dropdown.get_attribute("outerHTML")
soup = BeautifulSoup(dropdown_html, "html.parser")

companies = {}
for option in soup.find_all("option"):
    name = option.text.strip()
    value = option.get("value")
    if name and value and name.lower() != "all":
        companies[name] = value.strip()
# company_name, company_value = next(iter(companies.items()))

for company_name, company_value in companies.items():
    # if company_name == 'Agromehanika AD Skopje':
        counter = 5
        folder_path = os.path.join(base_dir, company_name)
        os.makedirs(folder_path, exist_ok=True)
        txt_file = f'C:/Users/User/Downloads/Proeckt/Proeckt/data/{company_name}/{company_name}.txt'
        with open(txt_file, 'a', encoding='utf-8') as file:
            pass
        print(f"Processing company: {company_name}")
        company_url = f"https://seinet.com.mk/search/{company_value}"
        driver.get(company_url)
        try:
            table_body = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#root > main > div.mt-3.container > div > div > div > div > table > tbody")
                )
            )
            rows = table_body.find_elements(By.TAG_NAME, "tr")
            if rows:
                k = range(8) if len(rows) >= 8 else range(len(rows))
                for i in k:
                    print(driver.current_url)
                    link = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR,
                             f"#root > main > div.mt-3.container > div > div > div > div > table > tbody > tr:nth-child({i + 1}) > td:nth-child(2)")
                        )
                    )
                    if link.text == 'Други ценовно чувствителни информации' and counter != 0:
                        flag = True
                        link.click()
                        time.sleep(2)
                        print(f"Clicked on link for row {i + 1}: {driver.current_url}")
                        try:
                            file_download_button = wait.until(
                                EC.element_to_be_clickable(
                                    (By.CSS_SELECTOR, "#root > main > div > div:nth-child(6) > div > strong > div > i")
                                )
                            )
                            div_to_check = wait.until(
                                EC.element_to_be_clickable(
                                    (By.CSS_SELECTOR, "#root > main > div > div:nth-child(6) > div > strong > div")
                                )
                            )
                        except:
                            flag = False

                        if flag and div_to_check.text.__contains__(".pdf"):
                            print(f"Downloading pdf FILE...")
                            file_download_button.click()
                            sleep(5)
                            source_path = f'C:/Users/User/Downloads/{div_to_check.text}'
                            destination_path = f'C:/Users/User/Downloads/Proeckt/Proeckt/data/{company_name}'
                            shutil.move(source_path, destination_path)
                            print(f"File moved from {source_path} to {destination_path}")
                            file_path = f'C:/Users/User/Downloads/Proeckt/Proeckt/data/{company_name}/{div_to_check.text}'
                            text = extract_first_ten_sentences_from_pdf(file_path)
                            with open(txt_file, 'a', encoding='utf-8') as file:
                                file.write(f"\n{text}")
                            os.remove(file_path)
                        elif flag and ".docx" in div_to_check.text:
                            print(f"Downloading docx file...")
                            file_download_button.click()
                            sleep(5)
                            source_path = f'C:/Users/User/Downloads/{div_to_check.text}'
                            destination_path = f'C:/Users/User/Downloads/Proeckt/Proeckt/data/{company_name}'
                            shutil.move(source_path, destination_path)
                            print(f"File moved from {source_path} to {destination_path}")
                            file_path = f'C:/Users/User/Downloads/Proeckt/Proeckt/data/{company_name}/{div_to_check.text}'
                            text = extract_first_ten_sentences_from_docx(file_path)
                            with open(txt_file, 'a', encoding='utf-8') as file:
                                file.write(f"\n{text}")
                            os.remove(file_path)
                        elif flag and ".doc" in div_to_check.text:
                            print(f"Downloading doc file...")
                            file_download_button.click()
                            sleep(5)
                            source_path = f'C:/Users/User/Downloads/{div_to_check.text}'
                            destination_path = f'C:/Users/User/Downloads'
                            text = extract_text_from_doc(source_path, destination_path)
                            with open(txt_file, 'a', encoding='utf-8') as file:
                                file.write(f"\n{text}")
                            os.remove(source_path)
                        else:
                            print(f"Vlegov na {i + 1} link")
                            while True:
                                try:
                                    paragraphs = wait.until(
                                        EC.presence_of_all_elements_located(
                                            (By.CSS_SELECTOR, "div > div > div > p")
                                        )
                                    )
                                    if paragraphs:
                                        with open(txt_file, 'a', encoding='utf-8') as file:
                                            for paragraph in paragraphs:
                                                if paragraph.text.strip():
                                                    file.write(f"{paragraph.text}\n")
                                        print(f"Appended {len(paragraphs)} paragraphs to {txt_file}.")
                                        break
                                    else:
                                        print(f"No paragraphs found!")
                                        break
                                except Exception:
                                    print(f"No more paragraphs to scrape.")
                                    break
                        driver.back()
                        counter -= 1
            else:
                print(f"No rows found for {company_name}. Skipping.")
        except Exception:
            print("Skipping to the next company.")
