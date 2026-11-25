const express = require("express");

const app = express();
const PORT = 3001;

app.use(express.json());

app.get("/", (req, res) => {
  res.set("X-Backend", "A");
  res.set("Cache-Control", "public, max-age=30");

  res.json({
    backend: "A",
    service: "Phase 2 Backend",
    status: "healthy",
    hostname: process.env.HOSTNAME,
    timestamp: new Date().toISOString()
  });
});

app.get("/health", (req, res) => {
  res.set("X-Backend", "A");

  res.status(200).json({
    backend: "A",
    status: "healthy"
  });
});

app.get("/api", (req, res) => {
  res.set("X-Backend", "A");
  res.set("Cache-Control", "public, max-age=30");

  res.json({
    backend: "A",
    message: "Response served by Backend A",
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Backend A listening on port ${PORT}`);
});
