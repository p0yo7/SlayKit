import pandas as pd
import numpy as np
from pandas.tseries.offsets import DateOffset
import joblib

# Cargar modelos
model = joblib.load("subscription_model.pkl")
encoder = joblib.load("label_encoder.pkl")

# Cargar datasets
df_clientes = pd.read_csv("datos/base_clientes_final.csv", parse_dates=["fecha_nacimiento", "fecha_alta"])
df_transacciones = pd.read_csv("datos/base_transacciones_final.csv", parse_dates=["fecha"])

# === Preprocesamiento base ===
df_transacciones['anio'] = df_transacciones['fecha'].dt.year
df_transacciones['mes'] = df_transacciones['fecha'].dt.month
df_transacciones['dia'] = df_transacciones['fecha'].dt.day

# Asumimos que comercio_encoded no está en CSV original
df_transacciones['comercio_encoded'] = encoder.transform(df_transacciones['comercio'])

# === Funciones auxiliares ===

def predict_next_month_spending(user_df):
    results = {}

    monthly_spending = user_df.groupby(['anio', 'mes'])['monto'].sum().reset_index()
    monthly_spending = monthly_spending.sort_values(['anio', 'mes'])
    monthly_spending['month_index'] = np.arange(len(monthly_spending))

    X_total = monthly_spending[['month_index']]
    y_total = monthly_spending['monto']
    from sklearn.linear_model import LinearRegression
    reg_total = LinearRegression().fit(X_total, y_total)

    next_month_index = np.array([[monthly_spending['month_index'].max() + 1]])
    predicted_total = reg_total.predict(next_month_index)[0]
    results['total'] = predicted_total

    results['per_merchant'] = {}

    for merchant in user_df['comercio'].unique():
        merchant_df = user_df[user_df['comercio'] == merchant]
        monthly = merchant_df.groupby(['anio', 'mes'])['monto'].sum().reset_index()
        monthly = monthly.sort_values(['anio', 'mes'])
        monthly['month_index'] = np.arange(len(monthly))

        if len(monthly) < 2:
            results['per_merchant'][merchant] = monthly['monto'].iloc[-1]
            continue

        X = monthly[['month_index']]
        y = monthly['monto']
        reg = LinearRegression().fit(X, y)
        next_idx = np.array([[monthly['month_index'].max() + 1]])
        pred = reg.predict(next_idx)[0]
        if pred < 0:
            continue
        results['per_merchant'][merchant] = pred

    return predicted_total, results

def predict_next_month_subscriptions(user_id):
    user_df = df_transacciones[df_transacciones['id'] == user_id].copy()
    if user_df.empty:
        return pd.DataFrame(), 0.0

    feature_columns = ['comercio_encoded', 'anio', 'mes', 'dia', 'monto']
    user_df['subscription_prediction'] = model.predict(user_df[feature_columns])
    predicted_subs = user_df[user_df['subscription_prediction'] == 1].copy()

    if predicted_subs.empty:
        return pd.DataFrame(), 0.0

    most_recent_date = user_df['fecha'].max()
    cutoff_date = most_recent_date - DateOffset(months=3)
    recent_subs = predicted_subs[predicted_subs['fecha'] >= cutoff_date].copy()

    if recent_subs.empty:
        return pd.DataFrame(), 0.0

    last_month = most_recent_date.month
    next_month = last_month + 1 if last_month < 12 else 1
    next_year = most_recent_date.year if next_month != 1 else most_recent_date.year + 1

    frequent_days = recent_subs.groupby('comercio')['dia'].agg(lambda x: x.mode().tolist()).reset_index()
    frequent_days = frequent_days.explode('dia')
    base = recent_subs.drop_duplicates(subset='comercio', keep='first').drop(columns='dia')
    next_month_candidates = frequent_days.merge(base, on='comercio')
    next_month_candidates['mes'] = next_month
    next_month_candidates['anio'] = next_year

    X_next_month = next_month_candidates[feature_columns]
    next_month_candidates['subscription_prediction'] = model.predict(X_next_month)
    next_month_subs = next_month_candidates[next_month_candidates['subscription_prediction'] == 1]

    return next_month_subs[['comercio', 'monto', 'anio', 'mes', 'dia']]

def iconic_expense(user_df):
    unique_counts = user_df['comercio'].value_counts()
    most_unique_commerce = unique_counts.idxmin()
    most_unique_count = unique_counts.min()
    return most_unique_commerce, most_unique_count

def all_predictions(user_id):
    user_df = df_transacciones[df_transacciones['id'] == user_id].copy()
    if user_df.empty:
        return None

    total_spending, per_merchant_spending = predict_next_month_spending(user_df)
    predicted_subs = predict_next_month_subscriptions(user_id)
    iconic_commerce, iconic_count = iconic_expense(user_df)

    if isinstance(predicted_subs, pd.DataFrame):
        predicted_subs = predicted_subs.to_dict(orient='records')

    result = {
        'total_spending': float(total_spending),
        'per_merchant_spending': {
            str(k): float(v) for k, v in per_merchant_spending.get('per_merchant', {}).items()
        },
        'predicted_subs': predicted_subs,
        'iconic_commerce': str(iconic_commerce),
        'iconic_count': int(iconic_count)
    }

    return result
