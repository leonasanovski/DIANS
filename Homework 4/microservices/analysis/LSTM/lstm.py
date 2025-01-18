# -*- coding: utf-8 -*-
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import numpy as np
from tensorflow.keras.callbacks import EarlyStopping
import concurrent.futures

def predict(model, last_data, target_scaler, X_shape, lag):
    tomorrow_prediction = model.predict(last_data)
    predicted_price = target_scaler.inverse_transform(np.array(tomorrow_prediction).reshape(-1, 1))
    return predicted_price[0][0]


def function(company_name):
    csv_path = './LSTM/cleaned_results.csv'
    df = pd.read_csv(csv_path)
    df = df[df['Компанија'] == company_name]
    df = df.drop(columns=['Компанија', 'Количина'])

    df["Датум"] = pd.to_datetime(df["Датум"])
    df.set_index(keys=["Датум"], inplace=True)
    df.sort_index(inplace=True)
    df = df["2023-01-01":].copy(deep=True)
    lag = 7
    df_lagged = df.copy()

    feature_scaler = MinMaxScaler(feature_range=(0, 1))
    target_scaler = MinMaxScaler(feature_range=(0, 1))

    df_lagged_scaled = df_lagged.copy()
    for col in df.columns:
        if col != 'Цена на последна трансакција':
            df_lagged_scaled[col] = feature_scaler.fit_transform(df_lagged[[col]])

    df_lagged_scaled['Цена на последна трансакција'] = target_scaler.fit_transform(
        df_lagged[['Цена на последна трансакција']])

    for col in df_lagged_scaled.columns:
        for i in range(1, lag + 1):
            df_lagged_scaled[f"{col}_{i}"] = df_lagged_scaled[col].shift(i)

    df_lagged_scaled = df_lagged_scaled.drop(columns=[
        '%пром.', 'Промет во БЕСТ во денари', 'Просечна цена', 'Вкупен промет во денари'])
    df_lagged_scaled.dropna(inplace=True)

    X, y = df_lagged_scaled.drop(columns=["Цена на последна трансакција"]), df_lagged_scaled[
        "Цена на последна трансакција"]
    train_X, test_X, train_y, test_y = train_test_split(X, y, shuffle=False)

    train_X = train_X.values.reshape(train_X.shape[0], lag, (train_X.shape[1] // lag))
    test_X = test_X.values.reshape(test_X.shape[0], lag, (test_X.shape[1] // lag))

    all_predictions = []

    # Run the model 3 times
    for i in range(5):
        # Define and compile the model
        model = Sequential([
            LSTM(36, return_sequences=True, input_shape=(train_X.shape[1], train_X.shape[2]), activation='relu'),
            LSTM(15, return_sequences=False, activation='relu'),
            Dense(1, activation='linear')
        ])
        print(f"Model run {i + 1}")
        model.compile(
            loss="mean_squared_error",
            optimizer="adam",
            metrics=["mean_squared_error"]
        )

        # Define early stopping callback
        early_stopping = EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True)

        # Train the model
        history = model.fit(train_X, train_y, validation_split=0.3, epochs=13, batch_size=16, verbose=1, shuffle=False,
                            callbacks=[early_stopping])

        # Plot the loss curve
        sns.lineplot(history.history['loss'][1:], label=f'Run {i + 1} loss')
        sns.lineplot(history.history['val_loss'][1:], label=f'Run {i + 1} val_loss')

        # plt.show()

        # Get the last data point to predict the next value
        last_data = df_lagged_scaled.iloc[-1][:-1].values.reshape(1, lag, X.shape[1] // lag)

        # Use multi-threading to make multiple predictions
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(predict, model, last_data, target_scaler, X.shape, lag) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Calculate the average prediction from multiple results
        average_prediction = np.mean(results)
        print(f"Prediction from model run {i + 1}: {average_prediction}")

        # Append the average prediction to the list
        all_predictions.append(average_prediction)

    # Calculate the overall average prediction from all runs
    overall_average_prediction = np.mean(all_predictions)
    print(f"Overall average prediction from 5 runs: {overall_average_prediction}")
    return overall_average_prediction


if __name__ == '__main__':
    company_name = 'ZUAS'
    function(company_name)
