from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify(backend="A", message="Backend A is running")

@app.route("/api/status")
def status():
    return jsonify(backend="A", status="ok")

@app.after_request
def headers(response):
    response.headers["X-Backend"] = "A"
    return response

app.run(host="0.0.0.0", port=3001)