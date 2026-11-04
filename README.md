<div align="center">

# 🌸 VestiQ 🌸

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
  <img src="https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white" />
</p>

<img src="frontend/public/vestiq-logo.png" alt="Vest IQ Logo" width="120"/>

### 🌷 AI-Powered Digital Wardrobe & Outfit Recommendation 🌷

**✨ Your wardrobe. Your style. Smarter outfit decisions. ✨**

</div>

---

## 🌼 What is VestiQ?

**VestiQ** is an intelligent wardrobe and outfit recommendation app. Add your clothes once, and get outfit combinations based on weather, occasion, and style. 🌸

## Screenshots

<p align="center">
  <img src="screenshots/landing_page.png" alt="VestiQ Landing Page" width="85%">
</p>

<details>
  <summary><strong>View More Screenshots</strong></summary>
  <br>

  <p align="center">
    <img src="screenshots/login_page.png" alt="Login Page" width="85%">
  </p>

  <p align="center">
    <img src="screenshots/create_account.png" alt="Create Account Page" width="85%">
  </p>

  <p align="center">
    <img src="screenshots/home_page.png" alt="Home Page" width="85%">
  </p>

  <p align="center">
    <img src="screenshots/my_wardrobe.png" alt="My Wardrobe" width="85%">
  </p>

  <p align="center">
    <img src="screenshots/style_me.png" alt="Style Me" width="85%">
  </p>

  <p align="center">
    <img src="screenshots/mira_AI_chatbot.png" alt="Mira AI Chatbot" width="85%">
  </p>

  <p align="center">
    <img src="screenshots/outfit_recommendation.png" alt="Outfit Recommendations" width="85%">
  </p>

</details>

## 🌿 Architecture Overview

```text
                                     VESTiQ
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
                                                                       Gemini
```

## 📁 Directory Layout

```text
VestiQ/
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

## 🔗 Project Links

- 🌸 **GitHub Repository:** https://github.com/somyagoyal09/vestiQ
- 🌷 **Live Application:** https://vestiq-h91b.onrender.com

## 📜 License

This project is licensed under the **MIT License**.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software, subject to the conditions of the MIT License.

For complete terms and conditions, refer to the [LICENSE](LICENSE) file.

<div align="center">

🌸 🌷 🌼 🌿 🌺 🦋 🌹 🍃 🌸

**🌸 VestiQ — Your wardrobe. Your style. Smarter outfit decisions. 🌸**

</div>
