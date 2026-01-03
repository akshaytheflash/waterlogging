# Delhi Waterlogging Monitoring & Response System

A government-grade web platform designed to address waterlogging issues in Delhi through citizen reporting, AI-assisted analysis, and authority action.

## 🚀 Key Features

*   **Citizen Reporting**: Auto-location detection, severity classification, and image upload.
*   **Live Map**: Interactive visualization of reports and known hotspots using Leaflet.js.
*   **AI Integration**:
    *   **Authority Prediction**: Automatically suggests the responsible authority (MCD, PWD, DJB, etc.) based on the report description.
    *   **Chatbot**: AI assistant for emergency guidance and safety tips.
*   **Authority Dashboard**: Dedicated portal for officials to view, filter, and resolve reports with proof.
*   **Rainfall Warnings**: Simulated risk alert system based on forecast data.

## 🛠️ Tech Stack

*   **Frontend**: HTML5, CSS3, Vanilla JavaScript, Leaflet.js (Maps)
*   **Backend**: Node.js, Express.js
*   **Database**: PostgreSQL (Supabase)
*   **AI**: Google Gemini API

## 📋 Prerequisites

*   **Node.js** (v14 or higher) installed on your system.

## 🏃‍♂️ How to Run Locally

Follow these steps to get the application running on your machine:

1.  **Install Dependencies**
    Open your terminal in the project folder and run:
    ```bash
    npm install
    ```

2.  **Start the Server**
    Run the following command:
    ```bash
    node server/index.js
    ```

3.  **Access the Application**
    Open your web browser and navigate to:
    [http://localhost:3000](http://localhost:3000)

## 🔑 Test Credentials

Use these accounts to explore the different roles in the system:

| Role | Username | Password |
|---|---|---|
| **Citizen** | `ravi_citizen` | `citizen123` |
| **Authority** | `mcd_official` | `authority123` |

## ☁️ Deployment

For instructions on how to deploy this application to the cloud (Vercel), please refer to **[DEPLOY.md](DEPLOY.md)**.
