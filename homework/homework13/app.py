from flask import Flask, request, jsonify
import joblib

# loaded ONCE, at startup - not inside a route
model = joblib.load('model/model.pkl')
app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict_post():
    data = request.get_json(silent=True) or {}
    features = data.get('features')
    if not isinstance(features, list) or len(features) != 2:
        return jsonify({'error': 'send JSON {"features": [f1, f2]} with exactly 2 numbers'}), 400
    try:
        row = [float(x) for x in features]
    except (TypeError, ValueError):
        return jsonify({'error': 'both features must be numbers'}), 400
    prediction = model.predict([row])[0]
    return jsonify({'prediction': float(prediction)})


@app.route('/predict/<f1>/<f2>', methods=['GET'])
def predict_get(f1, f2):
    try:
        row = [float(f1), float(f2)]
    except ValueError:
        return jsonify({'error': 'both path values must be numbers'}), 400
    prediction = model.predict([row])[0]
    return jsonify({'prediction': float(prediction)})


if __name__ == '__main__':
    # port 5001, not 5000: on macOS the Control Center / AirPlay Receiver also
    # listens on 5000 and answers first with HTTP 403.
    app.run(port=5001)
