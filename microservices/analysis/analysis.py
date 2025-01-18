from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from technical_analysis.osc_and_moving_averages import main_for_technical_analysis, \
    get_detailed_recommendation_for_period
from functional_analysis.NLP import main_funct
from LSTM.lstm import function

app = Flask(__name__)
CORS(app)


# app.secret_key = 'your_secret_key_here'


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Retrieve data from the request
        data = request.json
        company = data.get('company')
        period = data.get('period', '1d')

        # Perform analysis
        technical_analysis = main_for_technical_analysis(company)
        recommendation = get_detailed_recommendation_for_period(technical_analysis, company, period)
        nlp_result = main_funct(company_name=company)
        lstm_result = float(function(company))  # Ensure LSTM result is converted to float

        # Convert all numeric values to native Python floats
        recommendation['oscillators'] = [float(value) if isinstance(value, (np.float32, np.float64)) else value
                                         for value in recommendation['oscillators']]
        recommendation['moving_averages'] = [float(value) if isinstance(value, (np.float32, np.float64)) else value
                                             for value in recommendation['moving_averages']]
        print("oscilators ", recommendation['oscillators'])
        print("moving_averages ", recommendation['moving_averages'])
        # Send response
        return jsonify({
            'recommendation': recommendation,
            'nlp': nlp_result,
            'lstm': lstm_result
        }), 200

    except Exception as e:
        print(f"Error in /analyze: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
    # app.run(debug=True,port=5003)
