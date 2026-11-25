const express = require("express");

const app = express();
const PORT = 3002;

app.use(express.json());

app.get("/", (req, res) => {
  res.set("X-Backend", "B");
  res.set("Cache-Control", "public, max-age=30");

  res.json({
    backend: "B",
    service: "Phase 2 Backend",
    status: "healthy",
    hostname: process.env.HOSTNAME,
    timestamp: new Date().toISOString()
  });
});

app.get("/health", (req, res) => {
  res.set("X-Backend", "B");

  res.status(200).json({
    backend: "B",
    status: "healthy"
  });
});

app.get("/api", (req, res) => {
  res.set("X-Backend", "B");
  res.set("Cache-Control", "public, max-age=30");

  res.json({
    backend: "B",
    message: "Response served by Backend B",
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Backend B listening on port ${PORT}`);
});
