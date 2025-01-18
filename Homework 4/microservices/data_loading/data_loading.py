# -*- coding: utf-8 -*-
from flask_cors import CORS
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
import pandas as pd
from flask import Response
import json

app = Flask(__name__, template_folder='../../templates')
CORS(app)
# CSV_PATH = './results.csv'

CSV_PATH = '/app/results.csv'


# app.secret_key = 'q1w2e3r4t5y6u7i8o9p0a1s2d3f4g5h6'


@app.route('/companies', methods=['GET'])
def get_companies():
    try:
        df = pd.read_csv(CSV_PATH)
        companies = df['Компанија'].unique().tolist()
        return jsonify(companies), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/company_data', methods=['POST'])
def get_company_data():
    data = request.json
    company = data.get('company')
    time_span = data.get('time_span', '10_years')

    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8')

        # Filter the data for the selected company
        company_data = df[df['Компанија'] == company].copy()

        # Convert `Датум` to datetime and drop invalid rows
        company_data['Датум'] = pd.to_datetime(company_data['Датум'], format='%m/%d/%Y', errors='coerce')
        company_data.dropna(subset=['Датум'], inplace=True)
        company_data.sort_values(by='Датум', inplace=True)

        # Apply time span filtering
        end_date = company_data['Датум'].max()
        if time_span == '1_day':
            start_date = end_date - pd.Timedelta(days=1)
        elif time_span == '7_days':
            start_date = end_date - pd.Timedelta(days=7)
        elif time_span == '30_days':
            start_date = end_date - pd.Timedelta(days=30)
        elif time_span == '6_months':
            start_date = end_date - pd.DateOffset(months=6)
        elif time_span == '1_year':
            start_date = end_date - pd.DateOffset(years=1)
        elif time_span == '5_years':
            start_date = end_date - pd.DateOffset(years=5)
        else:
            start_date = end_date - pd.DateOffset(years=10)

        filtered_data = company_data[company_data['Датум'] >= start_date]

        if filtered_data.empty:
            return jsonify([]), 200

        # Replace NaN with empty strings or null
        filtered_data = filtered_data.fillna("")  # Replace NaN with ""

        # Convert `Timestamp` to string
        filtered_data['Датум'] = filtered_data['Датум'].dt.strftime('%Y-%m-%d')

        # Serialize DataFrame to JSON
        response_json = json.dumps(
            filtered_data.to_dict(orient='records'),
            ensure_ascii=False  # Preserve Cyrillic characters
        )
        return Response(response_json, mimetype='application/json', status=200)

    except Exception as e:
        error_message = {'error': str(e)}
        return Response(json.dumps(error_message, ensure_ascii=False), mimetype='application/json', status=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
    # app.run(port=5005, debug=True)
