from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.route("/")
def home():
    response = make_response(jsonify(
        backend="B",
        message="Backend B is running"
    ))
    response.headers["X-Backend"] = "B"
    return response

@app.route("/api/status")
def status():
    etag = '"backend-b-v1"'

    if request.headers.get("If-None-Match") == etag:
        response = make_response("", 304)
        response.headers["X-Backend"] = "B"
        response.headers["Cache-Control"] = "public, max-age=30"
        response.headers["ETag"] = etag
        return response

    response = make_response(jsonify(
        backend="B",
        status="ok"
    ))
    response.headers["X-Backend"] = "B"
    response.headers["Cache-Control"] = "public, max-age=30"
    response.headers["ETag"] = etag
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3002)