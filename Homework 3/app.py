import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from io import BytesIO
import base64
import time
import matplotlib.dates as mdates
import plotly.graph_objects as go
import os
import importlib.util
from flask import Flask, render_template, request
import importlib.util
import sqlite3
from Proeckt.ta.osc_and_moving_averages import *
from Proeckt.fa.NLP import *
from Proeckt.LSTM.lstm import *
from Proeckt.LSTM.clensing_data_for_lstm import *
from Proeckt.test import *

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_PATH = 'user_profiles.db'


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)  # Connect to the SQLite database file
    connection.row_factory = sqlite3.Row  # To access rows as dictionaries (optional)
    return connection


def update_user_profile(username, email, phone, resume):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE users
        SET email = ?, phone = ?, resume = ?
        WHERE username = ?
    """, (email, phone, resume, username))

    connection.commit()
    cursor.close()
    connection.close()


# Initialize the database
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            resume TEXT  -- Add this line to store the resume
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/test_db')
def test_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return f"Tables in database: {tables}"


# Add a new user
def add_user(username, password, email, phone, resume):
    try:
        conn = sqlite3.connect(DB_PATH,timeout=50)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, email, phone, resume)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password, email, phone, resume))  # Store the resume in the database
        conn.commit()  # Commit changes to save data
        conn.close()
        return True  # Return True if the operation succeeds
    except sqlite3.IntegrityError:
        return False  # Return False if there's a duplicate entry


# Find a user by username or email
def find_user(username=None, email=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if username:
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    elif email:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    else:
        return None
    user = cursor.fetchone()
    conn.close()
    return user


# Flask routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        # Extract form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        resume = request.form['resume']  # Get the resume data

        # Add user to the database
        if add_user(username, password, email, phone, resume):
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            error = 'Username or email already exists.'
            flash('Username or email already exists.', 'danger')
            return render_template('signup.html',error=error)

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = find_user(username=username)
        if user and user[2] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password.'
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' in session:
        username = session['username']

        email = request.form['email']
        phone = request.form['phone']
        resume = request.form['resume']

        update_user_profile(username, email, phone, resume)

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    flash('You need to log in first.', 'warning')
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        user = find_user(username=username)
        if user:
            return render_template('profile.html', username=user[1], email=user[3], phone=user[4], resume=user[5])
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('home'))
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


def load_companies_from_csv():
    df = pd.read_csv('results.csv')
    return df['Компанија'].unique().tolist()


@app.route('/results', methods=['POST', 'GET'])
def results():
    selected_company = None
    selected_period = '1d'
    recommendations = []
    nlp_news_prediction = None
    lstm_prediction = None
    if request.method == 'POST':
        selected_company = request.form.get('company')
        selected_period = request.form.get('period', '1d')
    print(selected_company)
    if selected_company:
        company_data = main_for_technical_analysis(selected_company)
        print(company_data)
        lstm_prediction = function(selected_company)
        if f'nlp_prediction_{selected_company}' in session:
            nlp_news_prediction = session[f'nlp_prediction_{selected_company}']
        else:
            nlp_news_prediction = main_funct(company_name=selected_company)
            session[f'nlp_prediction_{selected_company}'] = nlp_news_prediction

        if company_data is None or company_data.empty:
            pass
        else:
            recommendation = get_detailed_recommendation_for_period(company_data, selected_company, selected_period)
            recommendations = [recommendation]

    if not selected_company:
        return redirect('/')

    return render_template(
        'analysis.html',
        selected_company=selected_company,
        recommendations=recommendations,
        selected_period=selected_period,
        nlp=nlp_news_prediction,
        lstm=lstm_prediction
    )


@app.route('/')
def home():
    companies = load_companies_from_csv()
    print(companies)
    return render_template('home.html', companies=companies)


@app.route('/company_data', methods=['GET', 'POST'])
def company_data():
    companies = load_companies_from_csv()
    company = request.form['company']
    time_span = request.form.get('time_span', '10_years')
    df = pd.read_csv('results.csv')
    company_data = df[df['Компанија'] == company]

    # Clean the 'Цена на последна трансакција' column (ensure it's numeric)
    company_data['Цена на последна трансакција'] = pd.to_numeric(
        company_data['Цена на последна трансакција'].str.replace('.', '', regex=False).str.split(',').str[0],
        errors='coerce'
    )

    company_data['Датум'] = pd.to_datetime(company_data['Датум'], format='%m/%d/%Y')

    company_data.sort_values(by='Датум', inplace=True)

    # Set 'Отворена цена' as the previous day's 'Цена на последна трансакција'
    company_data['Отворена цена'] = company_data['Цена на последна трансакција'].shift(1)

    # Handle the first row (no previous day), set opening price to the first transaction price
    company_data['Отворена цена'].fillna(company_data['Цена на последна трансакција'], inplace=True)

    end_date = company_data['Датум'].max()

    # Define the start date based on the selected time span for the table
    if time_span == '1_day':
        start_date = end_date - pd.Timedelta(days=1)
    elif time_span == '7_days':
        start_date = end_date - pd.Timedelta(days=7)
    elif time_span == '30_days':
        start_date = end_date - pd.Timedelta(days=30)
    elif time_span == '6_months':
        start_date = end_date - pd.DateOffset(days=180)
    elif time_span == '1_year':
        start_date = end_date - pd.DateOffset(days=365)
    elif time_span == '5_years':
        start_date = end_date - pd.DateOffset(days=1825)
    else:
        start_date = end_date - pd.DateOffset(days=3650)

    filtered_data_for_table = company_data[(company_data['Датум'] >= start_date) & (company_data['Датум'] <= end_date)]
    fig = go.Figure(data=[go.Candlestick(
        x=company_data['Датум'],
        open=company_data['Отворена цена'],
        high=company_data['Мак.'],
        low=company_data['Мин.'],
        close=company_data['Цена на последна трансакција']
    )])

    # Update layout to change colors and improve visibility of toolbar icons
    fig.update_layout(
        title=f"{company} Candlestick Chart ({time_span.replace('_', ' ').title()})",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,  # Hide the range slider
        plot_bgcolor='rgb(30, 30, 30)',  # Dark background for the plot area
        paper_bgcolor='rgb(40, 40, 40)',  # Dark background for the entire paper
        font=dict(
            color='white'  # Change text color to white for better visibility
        ),
        hovermode='closest',  # Set hover mode to closest
        margin=dict(l=40, r=40, t=40, b=40),  # Adjust margins to ensure no clipping
        title_font=dict(
            size=24,  # Increase title font size for better readability
            color='white',  # Title color set to white for visibility
            family="Arial, sans-serif"  # Choose a readable font
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines for dark background
            zeroline=False,  # Remove the zero line
            tickangle=45  # Rotate the tick labels for better readability
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines for dark background
            zeroline=False  # Remove the zero line
        ),
        updatemenus=[{
            'buttons': [
                {
                    'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}],
                    'label': 'Play',
                    'method': 'animate'
                },
                {
                    'args': [[''], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate'}],
                    'label': 'Pause',
                    'method': 'animate'
                }
            ],
            'direction': 'left',
            'pad': {'r': 10, 't': 87},
            'showactive': False,
            'type': 'buttons',
            'x': 0.1,
            'xanchor': 'right',
            'y': 0,
            'yanchor': 'top'
        }],
        colorway=["#00ff00", "#ff0000"],
    )

    graph_html = fig.to_html(full_html=False)
    # AKO MI SE ZAEBE TUKA E PROBLEMOT STO POSTO TREBA DA GO KASTIRAME VO INT
    page = int(request.form.get('page', 1))
    per_page = 10
    total_items = len(filtered_data_for_table)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_data = filtered_data_for_table.iloc[start_idx:end_idx]
    columns = [
        "Датум",
        "Цена на последна трансакција",
        "Мак.",
        "Мин.",
        "Просечна цена",
        "%пром.",
        "Количина",
        "Промет во БЕСТ во денари",
        "Вкупен промет во денари",
        "Компанија",
    ]

    return render_template(
        'company_data.html',
        company=company,
        data=paginated_data[columns].to_html(classes='table table-striped', index=False),
        graph_html=graph_html,
        page=page,
        total_pages=total_pages,
        time_span=time_span,
        companies=companies
    )

# UPDATED DATABASE
@app.route('/update_database', methods=['POST'])
def update_database():
    return render_template('loading.html')


@app.route('/start_update')
def start_update():
    fin()
    # clense()
    return redirect(url_for('home'))


if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)
