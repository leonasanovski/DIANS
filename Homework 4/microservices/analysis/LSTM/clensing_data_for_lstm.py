# -*- coding: utf-8 -*-
import os.path
import missingno as msno
import pandas as pd
import matplotlib.pyplot as plt


def clense():
    data = pd.read_csv('../../../results.csv')

    print(data.isnull().sum())

    numeric_columns = [
        "Цена на последна трансакција",
        "Мак.",
        "Мин.",
        "Просечна цена",
        "%пром.",
        "Промет во БЕСТ во денари",
        "Вкупен промет во денари",
    ]

    for column in numeric_columns:
        data[column] = (
            data[column]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        data[column] = pd.to_numeric(data[column], errors="coerce")

    print(data.isnull().sum())
    msno.matrix(data)
    plt.show()
    data["Датум"] = pd.to_datetime(data["Датум"], format="%m/%d/%Y", errors="coerce")
    data = data.drop(columns=['Мак.', 'Мин.'])
    data["%пром."] = data["%пром."].interpolate(limit_direction='both', method="spline", order=3)
    data['Цена на последна трансакција'] = data['Цена на последна трансакција'].interpolate(limit_direction='both',
                                                                                            method="spline", order=3)
    data['Просечна цена'] = data['Просечна цена'].interpolate(limit_direction='both', method="spline", order=3)

    print(data.isnull().sum())

    if os.path.exists('cleaned_results.csv'):
        os.remove('cleaned_results.csv')
    data.to_csv('cleaned_results.csv', index=False)
