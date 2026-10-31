<div align="center">

# 🌸 Vest IQ 🌸

<p>
  <img src="https://img.shields.io/badge/React.js-61DAFB?style=flat-square&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" />
  <img src="https://img.shields.io/badge/Bootstrap-7952B3?style=flat-square&logo=bootstrap&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" />
  <img src="https://img.shields.io/badge/EfficientNet--B0-FF6F00?style=flat-square" />
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white" />
  <img src="https://img.shields.io/badge/Anthropic-191919?style=flat-square" />
  <img src="https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white" />
</p>

<img src="frontend/public/vestiq-logo.png" alt="Vest IQ Logo" width="120"/>

### 🌷 AI-Powered Digital Wardrobe & Outfit Recommendation 🌷

**✨ Your wardrobe. Your style. Smarter outfit decisions. ✨**

🌿 Organize clothing digitally and discover outfit combinations based on personal preferences, occasions, and weather. 🌿

</div>

---

## 🌼 What is Vest IQ?

**Vest IQ** is an intelligent wardrobe and outfit recommendation web application, designed to make everyday outfit selection easier, more personal, and a little more stylish. 🌸

Build a digital wardrobe by adding clothing items, sort them into categories, and explore outfit combinations. The recommendation system considers wardrobe availability along with weather, occasion, style, and clothing choices. 🌺

The machine-learning component uses EfficientNet-B0 with transfer learning to classify Western and traditional clothing images. The conversational stylist, **Mira**, offers fashion guidance and outfit ideas, with optional access to the user's wardrobe context. 🌿

## 🌹 Key Features

- 👗 **Digital Wardrobe**: Add clothing items, organize them into categories, and build a personal digital wardrobe.
- 🪡 **AI Clothing Classification**: EfficientNet-B0 transfer learning classifies Western and traditional/Indian clothing, including 12 traditional categories such as sarees, kurtas, lehengas, and sherwanis.
- 🌸 **Recommendation System**: A context-aware engine ranks wardrobe combinations using clothing categories, color compatibility, style, occasion, and weather.
- ☁️ **Weather-Aware Suggestions**: Outfit recommendations adapt to current weather conditions.
- 🎀 **Occasion-Based Styling**: Get outfit ideas suited to different occasions and style preferences.
- 🦋 **Mira, AI Stylist Chatbot**: An LLM-powered conversational stylist for fashion guidance and outfit ideas.
  - Supports both Anthropic and Gemini as LLM providers.
  - Can use the user's wardrobe context when enabled.
  - Handles natural-language requests, such as "something comfortable for a wedding in winter."
- 🌷 **Outfit History and Saved Looks**: Track outfit choices and save or rate preferred combinations.
- 🔐 **User Authentication**: Account-based access to wardrobe and application features.

## 🌺 Screenshots

> 🌼 Screenshots will be added to `docs/screenshots/`.

### 🌸 Landing Page

<p align="center">
  <img src="docs/screenshots/landing-page.png" alt="Vest IQ Landing Page" width="100%"/>
</p>

<details>
<summary><strong>🌷 View More Screenshots</strong></summary>

### 🔐 Authentication

<p align="center">
  <img src="docs/screenshots/authentication.png" alt="Vest IQ Authentication" width="100%"/>
</p>

### 👗 Digital Wardrobe

<p align="center">
  <img src="docs/screenshots/wardrobe.png" alt="Vest IQ Digital Wardrobe" width="100%"/>
</p>

### 🌸 Outfit Recommendations

<p align="center">
  <img src="docs/screenshots/recommendations.png" alt="Vest IQ Outfit Recommendations" width="100%"/>
</p>

### 🦋 Mira AI Stylist

<p align="center">
  <img src="docs/screenshots/mira-stylist.png" alt="Mira AI Stylist" width="100%"/>
</p>

</details>

## 🌿 Architecture Overview

```text
                                     VEST IQ
                                        │
                                  User Interface
                                        │
                                React + Vite Frontend
                                        │
                                 FastAPI Backend
                                        │
          ┌──────────────────┬──────────┴───────────┬───────────────────────────┐
          ▼                  ▼                      ▼                           ▼
   Authentication      Wardrobe APIs    Recommendation APIs         Mira Stylist APIs
          │                  │                      │                           │
Protects all routes     MongoDB Data     Context & Preferences                  │
                                                  │                           │
                                 ├─ Weather Context                           │
                                 ├─ Occasion Preferences                      │
                                 └─ Style & Clothing                          │
                                                  │                           │
                                         Outfit Generation                    │
                                                  │                           │
                                       Recommended Outfits                    │
                                                                   Anthropic / Gemini
```

## 📁 Directory Layout

```text
VestIQ/
│
├── ai/                                  # Machine-learning pipeline
│   ├── dataset/
│   │   └── README.md                    # Dataset notes and guidance
│   ├── evaluation/
│   │   └── evaluate_model.py             # Evaluates trained model performance
│   ├── inference/
│   │   ├── predict.py                    # Runs clothing image prediction
│   │   └── predict_traditional.py         # Inference for the traditional model
│   ├── models/
│   │   ├── vestiq_efficientnet_b0.pth    # Saved EfficientNet model
│   │   └── vestiq_traditional_efficientnet_b0.pth
│   ├── preprocessing/
│   │   ├── create_train_val_split.py     # Creates dataset splits
│   │   ├── prepare_fashionpedia.py       # Prepares Fashionpedia data
│   │   └── prepare_traditional.py        # Prepares data for traditional pipeline
│   └── training/
│       ├── train_efficientnet.py         # Trains the EfficientNet model
│       └── train_traditional.py          # Trains the traditional model
│
├── backend/                              # FastAPI backend application
│   ├── app/
│   │   ├── core/
│   │   │   └── configuration.py          # Loads application configuration
│   │   ├── database/
│   │   │   └── database_connection.py    # MongoDB connection setup
│   │   ├── models/
│   │   │   ├── clothing.py               # Clothing data models
│   │   │   ├── stylist.py                # Stylist-related models
│   │   │   └── user.py                   # User data models
│   │   ├── routes/
│   │   │   ├── authentication.py         # Authentication endpoints
│   │   │   ├── recommendations.py        # Outfit recommendation endpoints
│   │   │   ├── stylist.py                # Personal stylist endpoints
│   │   │   ├── wardrobe.py               # Wardrobe management endpoints
│   │   │   └── weather.py                # Weather-related endpoints
│   │   ├── schemas/
│   │   │   ├── clothing.py               # Clothing request/response schemas
│   │   │   ├── stylist.py                # Stylist schemas
│   │   │   └── user.py                   # User schemas
│   │   ├── services/
│   │   │   ├── authentication.py         # Authentication logic
│   │   │   ├── cloudinary_service.py     # Image storage integration
│   │   │   ├── color_service.py          # Clothing color-related processing
│   │   │   ├── llm_client.py             # LLM client integration
│   │   │   ├── outfit_generation_service.py
│   │   │   ├── outfit_image_service.py   # Outfit image-related processing
│   │   │   ├── recommendation_service.py # Recommendation logic
│   │   │   ├── stylist_service.py        # Stylist assistant logic
│   │   │   ├── wardrobe_intelligence.py  # Wardrobe intelligence functions
│   │   │   └── weather_service.py        # Weather data handling
│   │   ├── main.py                       # FastAPI application entry point
│   │   └── wardrobe.py                   # Wardrobe-related application module
│   ├── scripts/
│   │   └── check_stylist_prompts.py      # Utility for checking stylist prompts
│   └── requirements.txt                  # Backend Python dependencies
│
├── frontend/                              # React + Vite frontend
│   ├── public/
│   │   └── vestiq-logo.png               # Public logo asset
│   ├── src/
│   │   ├── assets/                       # Images and visual assets
│   │   ├── components/
│   │   │   ├── LandingPage.jsx           # Landing page UI
│   │   │   ├── StylistChat.jsx           # Stylist chat interface
│   │   │   ├── landing.css               # Landing page styling
│   │   │   └── stylist-chat.css          # Stylist chat styling
│   │   ├── App.jsx                       # Root React application
│   │   ├── main.jsx                      # Frontend entry point
│   │   ├── dashboard-theme.css            # Dashboard theme styles
│   │   ├── vestiq-polish.css              # Additional UI styling
│   │   └── components/mira-chat.css       # Chat interface styles
│   ├── index.html                        # Vite HTML entry point
│   ├── package.json                      # Frontend scripts and dependencies
│   ├── package-lock.json                 # Locked npm dependency versions
│   └── vite.config.js                    # Vite configuration
│
├── .env.example                           # Environment variable template
├── .gitignore                             # Files excluded from Git
├── LICENSE                                # MIT license
└── README.md                              # Project documentation
```

### 🍃 Folder Responsibilities

**`ai/`** contains the machine-learning workflow for clothing image classification. Its preprocessing scripts prepare datasets, training scripts train the models, evaluation scripts measure model performance, and inference scripts load saved models to predict clothing categories from images. Dataset contents and large model files are managed separately from the source code where appropriate.

**`backend/`** contains the FastAPI application that exposes the application's APIs. The `routes/` modules define endpoints, `schemas/` describe validated request and response structures, `models/` hold data model definitions, and `services/` contain the main business logic for authentication, wardrobe operations, outfit generation, weather context, and stylist interactions. The database module manages the MongoDB connection.

**`frontend/`** contains the React user interface built with Vite. The `src/` directory contains the root application, reusable components, styling, and visual assets. The landing page and stylist chat are implemented as dedicated components, while `public/` contains assets served directly by the frontend.

**`.env.example`** provides a template for configuring environment variables locally or during deployment. It should contain placeholder values only; real credentials belong in a private `.env` file or the deployment platform's environment settings.

**`.gitignore`** lists local environments, generated files, datasets, model artifacts, secrets, and other files that should not be committed to Git.

## ⚙️ Setup & Installation

### 🌸 Prerequisites

- Python 3.11+
- Node.js and npm
- MongoDB Atlas account or a local MongoDB instance
- Required API credentials for the services enabled in your configuration

### 🌷 1. Clone the Repository

```bash
git clone https://github.com/somyagoyal09/vestiQ.git
cd vestiQ
```

### 🌼 2. Configure the Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create the local environment file from the root directory:

```powershell
cd ..
copy .env.example backend\.env
```

Configure the required MongoDB connection string, authentication settings, and service credentials in the environment file. Use the variable names documented in `.env.example` and the backend configuration module.

> 🔒 **Security Note:** Never commit `.env` files or private API credentials to GitHub.

### 🌺 3. Configure the Frontend

```bash
cd frontend
npm install
```

Configure the frontend API base URL using the environment variable expected by the frontend code.

## ▶️ Running the Application

### 🌸 Start the FastAPI Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

### 🌷 Start the React Frontend

From the `frontend/` directory:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

### 🌿 API Documentation

FastAPI provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## 🚀 Deployment

Vest IQ can be deployed using separate frontend and backend services.

| Component | Suggested Platform | Purpose |
|---|---|---|
| React + Vite frontend | Vercel | Hosts the frontend application |
| FastAPI backend | Render | Runs the backend API |
| Database | MongoDB Atlas | Stores application data |
| Image storage | Cloudinary | Stores uploaded clothing images, if configured |

Deployment requires configuring the frontend's backend API URL, backend environment variables, database access, and allowed frontend origins in the backend CORS settings.

> 🌼 Deployment URLs will be added here after the application is live and verified.

## 🔗 Project Links

- 🌸 **GitHub Repository:** https://github.com/somyagoyal09/vestiQ
- 🌷 **Live Application:** Coming soon
- 🌿 **Backend API:** Coming soon
- 🌺 **API Documentation:** Coming soon

## 📜 License

This project is licensed under the **MIT License**.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software, subject to the conditions of the MIT License.

For complete terms and conditions, refer to the [LICENSE](LICENSE) file.

<div align="center">

🌸 🌷 🌼 🌿 🌺 🦋 🌹 🍃 🌸

**🌸 Vest IQ — Your wardrobe. Your style. Smarter outfit decisions. 🌸**

</div>
