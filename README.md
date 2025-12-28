# Credible

> **Misinformation Detection & Verification System**

Credible is a full-stack application designed to combat misinformation by verifying user queries against global news sources. It combines the power of the **GDELT Project** for real-time news ingestion, **Google Gemini** for intelligent query expansion and bias analysis, and **SentenceTransformers** for local semantic ranking.

The system features a robust **Python/Flask backend** and a modern **Flutter frontend** (MisinfoGuard) to provide users with concise, multi-perspective summaries of complex topics.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
  - [Backend Setup](#1-backend-setup)
  - [Frontend Setup](#2-frontend-setup)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [License](#-license)

---

## 🚀 Features

* **Multi-Source Verification:** Fetches and normalizes articles from the GDELT Project (Global Database of Events, Language, and Tone).
* **AI-Driven Query Expansion:** Uses Gemini to generate robust search query variations (AND-only operators, language preservation).
* **Bias Analysis:** Automatically categorizes news sources into bias perspectives (including a strictly enforced "Unbiased" category) using Gemini.
* **Semantic Ranking:** Uses a local embedding model (cached `SentenceTransformers`) to rank articles by relevance to the user's specific query.
* **Sensitive Content Guard:** Automatically short-circuits queries related to sensitive topics (e.g., pornography, hate speech).
* **Multi-Perspective Summarization:** Generates a final summary that groups sources by perspective and explains the reasoning behind the verification.
* **Cross-Platform UI:** A clean Flutter application ("MisinfoGuard") that runs on Android, iOS, Web, Linux, and Windows.

---

## 🛠 Tech Stack

### Backend (`misinformation_detection_backend`)
* **Language:** Python 3.11+
* **Framework:** Flask
* **AI/ML:** Google Generative AI (Gemini), SentenceTransformers, PyTorch
* **Data:** GDELT Project API
* **Utilities:** NumPy, python-dotenv

### Frontend (`misinformationui`)
* **Framework:** Flutter
* **Language:** Dart
* **Dependencies:** `http`, `flutter_linkify`, `google_fonts`, `url_launcher`

---

## 📂 Project Structure

```text
credible/
├── misinformation_detection_backend/  # Python Flask Server
│   ├── main.py                        # Entry point
│   ├── bias_analyzer.py               # Gemini bias analysis logic
│   ├── gdelt_api.py                   # GDELT data fetching
│   ├── ranker.py                      # Semantic ranking logic
│   ├── requirements.txt               # Python dependencies
│   └── ...
├── misinformationui/                  # Flutter Client Application
│   ├── lib/
│   │   ├── main.dart                  # App entry point
│   │   ├── chat_screen.dart           # Main chat interface
│   │   └── ...
│   ├── pubspec.yaml                   # Flutter dependencies
│   └── ...
└── README.md

```

---

## 📦 Prerequisites

* **Python 3.11** or higher
* **Flutter SDK** (3.0.0+)
* **Google Gemini API Key**
* **Conda** (Optional, but recommended for environment management)

---

## ⚙️ Installation & Setup

### 1. Backend Setup

1. Navigate to the backend directory:
```bash
cd misinformation_detection_backend

```


2. Create and activate a virtual environment:
```bash
conda create -n fake_news_detection python=3.11 -y
conda activate fake_news_detection

```


3. Install dependencies:
```bash
pip install -r requirements.txt

```


*Note: If you have an NVIDIA GPU, uncomment the specific CUDA libraries in `requirements.txt` for faster embedding generation.*
4. Configure environment variables:
Copy the example file and edit it:
```bash
cp .env.example .env

```


**Required `.env` variables:**
* `GEMINI_API_KEY`: Your Google Gemini API key.
* `GEMINI_MODEL`: e.g., `gemini-1.5-pro` or `gemini-2.0-flash`.
* `SIMILARITY_MODEL`: e.g., `intfloat/multilingual-e5-base`.


5. Run the server:
```bash
# Linux/Mac
chmod +x ./main.py
./main.py

# Windows
python main.py

```


The server will start on `http://127.0.0.1:5000`.

### 2. Frontend Setup

1. Open a new terminal and navigate to the UI directory:
```bash
cd misinformationui

```


2. Install Flutter dependencies:
```bash
flutter pub get

```


3. Configure API Endpoint:
If running on an Emulator/Simulator or physical device, ensure the `chat_screen.dart` points to the correct IP address (use `10.0.2.2` for Android Emulator, or your LAN IP for physical devices).
4. Run the app:
```bash
# Web (Chrome)
flutter run -d chrome

# Linux Desktop
flutter run -d linux

# Android
flutter run -d emulator

```



---

## 🔧 Configuration

The backend behavior is highly customizable via the `.env` file:

| Variable | Description | Default |
| --- | --- | --- |
| `MAX_ARTICLES_PER_QUERY` | Max articles fetched from GDELT | `250` |
| `TOP_N_PER_CATEGORY` | Top articles to keep per bias category | `5` |
| `MIN_SIMILARITY_THRESHOLD` | Cutoff for relevance ranking | `0.1` |
| `USE_WHITELIST_ONLY` | Restrict results to known domains | `false` |
| `SHOW_SIMILARITY_SCORES` | Include ranking scores in API response | `true` |

---

## 📡 API Reference

### Detect Misinformation

**Endpoint:** `POST /api/detect`

**Request Body:**

```json
{
  "query": "Is the earth flat?"
}

```

**Response:**

```json
{
  "summary": "MULTI-PERSPECTIVE FACTUAL SUMMARY...\n\n...SOURCES BY CATEGORY...\n\n...REASONING: ...",
  "status": "ok"
}

```

---

## 📄 License

Copyright 2024 Credible Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

```
http://www.apache.org/licenses/LICENSE-2.0

```

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

```

```
