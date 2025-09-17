# Gemini Integration: GDELT Query Builder & Summarization

This project uses Google’s Gemini for:
- Building 10 language-preserving GDELT query variations.
- Analyzing outlet bias and returning categories (must include exactly “unbiased”).
- Producing a multi‑perspective factual summary grouped by bias categories.

Gemini runs in the cloud and is not cached. The local embedding model is cached and shared across requests.

## Setup
- Get an API key from https://ai.google.dev/
- .env:
  - GEMINI_API_KEY=your_key
  - GEMINI_MODEL=gemini-1.5-pro (or gemini-2.5-pro / flash variants)

## Query Builder (gdelt_query_builder.py)
- Generates EXACTLY 10 variations separated by |||.
- Preserves user language.
- Uses AND-only operators between terms.
- Adds sourcecountry/sourceregion and datetimes when implied.
- Sensitive-query guard:
  - The system prompt instructs Gemini to return the literal token INAPPROPRIATE_QUERY_DETECTED for sensitive topics (e.g., pornography, explicit adult content, certain religious questions flagged by policy).
  - The backend detects this and immediately returns a summary “I cannot respond to this query.” (status=blocked).

Example request body to backend:
```
{"query": "news about war in Ukraine"}
```

## Bias Analysis
- Gemini returns bias categories and counts; one category is normalized to exactly “unbiased”.
- Reasoning text explains the categorization logic; this is appended after sources in the final summary.

## Summarization
- Backend sends top URLs from all categories (including unbiased) to Gemini, labeled by category.
- Gemini instruction highlights:
  - Produce a concise factual answer first.
  - Then list SOURCES BY CATEGORY with up to 5 URLs per category.
  - Numbering restarts at 1 per category (1–5 for each).
  - After sources, append “REASONING:” with the bias-analysis reasoning string.
- The backend returns only the final formatted summary string; UI renders it verbatim.

## Notes
- No Gemini model caching (cloud API).
- Local embedding model (SentenceTransformers) is cached once and reused.
- Optional whitelist filtering toggled via USE_WHITELIST_ONLY in .env.