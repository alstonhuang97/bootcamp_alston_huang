# Stage 13 Homework - Prediction API

A `LinearRegression` model trained on a synthetic 2-feature dataset from scikit-learn's
`make_regression` (100 samples, noise=0.1, random_state=42). It takes two numeric features
and returns a single continuous predicted value.

## Running it

    python app.py

The server starts on http://127.0.0.1:5001 and loads model/model.pkl once at startup.
(Port 5001, not 5000: on macOS the Control Center / AirPlay Receiver also listens on 5000.)

## POST /predict

    curl -X POST http://127.0.0.1:5001/predict \
         -H "Content-Type: application/json" \
         -d "{\"features\": [0.1, 0.2]}"

Response: 200 {"prediction":23.58961171297328}

## GET /predict/<f1>/<f2>

    curl http://127.0.0.1:5001/predict/0.1/0.2

Response: 200 {"prediction":23.58961171297328}

## Bad input

Every bad request returns HTTP 400 with a JSON `error` field instead of a traceback:

- `GET /predict/abc/0.2` (not a number) -> {"error":"both path values must be numbers"}
- `POST /predict` with `features` missing or not exactly 2 values ->
  {"error":"send JSON {\"features\": [f1, f2]} with exactly 2 numbers"}
- `POST /predict` with non-numeric values -> {"error":"both features must be numbers"}
