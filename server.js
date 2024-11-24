const express = require("express");
const { spawn } = require("child_process");
const cors = require("cors");
const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

// Documentation route
app.get("/api/docs", (req, res) => {
  const documentation = {
    title: "Heart Disease Prediction API",
    description:
      "API for predicting heart disease risk using medical parameters",
    version: "1.0.0",
    endpoints: {
      "/api/predict": {
        method: "POST",
        description: "Predict heart disease risk based on medical parameters",
        requestBody: {
          type: "application/json",
          required: true,
          content: {
            age: { type: "number", description: "Patient's age", example: 52 },
            sex: {
              type: "number",
              description: "0: Female, 1: Male",
              example: 1,
            },
            cp: {
              type: "number",
              description: "Chest pain type (0-3)",
              example: 0,
            },
            trestbps: {
              type: "number",
              description: "Resting blood pressure in mm/Hg",
              example: 125,
            },
            chol: {
              type: "number",
              description: "Serum cholesterol in mg/dl",
              example: 212,
            },
            fbs: {
              type: "number",
              description:
                "Fasting blood sugar > 120 mg/dl (0: False, 1: True)",
              example: 0,
            },
            restecg: {
              type: "number",
              description: "Resting ECG results (0-2)",
              example: 1,
            },
            thalach: {
              type: "number",
              description: "Maximum heart rate achieved",
              example: 168,
            },
            exang: {
              type: "number",
              description: "Exercise induced angina (0: No, 1: Yes)",
              example: 0,
            },
            oldpeak: {
              type: "number",
              description: "ST depression induced by exercise relative to rest",
              example: 1.0,
            },
            slope: {
              type: "number",
              description: "Slope of the peak exercise ST segment (0-2)",
              example: 2,
            },
            ca: {
              type: "number",
              description:
                "Number of major vessels colored by flourosopy (0-3)",
              example: 2,
            },
            thal: {
              type: "number",
              description: "Thalassemia (1-3)",
              example: 3,
            },
          },
        },
        response: {
          type: "application/json",
          content: {
            status: { type: "string", example: "success" },
            prediction: {
              type: "number",
              description: "0: No Disease, 1: Disease",
              example: 0,
            },
            probability: {
              type: "number",
              description: "Probability of heart disease",
              example: 0.34,
            },
            classification: {
              type: "string",
              description: "Disease stage classification",
              example: "No Disease",
              possibleValues: [
                "No Disease",
                "Early Stage",
                "Medium Stage",
                "Critical Stage",
              ],
            },
          },
        },
      },
    },
    sampleRequests: [
      {
        description: "Sample case 1 - No Disease",
        request: {
          age: 52,
          sex: 1,
          cp: 0,
          trestbps: 125,
          chol: 212,
          fbs: 0,
          restecg: 1,
          thalach: 168,
          exang: 0,
          oldpeak: 1.0,
          slope: 2,
          ca: 2,
          thal: 3,
        },
        expectedResponse: {
          status: "success",
          prediction: 0,
          probability: 0.34,
          classification: "No Disease",
        },
      },
      {
        description: "Sample case 2 - Critical Stage",
        request: {
          age: 61,
          sex: 1,
          cp: 2,
          trestbps: 148,
          chol: 203,
          fbs: 1,
          restecg: 1,
          thalach: 161,
          exang: 0,
          oldpeak: 2.1,
          slope: 2,
          ca: 1,
          thal: 3,
        },
        expectedResponse: {
          status: "success",
          prediction: 1,
          probability: 0.89,
          classification: "Critical Stage",
        },
      },
    ],
  };

  res.json(documentation);
});

// Prediction route
app.post("/api/predict", (req, res) => {
  const pythonProcess = spawn("python", [
    "predict.py",
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
      // Remove processed_features from response
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
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
