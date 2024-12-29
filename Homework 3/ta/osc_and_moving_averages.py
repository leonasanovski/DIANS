import pandas as pd
import numpy as np


# OSCILATORS
def calculate_rsi(data, period=14):
    delta = data['Цена на последна трансакција'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_stochastic(data, period=14):
    low_min = data['Цена на последна трансакција'].rolling(window=period).min()
    high_max = data['Цена на последна трансакција'].rolling(window=period).max()
    return 100 * ((data['Цена на последна трансакција'] - low_min) / (high_max - low_min))


def calculate_cci(data, period=14):
    typical_price = data['Цена на последна трансакција']
    sma = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    return (typical_price - sma) / (0.015 * mean_deviation)


def calculate_momentum(data, period=14):
    return data['Цена на последна трансакција'].diff(periods=period)


def calculate_demark(data, period=14):
    return pd.Series([np.nan] * len(data), index=data.index)


# MOVINGA AVERAGES
def calculate_sma(data, period=14):
    return data['Цена на последна трансакција'].rolling(window=period).mean()


def calculate_ema(data, period=14):
    return data['Цена на последна трансакција'].ewm(span=period, adjust=False).mean()


def calculate_wma(data, period=14):
    weights = np.arange(1, period + 1)
    return data['Цена на последна трансакција'].rolling(window=period).apply(
        lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)


def calculate_smma(data, period=14):
    smma = [np.nan] * (period - 1)
    sma = data['Цена на последна трансакција'].rolling(window=period).mean()
    smma.append(sma.iloc[period - 1])
    for i in range(period, len(data)):
        smma.append((smma[-1] * (period - 1) + data['Цена на последна трансакција'].iloc[i]) / period)
    return smma


def calculate_vwma(data, period=14):
    vwma = [np.nan] * (period - 1)
    for i in range(period - 1, len(data)):
        price_volume_sum = np.sum(
            data['Цена на последна трансакција'].iloc[i - period + 1:i + 1] * data['Количина'].iloc[
                                                                              i - period + 1:i + 1]
        )
        volume_sum = np.sum(data['Количина'].iloc[i - period + 1:i + 1])
        vwma.append(price_volume_sum / volume_sum if volume_sum != 0 else np.nan)
    return pd.Series(vwma, index=data.index)


def calculate_indicators(data, period):
    data[f'RSI_{period}'] = calculate_rsi(data, period)
    data[f'Stochastic_{period}'] = calculate_stochastic(data, period)
    data[f'CCI_{period}'] = calculate_cci(data, period)
    data[f'Momentum_{period}'] = calculate_momentum(data, period)
    data[f'DeMark_{period}'] = calculate_demark(data, period)
    data[f'SMA_{period}'] = calculate_sma(data, period)
    data[f'EMA_{period}'] = calculate_ema(data, period)
    data[f'WMA_{period}'] = calculate_wma(data, period)
    data[f'SMMA_{period}'] = calculate_smma(data, period)
    data[f'VWMA_{period}'] = calculate_vwma(data, period)
    return data


# Generate signals
def generate_signals(data, period):
    signals = []

    for index, row in data.iterrows():
        rsi_signal = 'Buy' if row[f'RSI_{period}'] < 40 else ('Sell' if row[f'RSI_{period}'] > 60 else 'Hold')
        stochastic_signal = 'Buy' if row[f'Stochastic_{period}'] < 30 else (
            'Sell' if row[f'Stochastic_{period}'] > 70 else 'Hold')
        cci_signal = 'Buy' if row[f'CCI_{period}'] < -50 else ('Sell' if row[f'CCI_{period}'] > 50 else 'Hold')
        momentum_signal = 'Buy' if row[f'Momentum_{period}'] > 0.1 else (
            'Sell' if row[f'Momentum_{period}'] < -0.1 else 'Hold')
        demark_signal = 'Hold'

        signals_list = [rsi_signal, stochastic_signal, cci_signal, momentum_signal, demark_signal]
        final_signal = 'Buy' if signals_list.count('Buy') > signals_list.count('Sell') else (
            'Sell' if signals_list.count('Sell') > signals_list.count('Buy') else 'Hold')
        signals.append(final_signal)

    data[f'Signal_{period}'] = signals

    return data


def all_in_one_function(data, company_name):
    company_data = data[data["Компанија"] == company_name].sort_values("Датум")
    for period in [1, 7, 30]:
        company_data = calculate_indicators(company_data, period=period)
        company_data = generate_signals(company_data, period=period)
    return company_data


def get_detailed_recommendation_for_period(data, selected_company, period):
    if period == '1d':
        period_days = 1
    elif period == '7d':
        period_days = 7
    elif period == '1m':
        period_days = 30
    else:
        raise ValueError("Invalid period. Use '1d', '7d', or '1m'.")

    latest_row = data.iloc[-1]

    oscillators = [
        round(latest_row[f'RSI_{period_days}'], 2) if not pd.isna(
            latest_row[f'RSI_{period_days}']) else "Not enough data provided",
        round(latest_row[f'Stochastic_{period_days}'], 2) if not pd.isna(
            latest_row[f'Stochastic_{period_days}']) else "Not enough data provided",
        round(latest_row[f'CCI_{period_days}'], 2) if not pd.isna(
            latest_row[f'CCI_{period_days}']) else "Not enough data provided",
        round(latest_row[f'Momentum_{period_days}'], 2) if not pd.isna(
            latest_row[f'Momentum_{period_days}']) else "Not enough data provided",
        round(latest_row[f'DeMark_{period_days}'], 2) if not pd.isna(
            latest_row[f'DeMark_{period_days}']) else "Not enough data provided",
    ]

    moving_averages = [
        round(latest_row[f'SMA_{period_days}'], 2) if not pd.isna(
            latest_row[f'SMA_{period_days}']) else "Not enough data provided",
        round(latest_row[f'EMA_{period_days}'], 2) if not pd.isna(
            latest_row[f'EMA_{period_days}']) else "Not enough data provided",
        round(latest_row[f'WMA_{period_days}'], 2) if not pd.isna(
            latest_row[f'WMA_{period_days}']) else "Not enough data provided",
        round(latest_row[f'SMMA_{period_days}'], 2) if not pd.isna(
            latest_row[f'SMMA_{period_days}']) else "Not enough data provided",
        round(latest_row[f'VWMA_{period_days}'], 2) if not pd.isna(
            latest_row[f'VWMA_{period_days}']) else "Not enough data provided",
    ]

    final_signal = latest_row[f'Signal_{period_days}'] if not pd.isna(
        latest_row[f'Signal_{period_days}']) else "Not enough data provided"

    return {
        'period': period,
        'oscillators': oscillators,
        'moving_averages': moving_averages,
        'recommendation': final_signal,
    }


def main_for_technical_analysis(company):
    company_name = company
    data = pd.read_csv('C:/Users/User/Downloads/Proeckt/Proeckt/LSTM/cleaned_results.csv')
    data = all_in_one_function(data, company_name)
    return data


if __name__ == '__main__':
    main_for_technical_analysis('MPT').tail(1).to_csv('test.csv')
