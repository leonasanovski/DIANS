import aiohttp
from bs4 import BeautifulSoup
import os
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import time


def swap_commas_and_dots(value):
    return value.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')


# Singleton pattern for managing aiohttp ClientSession
class SingletonSession:
    _instance = None

    @staticmethod
    def get_instance():
        if SingletonSession._instance is None:
            SingletonSession._instance = aiohttp.ClientSession()
        return SingletonSession._instance

    @staticmethod
    async def close_instance():
        if SingletonSession._instance is not None:
            await SingletonSession._instance.close()


# "FILTER 1" to fetch company information from the Macedonian stock exchange
async def fetch_companies(session, url):
    companies = []
    async with session.get(url) as response:
        data = await response.text()
        soup = BeautifulSoup(data, 'html.parser')
        for option in soup.select("#Code > option"):
            if not any(char.isdigit() for char in option.text):
                companies.append(option.text)
    return companies


# Filter 2 functions for data collection over a 10-year period
def get_last_recorded_date(company_code, csv_file):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        company_data = df[df['Компанија'] == company_code]
        if not company_data.empty:
            last_date = company_data['Датум'].max()
            return datetime.strptime(last_date, "%m/%d/%Y")
    ten_years_ago = datetime.now() - timedelta(days=365 * 10)
    return ten_years_ago


def get_date_ranges_for_update(company_code, csv_file):
    last_date = get_last_recorded_date(company_code, csv_file)
    start_year = last_date.year
    end_year = datetime.now().year
    date_ranges = [(f"01/01/{year}", f"12/31/{year}") for year in range(start_year, end_year + 1)]
    date_ranges[-1] = (f"01/01/{end_year}", datetime.now().strftime("%m/%d/%Y"))
    return date_ranges


# This function is used to write data in Filter 2 and Filter 3
async def fetch_missing_data(session, company_code, date_ranges):
    all_rows = []
    for from_date, to_date in date_ranges:
        to_date_obj = datetime.strptime(to_date, "%m/%d/%Y")
        if from_date == to_date == to_date_obj:
            return all_rows

        url = f"https://www.mse.mk/en/stats/symbolhistory/{company_code}"
        params = {
            'FromDate': from_date,
            'ToDate': to_date,
            'Code': company_code,
        }

        async with session.get(url, params=params) as response:
            data = await response.text()
            soup = BeautifulSoup(data, 'html.parser')

            for row in soup.select("#resultsTable tbody tr"):
                tds = row.text.split("\n")
                try:
                    date_str = tds[1].strip()
                    formatted_date = datetime.strptime(date_str, "%m/%d/%Y").strftime("%m/%d/%Y")
                except ValueError:
                    print(f"Skipping invalid date format: {tds[1]}")
                    continue

                all_rows.append({
                    "Датум": formatted_date,
                    "Цена на последна трансакција": swap_commas_and_dots(tds[2]),
                    "Мак.": swap_commas_and_dots(tds[3]),
                    "Мин.": swap_commas_and_dots(tds[4]),
                    "Просечна цена": swap_commas_and_dots(tds[5]),
                    "%пром.": swap_commas_and_dots(tds[6]),
                    "Количина": swap_commas_and_dots(tds[7]),
                    "Промет во БЕСТ во денари": swap_commas_and_dots(tds[8]),
                    "Вкупен промет во денари": swap_commas_and_dots(tds[9]),
                    "Компанија": company_code,
                })
    return all_rows


# Function to save the data into a CSV file
async def save_to_csv(rows):
    file_path = "results.csv"
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path)
    else:
        existing_data = pd.DataFrame()

    new_data = pd.DataFrame(rows)
    new_data["Датум"] = pd.to_datetime(new_data["Датум"], format="%m/%d/%Y")

    if not existing_data.empty:
        existing_data["Датум"] = pd.to_datetime(existing_data["Датум"], format="%m/%d/%Y")

    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    updated_data.drop_duplicates(subset=["Датум", "Компанија"], keep='last', inplace=True)
    updated_data["Датум"] = updated_data["Датум"].dt.strftime("%m/%d/%Y")  # Format date to MM/dd/yyyy
    updated_data.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")


async def main():
    # Get singleton session instance
    session = SingletonSession.get_instance()

    url = "https://www.mse.mk/mk/stats/symbolhistory/alk"
    companies = await fetch_companies(session, url)

    tasks = []
    for company in companies:
        date_ranges = get_date_ranges_for_update(company, "results.csv")
        tasks.append(fetch_missing_data(session, company, date_ranges))

    all_data_batches = await asyncio.gather(*tasks)
    all_data = [row for company_data in all_data_batches for row in company_data]

    await save_to_csv(all_data)

    # Close the session after all tasks are done
    await SingletonSession.close_instance()


def fin():
    asyncio.run(main())


if __name__ == '__main__':
    start_time = time.time()
    fin()
    print(f"Execution time was {int((time.time() - start_time) / 60)}:{int((time.time() - start_time) % 60)}")
