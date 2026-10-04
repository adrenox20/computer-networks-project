const http = require("http");

const server = http.createServer((req, res) => {
  res.setHeader("Content-Type", "application/json");
  res.setHeader("X-Backend", "B");

  if (req.url === "/") {
    res.end(JSON.stringify({
      backend: "B",
      message: "Backend B is running"
    }));
  } else if (req.url === "/api/status") {
    const etag = '"backend-b-v1"';

    res.setHeader("Cache-Control", "public, max-age=30");
    res.setHeader("ETag", etag);

    if (req.headers["if-none-match"] === etag) {
      res.statusCode = 304;
      res.end();
      return;
    }

    res.end(JSON.stringify({
      backend: "B",
      status: "ok"
    }));
  } else {
    res.statusCode = 404;
    res.end(JSON.stringify({ error: "Not found" }));
  }
});

server.listen(3002, "0.0.0.0", () => {
  console.log("Backend B running on port 3002");
});