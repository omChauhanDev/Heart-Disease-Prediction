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
    // Try different Python executable names
    const pythonCommands = ["python3", "python"];
    let pythonProcess = null;
    let errorMessage = "";

    // Try each Python command until one works
    for (const cmd of pythonCommands) {
      try {
        pythonProcess = spawn(cmd, [
          path.join(__dirname, "predict.py"),
          JSON.stringify(req.body),
        ]);
        break; // If spawn successful, break the loop
      } catch (err) {
        errorMessage += `Failed to spawn ${cmd}: ${err.message}\n`;
        continue;
      }
    }

    if (!pythonProcess) {
      throw new Error(
        `Could not find Python executable. Errors: ${errorMessage}`
      );
    }

    let result = "";
    let error = "";

    pythonProcess.stdout.on("data", (data) => {
      result += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      error += data.toString();
    });

    pythonProcess.on("error", (err) => {
      res.status(500).json({
        status: "error",
        message: "Failed to execute Python script",
        details: err.message,
      });
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        return res.status(500).json({
          status: "error",
          message: "Python script execution failed",
          details: error || `Process exited with code ${code}`,
        });
      }

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
    res.status(500).json({
      status: "error",
      message: "Failed to process request",
      details: error.message,
    });
  }
};
