
import re
import os
import random
from datetime import datetime
from langdetect import detect, LangDetectException


# Google Generative AI import (make sure google-generativeai is installed)
import google.generativeai as genai

# FastAPI app and request model
from fastapi import FastAPI
from pydantic import BaseModel

# Import helper functions from utils.py
from utils import detect_urls_in_query, fetch_website_content, create_website_summary_response

# Dummy BOT_LANGUAGE_MAP for demo (replace with your real mapping)
BOT_LANGUAGE_MAP = {
    'default': ['english', 'hindi', 'french', 'german', 'japanese'],
    'delhi': ['hindi'],
    'japanese': ['japanese'],
    'french': ['french'],
    'german': ['german'],
    'english': ['english']
}

# FastAPI app instance
app = FastAPI()

# NewsSummaryRequest model
class NewsSummaryRequest(BaseModel):
    query: str
    bot_id: str
    user_email: str
    conversation_id: str

# Function to detect the language of a song based on its content, URL, and title

hindi_keywords = [
        # Common Hindi words
        "hai", "mein", "tum", "dil", "pyar", "tere", "hindi", "गीत", "गाना", "raataan", "lambiyan", "shershaah",
        "kiara", "sid", "b praak", "jasleen", "royal", "anvita", "anvit", "kaur", "arijit", "singh", "bollywood",
        "love song", "romantic song", "zindagi", "yaar", "mohabbat", "sapna", "chalo", "aaja", "jaana", "sun", "sapne",
        "saath", "khwab", "yaadon", "yaari", "ishq", "janam", "safar", "pal", "raat", "din", "chand", "suraj", "aasman",
        "dhadkan", "bekhayali", "tujhe", "mujhko", "sanam", "mehboob", "dosti", "shayar", "shayari", "kuch", "bata", "batao",
        "kya", "kaise", "kaun", "kabhi", "kab", "kyun", "kyunki", "ab", "tab", "phir", "fir", "phir bhi", "tumse", "tumhi",
        "tumko", "main", "mera", "meri", "mere", "apna", "apni", "apne", "sapno", "sapne", "khush", "khushi", "khushiyan",
        "dard", "gumsum", "yaad", "yaadein", "yaadon", "yaariyan", "suno", "sunlo", "sun raha", "sun raha hai na tu",
        "aankh", "aankhon", "aansu", "muskurana", "muskurane", "muskurata", "muskurati", "muskurate", "muskurahat",
        "chahat", "chahatein", "chahata", "chahati", "chahate", "chah", "chaha", "chahiye", "chahungi", "chahunga",
        "chahte", "chahtey", "chahte ho", "chahte hoon", "chahte hain", "chahte hoon", "chahte ho", "chahte hain",
        "chahte hoon", "chahte ho", "chahte hain", "chahte hoon", "chahte ho", "chahte hain", "chahte hoon", "chahte ho",
        "chahte hain", "chahte hoon", "chahte ho", "chahte hain", "chahte hoon", "chahte ho", "chahte hain", "chahte hoon",
        "chahte ho", "chahte hain", "chahte hoon", "chahte ho", "chahte hain", "chahte hoon", "chahte ho", "chahte hain",
        # Popular Hindi singers
        "arijit singh", "shreya ghoshal", "sonu nigam", "udit narayan", "alka yagnik", "kumar sanu", "kishore kumar",
        "lata mangeshkar", "asha bhosle", "mohit chauhan", "jubin nautiyal", "neha kakkar", "badshah", "yo yo honey singh",
        "atif aslam", "sunidhi chauhan", "palak muchhal", "kk", "rahat fateh ali khan", "shaan", "ankit tiwari",
        # Bollywood movie names (partial)
        "dilwale", "kabir singh", "shershaah", "yeh jawaani hai deewani", "kal ho naa ho", "dil chahta hai", "barfi",
        "tamasha", "rockstar", "aashiqui", "aashiqui 2", "baazigar", "dangal", "lagaan", "chak de india", "kabhi khushi kabhie gham",
        "kuch kuch hota hai", "hum aapke hain koun", "hum dil de chuke sanam", "devdas", "veer-zaara", "jab we met", "zindagi na milegi dobara"
    ]
french_keywords = [
        # Common French words
        "je", "le", "la", "français", "amour", "paris", "france", "toi", "moi", "nous", "vous", "ils", "elles", "être",
        "avoir", "faire", "dire", "pouvoir", "aller", "voir", "vouloir", "venir", "devoir", "prendre", "trouver", "donner",
        "parler", "aimer", "chanter", "chanson", "musique", "paroles", "coeur", "fleur", "soleil", "lune", "nuit", "jour",
        "rêve", "rêver", "baiser", "douce", "doucement", "beau", "belle", "joli", "jolie", "fille", "garçon", "femme", "homme",
        "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "notre", "votre", "leur", "leurs", "chérie", "chéri",
        "mon amour", "ma vie", "mon coeur", "ma belle", "mon chéri", "ma chérie", "mon ange", "ma princesse", "mon prince",
        # French singers
        "edith piaf", "johnny hallyday", "mylene farmer", "francis cabrel", "charles aznavour", "stromaé", "indila", "zaz",
        "patrick bruel", "julien doré", "louane", "vianney", "christophe mae", "claude françois", "louis bertignac",
        # French song/album names
        "la vie en rose", "ne me quitte pas", "je t'aime", "je te promets", "formidable", "papaoutai", "dernière danse",
        "sous le vent", "elle me dit", "si jamais j'oublie", "parler à mon père", "on écrit sur les murs"
    ]
german_keywords = [
        # Common German words
        "liebe", "deutsch", "berlin", "german", "schatz", "lied", "herz", "leben", "träume", "nacht", "tag", "himmel",
        "sonne", "mond", "sterne", "freund", "freundin", "mädchen", "junge", "frau", "mann", "mein", "meine", "dein",
        "deine", "unser", "unsere", "euer", "eure", "ihr", "ihre", "ich", "du", "er", "sie", "es", "wir", "ihr", "sie",
        "dich", "mich", "uns", "euch", "ihn", "sie", "es", "uns", "euch", "sie", "ihnen", "musik", "liedtext", "singen",
        "sänger", "sängerin", "band", "album", "titel", "melodie", "refrain", "vers", "chor", "tanz", "party", "spaß",
        # German singers/bands
        "helene fischer", "udo lindenberg", "herbert grönemeyer", "nena", "tokio hotel", "cro", "mark forster", "sido",
        "peter fox", "xavier naidoo", "andreas bourani", "revolverheld", "silbermond", "pur", "die toten hosen", "die ärzte",
        # German song/album names
        "atemlos durch die nacht", "99 luftballons", "männer", "auf uns", "tage wie diese", "ein hoch auf uns", "ich will nur",
        "ich will", "ich liebe dich", "du bist mein", "mein herz brennt", "ich geh in flammen auf"
    ]
japanese_keywords = [
        # Common Japanese words/phrases
        "watashi", "anata", "nihon", "japan", "koi", "suki", "日本", "歌", "愛", "恋", "心", "夢", "夜", "日", "月", "星",
        "空", "花", "桜", "涙", "友達", "友", "君", "僕", "私", "あなた", "彼", "彼女", "好き", "大好き", "愛してる", "会いたい",
        "ありがとう", "さようなら", "おはよう", "こんばんは", "おやすみ", "歌詞", "音楽", "メロディー", "バンド", "シンガー", "アルバム",
        "タイトル", "リフレイン", "サビ", "ダンス", "パーティー", "楽しい", "悲しい", "嬉しい", "切ない", "寂しい", "幸せ", "希望",
        # Japanese singers/bands
        "宇多田ヒカル", "浜崎あゆみ", "米津玄師", "中島美嘉", "嵐", "乃木坂46", "欅坂46", "perfume", "one ok rock", "bump of chicken",
        "king gnu", "official髭男dism", "あいみょん", "back number", "yui", "lisa", "yoasobi", "aimyon", "utada hikaru", "kenshi yonezu",
        # Japanese song/album names
        "first love", "lemon", "pretender", "紅蓮華", "炎", "打上花火", "小さな恋のうた", "さくら", "ありがとう", "世界に一つだけの花"
    ]
english_keywords = [
        # Common English words/phrases
        "the", "love", "baby", "girl", "boy", "english", "heart", "music", "song", "you", "me", "us", "life", "dream",
        "night", "day", "moon", "sun", "star", "sky", "friend", "friends", "dance", "party", "happy", "sad", "cry", "smile",
        "kiss", "hug", "forever", "always", "never", "together", "apart", "alone", "miss", "missing", "remember", "forget",
        "goodbye", "hello", "hi", "hey", "yeah", "oh", "yeah yeah", "oh oh", "la la", "na na", "chorus", "verse", "melody",
        "lyrics", "band", "album", "track", "playlist", "single", "hit", "top", "chart", "radio", "remix", "cover", "original",
        # English singers/bands
        "taylor swift", "ed sheeran", "justin bieber", "ariana grande", "beyonce", "rihanna", "drake", "adele", "bruno mars",
        "billie eilish", "dua lipa", "the weeknd", "shawn mendes", "lady gaga", "katy perry", "maroon 5", "coldplay", "eminem",
        "post malone", "selena gomez", "harry styles", "olivia rodrigo", "sam smith", "sia", "imagine dragons", "one direction",
        # English song/album names
        "shape of you", "blinding lights", "bad guy", "someone like you", "hello", "rolling in the deep", "love story", "perfect",
        "thinking out loud", "all of me", "let her go", "see you again", "uptown funk", "closer", "faded", "cheap thrills"
    ]

    # Function to detect the language of a song based on its content, URL, and title
def detect_song_language(content, url, title):
    text_all = f"{content} {url} {title}".lower()

    # 1. Script-based detection (highest priority)
    if re.search(r'[\u0900-\u097F]', text_all):
        return "hindi"
    if re.search(r'[\u3040-\u30ff\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff]', text_all):
        return "japanese"
    # German-specific characters
    if re.search(r'[äöüß]', text_all):
        return "german"
    # French-specific characters
    if re.search(r'[àâçéèêëîïôœùûüÿ]', text_all):
        return "french"

    # 2. Keyword-based detection (non-English first)
    if any(word in text_all for word in hindi_keywords):
        return "hindi"
    if any(word in text_all for word in french_keywords):
        return "french"
    if any(word in text_all for word in japanese_keywords):
        return "japanese"
    if any(word in text_all for word in german_keywords):
        return "german"

    # 3. Only now check for English keywords
    if any(word in text_all for word in english_keywords):
        return "english"

    # 4. Fallback: langdetect
    try:
        text = f"{content} {title}".strip()
        if text and len(text.split()) > 5:
            lang = detect(text)
            if lang == "hi":
                return "hindi"
            elif lang == "fr":
                return "french"
            elif lang == "ja":
                return "japanese"
            elif lang == "de":
                return "german"
            elif lang == "en":
                return "english"
    except LangDetectException:
        pass

    # 5. Fallback: URL/title hints
    if "hindi" in url or "hindi" in title:
        return "hindi"
    if "french" in url or "francais" in title:
        return "french"
    if "japan" in url or "japanese" in title:
        return "japanese"
    if "german" in url or "deutsch" in title:
        return "german"
    if "english" in url or "english" in title:
        return "english"

    return "unknown"

    # 6. If nothing matches, return unknown

    # --- Expanded keyword lists for each language ---


    text_all = f"{content} {url} {title}".lower()
    if any(word in text_all for word in hindi_keywords) or re.search(r'[\u0900-\u097F]', text_all):
        return "hindi"
    if any(word in text_all for word in french_keywords):
        return "french"
    if any(word in text_all for word in japanese_keywords) or re.search(r'[\u3040-\u30ff\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff]', text_all):
        return "japanese"
    if any(word in text_all for word in german_keywords):
        return "german"
    if any(word in text_all for word in english_keywords):
        return "english"
    if "hindi" in url or "hindi" in title:
        return "hindi"
    if "french" in url or "francais" in title:
        return "french"
    if "japan" in url or "japanese" in title:
        return "japanese"
    if "german" in url or "deutsch" in title:
        return "german"
    if "english" in url or "english" in title:
        return "english"
    return "unknown"

# --- Language support mapping for bots ---
def is_language_supported_by_bot(bot_id: str, detected_language: str) -> bool:
    bot_id = bot_id.lower().strip()
    detected_language = detected_language.lower().strip()
    # Prefix-based support: if bot_id starts with a known key, use that mapping
    for key in BOT_LANGUAGE_MAP:
        if bot_id.startswith(key):
            supported = BOT_LANGUAGE_MAP[key]
            break
    else:
        supported = BOT_LANGUAGE_MAP['default']
    return detected_language in [lang.lower().strip() for lang in supported]

# --- Language support mapping for bots ---
def call_gemini_ai(prompt, max_tokens=180):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        )
    )
    return response.text.strip()

#if the detected language is not supported by the bot, return a friendly message

SONG_UNSUPPORTED_LANGUAGE_RESPONSES = [
    "I bet it's a wonderful song, but sorry dear, I don't know this language yet! 🎶🌏",
    "This song sounds interesting, but I can't understand the language. Maybe you can tell me what it's about? 😊",
    "Sorry, I wish I could help with this song, but I don't know this language. Music is still magical though! ✨",
    "Oh, I love discovering new music! Sadly, I can't understand this language yet. Want to share what it means to you?",
    "It must be a beautiful song, but I don't know this language. Maybe you can teach me a word or two? 🎵💬"
]

def get_unsupported_language_message(detected_language):
    return random.choice(SONG_UNSUPPORTED_LANGUAGE_RESPONSES)



@app.post("/api/news")
async def api_news(request: NewsSummaryRequest):
    try:
        query = request.query
        bot_id = request.bot_id
        user_email = request.user_email
        conversation_id = request.conversation_id
        # --- 1. Detect URLs in the user query (e.g., news, YouTube, Spotify, etc.) ---

        detected_urls = detect_urls_in_query(query)
        if detected_urls:
            # --- 2. Fetch website content for the first detected URL ---
            website_data = fetch_website_content(detected_urls[0])
            if website_data:
                url = website_data.get("url", "")
                content = website_data.get("content", "")
                title = website_data.get("title", "")

                # --- 3. Check if the URL or title suggests a song/music link ---
                song_keywords = [
                    "spotify", "youtube", "youtu.be", "song", "lyrics", "music", "album", "track", "playlist", "गीत", "गाना"
                ]
                # If any keyword is present in the URL or title, treat as a song/music link
                is_song = any(kw in url.lower() for kw in song_keywords) or any(kw in title.lower() for kw in song_keywords)
                # --- 4. Song detected: Get bot persona and detect song language ---
                if is_song:
                    from bot_prompt import get_bot_prompt
                    bot_persona = get_bot_prompt(bot_id)
                    song_language = detect_song_language(content, url, title)
                    print(f"DEBUG: bot_id={bot_id}, detected_language={song_language}, supported={BOT_LANGUAGE_MAP.get(bot_id, BOT_LANGUAGE_MAP['default'])}")
                    # Language-bot matching logic
                    if not is_language_supported_by_bot(bot_id, song_language):
                        print(f"DEBUG: Language '{song_language}' is NOT supported by bot '{bot_id}'. Returning unsupported message.")
                        return {
                            'status': 'error',
                            'result': get_unsupported_language_message(song_language),
                            'mode': 'website_summary',
                            'timestamp': datetime.now().isoformat(),
                            'debug': {
                                'bot_id': bot_id,
                                'song_language': song_language,
                                'supported_languages': BOT_LANGUAGE_MAP.get(bot_id, BOT_LANGUAGE_MAP['default'])
                            }
                        }
                    print(f"DEBUG: Language '{song_language}' IS supported by bot '{bot_id}'. Proceeding to AI summary.")
                    # If supported, proceed as before
                    persona_instructions = (
                        f"{bot_persona}\n"
                        "You are a music-loving assistant. When summarizing a song, adapt your tone and emojis to the mood of the lyrics (love, heartbreak, party, motivational, sad, etc.) "
                        "and to your persona (mentor, friend, romantic, etc.). "
                        "For each response, the proactive message (Line 3) must be unique, creative, and use different emojis that fit both the mood and the persona. "
                        "Do NOT repeat the same proactive message or emoji style for every song or persona. "
                        "For example:\n"
                        "- For a friend persona and party song, use fun, energetic language and party emojis 🎉🕺.\n"
                        "- For a romantic persona and love song, use sweet, dreamy language and heart/love emojis 💖😍.\n"
                        "- For a mentor persona and motivational song, use encouraging words and uplifting emojis 🚀🌟.\n"
                        "- For a friend persona and heartbreak song, use supportive, caring words and comforting emojis 🤗💔.\n"
                        "Be creative and make each proactive message feel personal and fresh!\n"
                        f"Song title: {title}\n"
                        f"Lyrics/content: {content[:1500]}\n"
                        "Respond in three lines (no labels):\n"
                        "Do not ever mention the song name or movie name in your response."
                        "- First line: Song summary (first sentence)\n"
                        "- Second line: Song summary (second sentence, or leave blank if not needed)\n"
                        "- Third line: Proactive message or question for the user that fits the mood and your persona, with unique emojis.\n"
                        "If the summary can be done in one sentence, leave the second line blank.\n"
                    )
                    # --- 7. Call Gemini AI to generate the summary using the instructions ---
                    ai_response = call_gemini_ai(persona_instructions, max_tokens=180)
                else:
                    # --- 8. If not a song/music link, generate a regular website/news summary ---
                    ai_response = create_website_summary_response(query, website_data, bot_id=bot_id)
                # --- 9. Return the AI response and website data ---
                return {
                    'status': 'success',
                    'ai_response': ai_response,
                    'website_data': website_data,
                    'detected_urls': detected_urls,
                    'mode': 'website_summary',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # --- 10. Could not fetch website content ---
                return {
                    'status': 'error',
                    'result': f"Could not fetch content from {detected_urls[0]}",
                    'mode': 'website_summary',
                    'timestamp': datetime.now().isoformat()
                }
        # --- 11. No URL found in the query ---
        return {
            'status': 'error',
            'result': "No website or YouTube link found in your query.",
            'mode': 'website_summary',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        return {
            'status': 'error',
            'result': f'Internal error: {str(e)}',
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
