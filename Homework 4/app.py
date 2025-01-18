from flask import Flask, request, redirect, url_for, render_template, flash, session
import requests
import os

app = Flask(__name__)
app.secret_key = 'b1a2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'

# Microservice URLs
# USER_SERVICE_URL = 'http://127.0.0.1:5001'
# DATA_SERVICE_URL = 'http://127.0.0.1:5005'
# ANALYSIS_SERVICE_URL = 'http://127.0.0.1:5003'

# Docker
USER_SERVICE_URL = 'http://user_management:5001'
DATA_SERVICE_URL = 'http://data_loading:5005'
ANALYSIS_SERVICE_URL = 'http://analysis:5003'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username')
    password = request.form.get('password')
    print(username, password)
    try:
        response = requests.post(f'{USER_SERVICE_URL}/login', json={'username': username, 'password': password})
        print(response.status_code)
        if response.status_code == 200:
            session['username'] = username
            return redirect(url_for('home'))
        elif response.status_code == 404:
            flash('Username does not exist.', 'danger')
        elif response.status_code == 401:
            flash('Incorrect password.', 'danger')
        else:
            flash('Invalid login information.', 'danger')
    except requests.exceptions.RequestException:
        flash("Unable to connect to the login service. Please try again later.", "danger")

    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    user_data = {
        'username': request.form['username'],
        'password': request.form['password'],
        'email': request.form['email']
    }

    try:
        response = requests.post(f'{USER_SERVICE_URL}/signup', json=user_data)
        if response.status_code == 201:
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        elif response.status_code == 400:
            error_message = response.json().get('error', 'Invalid information provided.')
            flash(error_message, 'danger')
        else:
            flash('An unknown error occurred during signup.', 'danger')
    except requests.exceptions.RequestException:
        flash("Unable to connect to the server. Please try again later.", "danger")

    return redirect(url_for('signup'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/')
def home():
    if 'username' not in session:
        flash('Please log in to access the home page.', 'warning')
        return redirect(url_for('login'))

    try:
        response = requests.get(f"{DATA_SERVICE_URL}/companies")
        if response.status_code == 200:
            companies = response.json()
        else:
            flash('Failed to fetch company list.', 'danger')
            companies = []
    except Exception as e:
        flash(f'Error fetching companies: {str(e)}', 'danger')
        companies = []

    return render_template('home.html', companies=companies)


@app.route('/company_data', methods=['POST'])
def company_data():
    print("Entered company_data route.")
    company = request.form['company']
    time_span = request.form.get('time_span', '10_years')
    page = int(request.form.get('page', 1))
    per_page = 10

    payload = {'company': company, 'time_span': time_span}
    try:
        response = requests.post(f'{DATA_SERVICE_URL}/company_data', json=payload)
        print("Response Status Code:", response.status_code)
        print("Raw Response Text:", response.text)  # Log the raw response

        if response.status_code == 200:
            try:
                data = response.json()
                print("Parsed Data:", data)  # Debug parsed JSON
            except ValueError as e:
                print(f"JSON Decode Error: {e}")
                flash('Invalid response format from the Data Loading Microservice.', 'danger')
                return redirect(url_for('home'))

            total_items = len(data)
            total_pages = (total_items + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_data = data[start_idx:end_idx]

            return render_template(
                'company_data.html',
                company=company,
                data=paginated_data,
                time_span=time_span,
                page=page,
                total_pages=total_pages
            )
        else:
            flash(response.json().get('error', 'Failed to fetch company data.'), 'danger')
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Data Loading Microservice: {e}")
        flash(f'Error communicating with Data Loading Microservice: {str(e)}', 'danger')

    return redirect(url_for('home'))


@app.route('/results', methods=['POST'])
def results():
    selected_company = request.form.get('company')
    selected_period = request.form.get('period', '1d')

    try:
        response = requests.post(f'{ANALYSIS_SERVICE_URL}/analyze',
                                 json={'company': selected_company, 'period': selected_period})
        if response.status_code == 200:

            analysis_results = response.json()
            print("Analysis Results:", analysis_results)
            recommendation = analysis_results.get('recommendation', {})
            return render_template(
                'analysis.html',
                selected_company=selected_company,
                recommendations=recommendation,
                oscillators=recommendation.get('oscillators', []),
                moving_averages=recommendation.get('moving_averages', []),
                recomended_from_calculations=recommendation.get('recommendation', "No Recommendation Available"),
                nlp=analysis_results.get('nlp', 'No analysis'),
                lstm=analysis_results.get('lstm', 'No prediction')
            )

        else:
            flash(f"Failed to analyze data: {response.json().get('error', 'Unknown error')}", 'danger')
    except Exception as e:
        flash(f"Error fetching analysis: {str(e)}", 'danger')

    return redirect(url_for('home'))


@app.route('/analyze', methods=['POST'])
def analyze():
    company = request.form['company']
    period = request.form['period']

    payload = {'company': company, 'period': period}
    response = requests.post(f'{ANALYSIS_SERVICE_URL}/analyze', json=payload)

    if response.status_code == 200:
        analysis_results = response.json()
        return render_template(
            'analysis.html',
            selected_company=company,
            recommendations=analysis_results.get('recommendations'),
            nlp=analysis_results.get('nlp'),
            lstm=analysis_results.get('lstm')
        )
    flash('Failed to analyze company data.', 'danger')
    return redirect(url_for('home'))


@app.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        if 'username' in session:
            username = session['username']
            email = request.form['email']
            phone = request.form['phone']
            resume = request.form['resume']

            # Call the microservice
            response = requests.post(
                f'{USER_SERVICE_URL}/update_profile',
                json={'username': username, 'email': email, 'phone': phone, 'resume': resume}
            )

            if response.status_code == 200:
                flash('Profile updated successfully!', 'success')
            else:
                error_message = response.json().get('error', 'Failed to update profile')
                flash(f"Error updating profile: {error_message}", 'danger')
        else:
            flash('You need to log in first.', 'warning')
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'danger')

    return redirect(url_for('profile'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session.get('username')
    if not username:
        flash("You need to log in first.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        resume = request.form.get('resume')

        try:
            response = requests.post(f'{USER_SERVICE_URL}/update_profile', json={
                'username': username,
                'email': email,
                'phone': phone,
                'resume': resume
            })

            if response.status_code == 200:
                flash("Profile updated successfully!", "success")
            else:
                error_message = response.json().get('error', 'An error occurred.')
                flash(f"Profile update failed: {error_message}", "danger")

        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "danger")

    try:
        response = requests.get(f'{USER_SERVICE_URL}/profile', params={'username': username})
        if response.status_code == 200:
            user = response.json()
        else:
            flash("Failed to load profile data.", "danger")
            user = {'email': '', 'phone': '', 'resume': ''}  # Default values
    except Exception as e:
        flash(f"An error occurred while fetching profile: {str(e)}", "danger")
        user = {'email': '', 'phone': '', 'resume': ''}  # Default values

    return render_template('profile.html', user=user)


@app.route('/update_database', methods=['POST'])
def update_database():
    return render_template('loading.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    # app.run(port=5000, debug=True)
