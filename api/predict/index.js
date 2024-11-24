const { spawn } = require("child_process");
const path = require("path");

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader("Access-Control-Allow-Credentials", true);
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET,OPTIONS,PATCH,DELETE,POST,PUT"
  );
  res.setHeader(
    "Access-Control-Allow-Headers",
    "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
  );

  // Handle OPTIONS request
  if (req.method === "OPTIONS") {
    res.status(200).end();
    return;
  }

  // Only allow POST requests
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const pythonProcess = spawn("python", [
      path.join(__dirname, "predict.py"),
      JSON.stringify(req.body),
    ]);

    let result = "";
    let error = "";

    pythonProcess.stdout.on("data", (data) => {
      result += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      error += data.toString();
    });

    pythonProcess.on("close", (code) => {
      try {
        const prediction = JSON.parse(result);
        const { processed_features, ...cleanResponse } = prediction;
        res.json(cleanResponse);
      } catch (err) {
        res.status(500).json({
          status: "error",
          message: "Failed to process prediction",
          details: error || err.message,
        });
      }
    });
  } catch (error) {
    res.status(500).json({ error: "Failed to process request" });
  }
};
