# KrishiAI (Smart Agriculture)

KrishiAI is a smart agriculture application that provides machine learning-powered insights. The project consists of a Python Flask backend serving a machine learning model and a React (Vite) frontend for the user interface.

## Project Structure

- `app.py`: The main Flask server that exposes the API and handles predictions using the trained model (`agriculture_model_improved.pkl`).
- `frontend/`: Contains the React + Vite frontend application.
- `training_workspace/`: Contains scripts and data used to train the machine learning models.

## Prerequisites

Before running the application, make sure you have the following installed on your system:
- [Python](https://www.python.org/downloads/) (3.8 or higher recommended)
- [Node.js](https://nodejs.org/) (which includes `npm`)

## Getting Started

You will need to run the backend and the frontend in two separate terminal windows.

### 1. Setup and Run the Backend

Open a terminal in the root directory of the project (`KrishiAI/`).

**Install required Python packages:**
```bash
pip install flask flask-cors pandas numpy requests scikit-learn
```

**Start the Flask server:**
```bash
python app.py
```
*The backend server will start running on `http://localhost:5000`.*

### 2. Setup and Run the Frontend

Open a new, separate terminal and navigate to the `frontend` directory:
```bash
cd frontend
```

**Install Node.js dependencies:**
```bash
npm install
```

**Start the React (Vite) development server:**
```bash
npm run dev
```
*The frontend server will start running on the local URL provided in the terminal (usually `http://localhost:5173`). Open that URL in your browser to view the application.*

## Models and Data
- **`agriculture_model_improved.pkl`**: Pre-trained machine learning model used for predictions.
- **`label_encoders_improved.pkl`**: Encoders for processing input data for the model.
- **`rainfall_monthly_averages.csv`**: Contains average rainfall data by district.
