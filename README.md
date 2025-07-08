# 🎼🤖 Symphony Summary Orchestra 📰✨

> **Transform every link into a standing ovation. Let your bots perform, narrate, and inspire!**

Step into the world of **Symphony Summary Orchestra** — the API where every song or news link is reimagined as a creative, language-aware, and personality-driven performance. From Bollywood blockbusters to J-Pop gems to headline news, your bot personas become the stars of a digital stage, delivering summaries with artistry, empathy, and a spark of magic.

Each bot is a virtuoso: some are mentors, some are friends, some are romantics — and each only performs in their own language. If they can't understand, they'll still delight you with a charming, proactive encore.

---


## 🚀 Features

- **AI-Powered Summaries:** Uses Google Gemini AI to generate concise, creative summaries for songs and news/websites.
- **Smart Language Detection:** Automatically detects Hindi, Japanese, French, German, or English from content, title, and URL.
- **Persona-Driven Bots:** Each bot supports only its intended language(s) (e.g., the "delhi" bot for Hindi, "japanese" bot for Japanese) and responds in a fitting tone.
- **Proactive, Friendly Messaging:** If a bot can't handle a language, it replies with a warm, creative fallback message.
- **Robust Error Handling:** Detailed error/debug output for easy troubleshooting.
- **Easy Integration:** Simple REST API for your apps, chatbots, or web frontends.

---

## 📚 Example Usage

### `POST /api/news`
Summarize a website or song link with a chosen bot persona.

**Request:**
```json
{
  "query": "Summarize this song: https://www.youtube.com/watch?v=xyz...",
  "bot_id": "delhi_mentor_male",
  "user_email": "user@email.com",
  "conversation_id": "abc123"
}
```

**Response (success):**
```json
{
  "status": "success",
  "ai_response": "A heartfelt Hindi love song...\n\nWhat memories does this song bring to you? 💖",
  "website_data": { ... },
  "detected_urls": [ ... ],
  "mode": "website_summary",
  "timestamp": "..."
}
```

**Response (unsupported language):**
```json
{
  "status": "error",
  "result": "I bet it's a wonderful song, but sorry dear, I don't know this language yet! 🎶🌏",
  ...
}
```

---

## ⚡ Quickstart

1. **Clone the repo:**
   ```sh
   git clone <your-repo-url>
   cd summary-for-link
   ```
2. **Create a virtual environment & install dependencies:**
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```
3. **Set your Google Gemini API key:**
   ```powershell
   $env:GOOGLE_API_KEY="YOUR_API_KEY"
   ```
4. **Run the server:**
   ```sh
   uvicorn main:app --reload
   ```
5. **Try it out!** Use Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test the API interactively.

---

## 🤖 Bot Language Support
| Bot Persona      | Supported Language(s) |
|------------------|-----------------------|
| delhi_*          | Hindi                 |
| japanese         | Japanese              |
| french           | French                |
| german           | German                |
| english          | English               |

---


## 🛠️ Project Structure
- `main.py` — FastAPI app, language detection, bot logic, error handling
- `utils.py` — Utility functions for URL/content extraction
- `bot_prompt.py` — Bot persona prompt templates
- `requirements.txt` — Python dependencies

---

## 🔄 Workflow Overview

1. **User sends a query** (with a song/news link and bot persona) to the `/api/news` endpoint.
2. **URL detection & content extraction:** The backend extracts the main content from the provided link (YouTube, Spotify, news, etc.).
3. **Language detection:** The system analyzes the content, title, and URL to determine the language (Hindi, Japanese, French, German, or English).
4. **Bot language check:** The bot persona is checked for support of the detected language.
   - If supported: The bot's persona prompt and content are sent to Gemini AI for a creative summary.
   - If not supported: The bot returns a friendly, proactive fallback message.
5. **Response:** The API returns the summary (or fallback message), detected URLs, and debug info.

---

## 🙏 Acknowledgments

- **Google Gemini AI** for powering the creative summaries.
- **FastAPI** for the robust, modern web framework.
- **newspaper3k, Selenium, BeautifulSoup** for content extraction.
- All open-source contributors and the developer community for inspiration and support.


---

## 📄 License
MIT License. See [LICENSE](LICENSE).
