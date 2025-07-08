
import re
import os
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from newspaper import Article
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bot_prompt import get_bot_prompt

def call_gemini_ai(prompt, max_tokens=300):
    """
    Calls Gemini AI (Google Generative AI) to summarize content.
    You must have the `google-generativeai` package installed and your API key set as GEMINI_API_KEY.
    """
    import google.generativeai as genai
    import os

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY environment variable is not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        )
    )
    return response.text.strip()



def detect_urls_in_query(query):
    """Detect if the query contains website URLs with enhanced YouTube detection"""
    print(f"🔍 Checking for URLs in query: {query}")

    # Fixed URL patterns with proper ordering (specific first, general last)
    url_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+(?:&[\w=&-]*)?',  # Full YouTube URLs
        r'https?://youtu\.be/[\w-]+(?:\?[\w=&-]*)?',                       # Short YouTube URLs
        r'https?://[^\s]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',                     # Complete HTTPS URLs
        r'http://[^\s]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',                       # Complete HTTP URLs
        r'www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',                 # www. URLs
    ]

    found_urls = []

    # Process patterns in order, skip general patterns if specific ones match
    for i, pattern in enumerate(url_patterns):
        matches = re.findall(pattern, query, re.IGNORECASE)
        for match in matches:
            # Clean the URL
            clean_url = match.strip().rstrip('.,;:!?')

            # Ensure proper protocol
            if not clean_url.startswith(('http://', 'https://')):
                if 'youtube.com' in clean_url or 'youtu.be' in clean_url:
                    clean_url = 'https://' + clean_url
                else:
                    clean_url = 'https://' + clean_url

            # Validate URL structure and avoid duplicates
            try:
                parsed = urlparse(clean_url)
                if parsed.netloc and parsed.scheme in ['http', 'https']:
                    # Check if this URL is already found (avoid duplicates)
                    if not any(clean_url.startswith(existing) or existing.startswith(clean_url) for existing in found_urls):
                        found_urls.append(clean_url)
                        print(f"✅ Found valid URL: {clean_url}")
            except:
                continue

        # If we found YouTube URLs, skip general patterns to avoid duplicates
        if i < 2 and found_urls:  # YouTube patterns are first two
            break

    return found_urls


def fetch_website_content(url):
    print(f"🌐 Fetching content from: {url}")

    # Try newspaper3k first
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text
        title = article.title or ""
        if text and len(text.split()) > 50:
            print("✅ Extracted content with newspaper3k")
            return {
                'title': title,
                'content': text,
                'url': url,
                'type': 'website',
                'extracted_at': datetime.now().isoformat()
            }
        else:
            print("⚠️ newspaper3k returned too little content, falling back to Selenium...")
    except Exception as e:
        print(f"❌ Error extracting with newspaper3k: {e}")
        print("⚠️ Falling back to Selenium + BeautifulSoup...")
        # === ADD DEBUG HERE ===
    import time
    print("DEBUG: time =", time)
    print("DEBUG: time.sleep =", getattr(time, 'sleep', '❌ NOT FOUND'))
    # ======================

    # Fallback: Selenium + BeautifulSoup (your existing code)
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)

        print("🚗 ChromeDriver started, loading URL...")
        driver.get(url)
        time.sleep(3)
        print("✅ Page loaded, extracting HTML...")
        html = driver.page_source
        driver.quit()
        print("✅ HTML extracted, parsing with BeautifulSoup...")
        soup = BeautifulSoup(html, 'html.parser')

        # Check for YouTube
        is_youtube = 'youtube.com/watch' in url or 'youtu.be/' in url
        if is_youtube:
            data = extract_youtube_content(soup, url)
            print("DEBUG: YouTube extraction result:", data)
            return data

        # For non-YouTube websites, use general extraction
        return extract_general_website_content(soup, url)

    except Exception as e:
        print(f"❌ Error fetching {url} with Selenium: {e}")
        return None

def extract_youtube_content(soup, url):
    """Extract detailed content from YouTube video pages with enhanced accuracy"""
    print("🎥 Extracting YouTube video content...")

    try:
        # Extract video ID for potential transcript access
        video_id = ""
        if 'watch?v=' in url:
            video_id = url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]

        # Extract video title with multiple fallbacks
        title = ""
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="title"]',
            'title',
            'h1.ytd-video-primary-info-renderer',
            '[data-e2e="video-title"]',
            'h1.ytd-watch-metadata',
            '.ytd-video-primary-info-renderer h1'
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    title = element.get('content', '').strip()
                else:
                    title = element.get_text().strip()
                if title and len(title) > 5:
                    break

        # Clean YouTube title
        if title:
            title = title.replace(' - YouTube', '').strip()
            title = re.sub(r'\s+', ' ', title)

        # Extract video description with better selectors
        description = ""
        desc_selectors = [
            'meta[property="og:description"]',
            'meta[name="description"]',
            '[data-e2e="video-desc"]',
            '#description',
            '.description',
            '.ytd-video-secondary-info-renderer #description',
            '.ytd-expandable-video-description-body-renderer',
            'ytd-expandable-video-description-body-renderer'
        ]

        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    description = element.get('content', '').strip()
                else:
                    description = element.get_text().strip()
                if description and len(description) > 30:
                    break

        # Extract channel name with better accuracy
        channel = ""
        channel_selectors = [
            'meta[property="og:video:creator"]',
            '.ytd-video-owner-renderer a',
            '.ytd-channel-name a',
            '#owner-name a',
            '.yt-user-info a',
            'link[itemprop="url"]'
        ]

        for selector in channel_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    channel = element.get('content', '').strip()
                elif element.name == 'link':
                    href = element.get('href', '')
                    if '/channel/' in href or '/@' in href:
                        channel = href.split('/')[-1].replace('@', '').strip()
                else:
                    channel = element.get_text().strip()
                if channel and len(channel) > 2:
                    break

        # Extract video metadata from page content and JSON-LD
        page_text = soup.get_text()

        # Try to extract structured data (JSON-LD)
        json_scripts = soup.find_all('script', type='application/ld+json')
        video_metadata = {}

        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}

                if data.get('@type') == 'VideoObject':
                    video_metadata = data
                    break
            except:
                continue

        # Extract comprehensive video information
        views = ""
        view_patterns = [
            r'([\d,\.]+)\s*views',
            r'([\d,\.]+)\s*Views',
            r'watched\s*([\d,\.]+)',
            r'"viewCount":"(\d+)"',
            r'"interactionCount":"(\d+)"'
        ]

        for pattern in view_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                views = match.group(1)
                break

        # Get view count from structured data
        if not views and video_metadata.get('interactionStatistic'):
            interaction = video_metadata['interactionStatistic']
            if isinstance(interaction, list):
                for stat in interaction:
                    if stat.get('interactionType', {}).get('@type') == 'WatchAction':
                        views = stat.get('userInteractionCount', '')
                        break
            elif isinstance(interaction, dict):
                views = interaction.get('userInteractionCount', '')

        # Extract duration with better patterns
        duration = ""
        duration_patterns = [
            r'Duration:\s*(\d+:\d+(?::\d+)?)',
            r'(\d+:\d+:\d+)',
            r'(\d+:\d+)',
            r'"lengthSeconds":"(\d+)"',
            r'"duration":"PT(\d+)M(\d+)S"',
            r'"duration":"PT(\d+)H(\d+)M(\d+)S"'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, page_text)
            if match:
                if 'lengthSeconds' in pattern:
                    seconds = int(match.group(1))
                    minutes = seconds // 60
                    remaining_seconds = seconds % 60
                    if minutes >= 60:
                        hours = minutes // 60
                        minutes = minutes % 60
                        duration = f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
                    else:
                        duration = f"{minutes}:{remaining_seconds:02d}"
                elif 'PT' in pattern and 'H' in pattern:
                    hours, minutes, seconds = match.groups()
                    duration = f"{hours}:{minutes.zfill(2)}:{seconds.zfill(2)}"
                elif 'PT' in pattern:
                    minutes, seconds = match.groups()
                    duration = f"{minutes}:{seconds.zfill(2)}"
                else:
                    duration = match.group(1)
                break

        # Get duration from structured data
        if not duration and video_metadata.get('duration'):
            duration_iso = video_metadata['duration']
            # Parse ISO 8601 duration (PT1H30M45S format)
            duration_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
            if duration_match:
                hours, minutes, seconds = duration_match.groups()
                hours = int(hours) if hours else 0
                minutes = int(minutes) if minutes else 0
                seconds = int(seconds) if seconds else 0

                if hours > 0:
                    duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration = f"{minutes}:{seconds:02d}"

        # Extract keywords/tags with better coverage
        keywords = ""
        keywords_sources = [
            soup.find('meta', {'name': 'keywords'}),
            video_metadata.get('keywords', [])
        ]

        all_keywords = []
        for source in keywords_sources:
            if isinstance(source, str):
                all_keywords.extend([k.strip() for k in source.split(',') if k.strip()])
            elif hasattr(source, 'get'):
                content = source.get('content', '')
                all_keywords.extend([k.strip() for k in content.split(',') if k.strip()])
            elif isinstance(source, list):
                all_keywords.extend(source)

        if all_keywords:
            keywords = ', '.join(all_keywords[:10])  # Limit to 10 keywords

        # Extract upload date
        upload_date = ""
        if video_metadata.get('uploadDate'):
            upload_date = video_metadata['uploadDate']
        else:
            date_patterns = [
                r'"publishDate":"([^"]+)"',
                r'"datePublished":"([^"]+)"'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    upload_date = match.group(1)
                    break

        # Try to extract video captions/transcript content from page
        transcript_content = ""

        # Look for transcript in page scripts
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'captions' in script.string.lower():
                # Try to extract caption data
                caption_matches = re.findall(r'"text":"([^"]+)"', script.string)
                if caption_matches:
                    # Clean and join captions
                    clean_captions = []
                    for caption in caption_matches[:50]:  # Limit to first 50 captions
                        caption = caption.replace('\\n', ' ').replace('\\', '').strip()
                        if len(caption) > 5 and not caption.startswith(('[', '{')):
                            clean_captions.append(caption)

                    if clean_captions:
                        transcript_content = ' '.join(clean_captions)
                        break

        # Analyze comments for additional context (limited)
        comments_content = ""
        comment_elements = soup.find_all(class_=re.compile(r'comment.*content'))
        if comment_elements:
            comment_texts = []
            for elem in comment_elements[:5]:  # First 5 comments only
                comment_text = elem.get_text().strip()
                if len(comment_text) > 20 and len(comment_text) < 200:
                    comment_texts.append(comment_text)

            if comment_texts:
                comments_content = ' | '.join(comment_texts)

        # Build comprehensive content structure
        content_parts = []

        if title:
            content_parts.append(f"Title: {title}")

        if channel:
            content_parts.append(f"Channel: {channel}")
          # Video statistics
        stats = []
        if duration:
            stats.append(f"Duration: {duration}")
        if views:
            stats.append(f"Views: {views}")
        if upload_date:
            try:
                date_obj = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
                stats.append(f"Published: {formatted_date}")
            except:
                stats.append(f"Published: {upload_date}")

        if stats:
            content_parts.append(f"Video Details: {' | '.join(stats)}")

        if keywords:
            content_parts.append(f"Topics/Tags: {keywords}")

        # Enhanced description processing
        if description:
            # Extract meaningful content from description
            desc_lines = description.split('\n')
            content_lines = []
            links = []

            for line in desc_lines:
                line = line.strip()
                if not line:
                    continue

                # Extract links
                if line.startswith('http') or 'http' in line:
                    url_matches = re.findall(r'https?://[^\s]+', line)
                    links.extend(url_matches)
                    # Remove URLs from description text
                    line = re.sub(r'https?://[^\s]+', '', line).strip()

                # Keep meaningful content
                if (len(line) > 15 and
                    not line.lower().startswith(('subscribe', 'follow', 'like', 'comment', 'share', 'download', 'visit', 'check out')) and
                    not re.match(r'^[#@]', line) and
                    not line.startswith('►')):
                    content_lines.append(line)

            # Build enhanced description
            enhanced_desc_parts = []

            if content_lines:
                main_desc = ' '.join(content_lines[:8])  # First 8 meaningful lines
                if len(main_desc) > 800:
                    main_desc = main_desc[:800] + "..."
                enhanced_desc_parts.append(f"Description: {main_desc}")

            if links:
                enhanced_desc_parts.append(f"Referenced Links: {len(links)} links mentioned")

            if enhanced_desc_parts:
                content_parts.extend(enhanced_desc_parts)

        # Add transcript if available
        if transcript_content:
            if len(transcript_content) > 1000:
                transcript_content = transcript_content[:1000] + "..."
            content_parts.append(f"Video Content Sample: {transcript_content}")
          # Add comment insights if available
        if comments_content:
            content_parts.append(f"Viewer Comments Sample: {comments_content}")

        final_content = '. '.join(content_parts)

        print(f"✅ YouTube content extracted: {len(final_content)} characters")
        print(f"📋 Title: {title[:50]}..." if title else "📋 Title: Not found")
        print(f"📋 Channel: {channel}" if channel else "📋 Channel: Not found")
        print(f"📋 Description length: {len(description) if description else 0}")
        print(f"📋 Transcript found: {len(transcript_content) > 0}")
        print(f"📋 Video ID: {video_id}" if video_id else "📋 Video ID: Not extracted")

        return {
            'title': title or 'YouTube Video',
            'content': final_content,
            'url': url,
            'type': 'youtube_video',
            'channel': channel,
            'description': description[:800] if description else '',
            'video_id': video_id,
            'duration': duration,
            'views': views,
            'upload_date': upload_date,
            'keywords': keywords,
            'transcript_sample': transcript_content[:500] if transcript_content else '',
            'extracted_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error extracting YouTube content: {e}")
        import traceback
        traceback.print_exc()
        return None
    
def extract_general_website_content(soup, url):
    """Extract content from general websites with robust fallbacks and better paragraph structure"""
    print("🌐 Extracting general website content...")

    try:
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()

        # Try to extract main content from common containers
        main_content = None
        content_selectors = [
            'article', 'main', '[role="main"]', '.content', '.main-content',
            '.post-content', '.entry-content', '.article-content', '.story-body',
            '#content', '#main-content', '.container', '#mw-content-text'
        ]

        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = elements[0]
                break

        # If no specific content container found, use body
        if not main_content:
            main_content = soup.find('body')

        if not main_content:
            return None

        # Get title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()

        # Try to extract all <p> tags as paragraphs (best for most sites)
        paragraphs = [p.get_text(" ", strip=True) for p in main_content.find_all('p') if len(p.get_text(strip=True)) > 30]
        clean_text = '\n\n'.join(paragraphs)

        # Fallback: If still too short, try <div> and <span> tags
        if len(clean_text) < 100:
            divs = [d.get_text(" ", strip=True) for d in main_content.find_all('div') if len(d.get_text(strip=True)) > 40]
            spans = [s.get_text(" ", strip=True) for s in main_content.find_all('span') if len(s.get_text(strip=True)) > 40]
            all_blocks = paragraphs + divs + spans
            clean_text = '\n\n'.join(all_blocks)

        # Fallback: If still too short, get all visible text from <body>
        if len(clean_text) < 100:
            body = soup.find('body')
            if body:
                text = body.get_text(separator='\n\n', strip=True)
                if len(text) > len(clean_text):
                    clean_text = text

        # Final fallback: get all text from soup
        if len(clean_text) < 100:
            text = soup.get_text(separator='\n\n', strip=True)
            if len(text) > len(clean_text):
                clean_text = text

        # Limit content length for summarization
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "..."

        print(f"✅ Successfully extracted content: {len(clean_text)} characters")

        return {
            'title': title,
            'content': clean_text,
            'url': url,
            'type': 'website',
            'extracted_at': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error extracting general website content: {e}")
        return None



def create_website_summary_response(query, website_data, bot_id=None):
    """Create a concise, persona-based summary of website content using AI"""
    print(f"📝 Creating AI-powered website summary response...")

    if not website_data:
        return f"I was unable to fetch content from the website you provided. Please check the URL and try again."

    title = website_data.get('title', 'Untitled')
    content = website_data.get('content', '')
    url = website_data.get('url', '')
    content_type = website_data.get('type', 'website')

    print(f"[DEBUG] Extracted content length: {len(content)}")
    print(f"[DEBUG] Extracted content preview: {content[:200]}")

    if not content or len(content) < 50:
        return f"I was able to access the website '{title}' but couldn't extract enough readable content to provide a summary."

    # --- Fetch bot prompt and traits ---
    bot_prompt = ""
    traits = ""
    if bot_id:
        try:
            bot_prompt = get_bot_prompt(bot_id)
            # You can fetch traits if you have them
        except Exception as e:
            print(f"Error fetching bot prompt: {e}")

    # --- NEW PROMPT: 2-3 line summary, persona-based ---
    ai_prompt = (
        f"You are a helpful assistant. {bot_prompt} "
        f"Summarize the following website content in 2-3 clear, complete sentences, using your unique style and personality. "
        f"Do not cut off sentences in the middle. Focus on the main topics and key details. "
        f"Here is the content:\n\n{content[:1500]}"
    )

    summary_text = call_gemini_ai(ai_prompt, max_tokens=120)
    # Ensure summary is not cut in the middle of a sentence
    if summary_text and isinstance(summary_text, str):
        # Optionally, trim to the last full sentence if needed
        if not summary_text.strip().endswith(('.', '!', '?')):
            last_period = summary_text.strip().rfind('.')
            if last_period != -1:
                summary_text = summary_text.strip()[:last_period+1]
    else:
        summary_text = f"I was able to access the website '{title}' but couldn't extract enough readable content to provide a summary."

    return summary_text.strip().replace(",,", ",").replace(" ,", ",").replace(" .", ".")

def create_structured_website_fallback(query, website_data, bot_id=None):
    import re
    from datetime import datetime
    from bot_prompt import get_bot_prompt

    title = website_data.get('title', 'Untitled')
    content = website_data.get('content', '')
    url = website_data.get('url', '')
    content_type = website_data.get('type', 'website')

    # --- Fetch bot prompt and traits ---
    bot_prompt = ""
    traits = ""
    if bot_id:
        try:
            bot_prompt = get_bot_prompt(bot_id)
            from utils import get_botname
            traits = get_botname(bot_id) or ""
        except Exception as e:
            bot_prompt = ""
            traits = ""

    response_parts = []

    if content_type == 'youtube_video':
        response_parts.append("# 🎥 Comprehensive YouTube Video Analysis")
        response_parts.append(f"*Comprehensive analysis completed on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
        return "\n".join(response_parts)

    # For general websites
    if content:
        ai_prompt = (
            f"You are a helpful assistant. {bot_prompt} "
            f"Your personality traits: {traits}. "
            f"Summarize the following website content in 2-3 clear, well-structured paragraphs, "
            f"using your unique style and personality. Focus on the main topics and key details. "
            f"Separate each paragraph with a blank line.\n\n{content[:1500]}"
        )
        summary_text = call_gemini_ai(ai_prompt, max_tokens=100)
        if summary_text and isinstance(summary_text, str) and len(summary_text.strip().split()) > 20:
            paragraphs = re.split(r'\n{2,}', summary_text.strip())
            if len(paragraphs) < 2:
                sentences = re.split(r'(?<=[.!?])\s+', summary_text.strip())
                midpoint = len(sentences) // 2
                summary_text = " ".join(sentences[:midpoint]) + "\n\n" + " ".join(sentences[midpoint:])
            response_parts = [summary_text]
        else:
            sentences = re.split(r'(?<=[.!?])\s+', content)
            filtered = [s.strip() for s in sentences if len(s.strip()) > 40 and not s.strip().endswith(':')]
            fallback_summary = " ".join(filtered[:6])
            if not fallback_summary or len(fallback_summary.split()) < 30:
                fallback_summary = (
                    f"This website appears to provide information related to '{title or query}'. "
                    "It covers key topics and recent developments relevant to this subject. "
                    "For more details, please visit the website directly."
                )
            response_parts = [fallback_summary]
    else:
        response_parts = [
            f"I was able to access the website '{title}' but couldn't extract enough readable content to provide a summary."
        ]

    response_parts.append(f"*Summary generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    return "\n\n".join(response_parts)
