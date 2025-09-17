# Fake News Detection (GDELT + Gemini)

This app takes a user query, builds robust GDELT queries via Gemini, fetches articles, analyzes outlet bias, ranks articles with local embeddings, and returns a concise, multi‑perspective summary. The UI renders exactly what the backend returns (no extra formatting or hardcoded values).

## Key Features
- Query expansion: 10 GDELT query variations, language-preserving, AND-only operators.
- Sensitive-query guard: pornography/religion and similar sensitive topics short‑circuit with “I cannot respond to this query.”
- GDELT ingestion and normalization.
- Gemini-driven bias analysis with categories; one category is strictly named “unbiased”.
- Per-category ranking using a cached local embedding model (SentenceTransformers), shared across requests.
- Multi‑perspective summarization:
  - Sends top URLs from all categories (including unbiased) to Gemini.
  - Summary lists sources grouped by category with up to 5 URLs per category.
  - Appends the “reasoning” string (from bias analysis) after the sources.
- Optional domain whitelisting (toggle in .env).
- Terminal and UI show the exact same summary string.

## Requirements
- Python 3.11+
- Conda/venv recommended
- Packages: flask, flask-cors, python-dotenv, requests, sentence-transformers, torch, google-generativeai

## Setup
1. Create and activate environment (example with conda):
   - conda create -n fake_news_detection python=3.11 -y
   - conda activate fake_news_detection
2. Install deps:
   - pip install -r requirements.txt  (if present) or install the packages listed above.
3. Copy .env.example to .env and set values:
   - GEMINI_API_KEY, GEMINI_MODEL (e.g., gemini-1.5-pro or gemini-2.5-pro)
   - MAX_ARTICLES_PER_QUERY, TOP_N_PER_CATEGORY, MIN_SIMILARITY_THRESHOLD
   - SIMILARITY_MODEL (e.g., intfloat/multilingual-e5-base)
   - SHOW_SIMILARITY_SCORES, SHOW_PUBLISH_DATE, SHOW_URL
   - USE_WHITELIST_ONLY (true/false)
   - PORT, DEBUG

## Run
- Linux:
  - chmod +x ./main.py
  - ./main.py
- Visit http://127.0.0.1:5000

## API
POST /api/detect
- Body: {"query": "your question"}
- Returns (simplified):
```
{
  "query": "...",
  "summary": "MULTI-PERSPECTIVE FACTUAL SUMMARY...\n\n...SOURCES BY CATEGORY...\n\n...REASONING: ...",
  "status": "ok" | "no_results" | "blocked"
}
```
Notes:
- If the query is sensitive, status=blocked and summary contains: “I cannot respond to this query.”
- Only the summary string is printed to terminal and sent to UI, and the UI renders it verbatim.

## Behavior Details
- Local embedding model is loaded once and cached for reuse across requests.
- Gemini runs in the cloud (no caching).
- Bias categories come from Gemini; one is enforced/normalized to exactly “unbiased”.
- Summarization uses top URLs from all categories and instructs Gemini to:
  - Group sources by category,
  - List up to 5 URLs per category (numbering restarts at 1 inside each category),
  - Then append the bias-analysis “reasoning” section.

## Whitelist Filtering
- USE_WHITELIST_ONLY=true limits articles to whitelisted domains.
- When false, all domains are considered.

## Frontend
- Primary UI: Flutter app in `misinformationui/`.
- Optional debug client: `static/` minimal JS page (useful for quick backend checks only).

### Run the Flutter UI
1) Start the backend (see Run section below) so it listens on http://localhost:5000

2) In a separate terminal, run the Flutter app:
   - cd misinformationui
   - flutter pub get
   - Choose a target:
     - Web (Chrome): flutter run -d chrome
     - Linux desktop: flutter run -d linux (ensure Linux desktop is enabled in Flutter)
     - Android emulator: flutter run -d emulator
       - Update the API URL in `misinformationui/lib/chat_screen.dart` from `http://localhost:5000` to `http://10.0.2.2:5000` for Android emulators, or use your machine's LAN IP for real devices.
     - iOS simulator: `http://localhost:5000` should work; real devices need your machine's LAN IP.

Note: The legacy `static/` page is kept for quick smoke tests; the production UX is the Flutter app.
