from flask import Flask, render_template, request, redirect, url_for, send_file
import requests, time, threading, webbrowser, hashlib, json, os
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
import csv
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")


# API Keys
HF_API_KEY = os.getenv("HF_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# HuggingFace Headers and APIs
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}
SUMMARIZATION_API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
SENTIMENT_API = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

# Cache folder
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(key):
    return os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".json")

def save_to_cache(key, data):
    cache_data = {
        "timestamp": int(time.time()),
        "data": data
    }
    with open(cache_path(key), "w") as f:
        json.dump(cache_data, f)

def load_from_cache(key):
    path = cache_path(key)
    if os.path.exists(path):
        with open(path) as f:
            cache_data = json.load(f)
        # Check if cache_data is a dictionary with a timestamp
        if isinstance(cache_data, dict) and "timestamp" in cache_data:
            if time.time() - cache_data.get("timestamp", 0) < 3600:
                return cache_data.get("data")
        # Handle legacy cache (plain list) by returning it without timestamp check
        elif isinstance(cache_data, list):
            return cache_data
    return None

# --- API Functions ---

def summarize_text(text):
    cache_key = "summary:" + text[:100]
    cached = load_from_cache(cache_key)
    if cached: return cached
    for _ in range(3):
        res = requests.post(SUMMARIZATION_API, headers=HEADERS, json={"inputs": text})
        if res.status_code == 200:
            try:
                summary = res.json()[0]["summary_text"]
                save_to_cache(cache_key, summary)
                return summary
            except:
                return "Summary error"
        elif "loading" in res.text.lower():
            time.sleep(3)
    return "Summary unavailable"

def analyze_sentiment(text):
    cache_key = "sentiment:" + text[:100]
    cached = load_from_cache(cache_key)
    if cached: return cached
    for _ in range(3):
        res = requests.post(SENTIMENT_API, headers=HEADERS, json={"inputs": text})
        if res.status_code == 200:
            try:
                sentiment = res.json()[0]["label"]
                save_to_cache(cache_key, sentiment)
                return sentiment
            except:
                return None
        elif "loading" in res.text.lower():
            time.sleep(3)
    return None

def parse_news(url, page_size):
    cached = load_from_cache(url)
    if cached:
        return cached[:page_size]

    res = requests.get(url)
    articles = []
    if res.status_code == 200:
        data = res.json()
        for article in data.get("articles", []):
            content = article.get("content") or article.get("description") or ""
            if content:
                summary = summarize_text(content)
                sentiment = analyze_sentiment(summary)
                published_at = article.get("publishedAt", "")
                published_fmt = relative_time(published_at)
                articles.append({
                    "title": article["title"],
                    "summary": summary,
                    "sentiment": sentiment,
                    "url": article["url"],
                    "source": article["source"]["name"],
                    "image": article.get("urlToImage"),
                    "published_at": published_fmt
                })
    save_to_cache(url, articles)
    return articles[:page_size]

def relative_time(timestr):
    try:
        dt = datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%SZ")
        delta = datetime.utcnow() - dt
        seconds = delta.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            return f"{int(seconds//60)} min ago"
        elif seconds < 86400:
            return f"{int(seconds//3600)} hrs ago"
        else:
            return dt.strftime("%d %b %Y")
    except:
        return ""

# --- News Fetching ---

def fetch_news_india(page=1):
    page_size = 10 if page == 1 else 5
    keywords = ["India", "Bharat", "Delhi", "Mumbai", "Chennai", "Hyderabad", "Bangalore", "Kolkata"]
    all_articles = []
    for keyword in keywords:
        url = f"https://newsapi.org/v2/everything?q={keyword}&language=en&sortBy=publishedAt&pageSize=5&page={page}&apiKey={NEWS_API_KEY}"
        all_articles += parse_news(url, 5)
    seen = set()
    unique = []
    for art in all_articles:
        if art["url"] not in seen:
            unique.append(art)
            seen.add(art["url"])
    return unique[:page_size]

def fetch_news_world(page=1):
    page_size = 10
    url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize={page_size}&page={page}&apiKey={NEWS_API_KEY}"
    return parse_news(url, page_size)

def fetch_news_query(query, page=1):
    page_size = 10
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize={page_size}&page={page}&apiKey={NEWS_API_KEY}"
    return parse_news(url, page_size)

# --- Routes ---

@app.route("/")
def home():
    return redirect(url_for("india_news"))

@app.route("/india")
def india_news():
    page = int(request.args.get("page", 1))
    articles = fetch_news_india(page)
    return render_template("index.html", articles=articles, page=page, category="India", query="")

@app.route("/world")
def world_news():
    page = int(request.args.get("page", 1))
    query = request.args.get("query", "")
    if query:
        articles = fetch_news_query(query, page)
    else:
        articles = fetch_news_world(page)
    return render_template("index.html", articles=articles, page=page, query=query, category="World")

@app.route("/search")
def search_city_state():
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    articles = fetch_news_query(query, page)
    return render_template("index.html", articles=articles, category="Search", query=query, page=page)

@app.route("/export/favorites/pdf", methods=["POST"])
def export_favorites_pdf():
    favorites = request.get_json()
    if not favorites:
        return {"error": "No favorites provided"}, 400

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    y = 800
    for idx, article in enumerate(favorites):
        p.drawString(30, y, f"{idx + 1}. {article['title']}")
        y -= 20
        p.drawString(40, y, f"Summary: {article['summary']}")
        y -= 20
        p.drawString(40, y, f"Source: {article['source']}")
        y -= 20
        p.drawString(40, y, f"URL: {article['url']}")
        y -= 40
        if y < 100:
            p.showPage()
            y = 800
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="favorites.pdf", mimetype="application/pdf")

@app.route("/export/favorites/csv", methods=["POST"])
def export_favorites_csv():
    favorites = request.get_json()
    if not favorites:
        return {"error": "No favorites provided"}, 400

    buffer = BytesIO()
    writer = csv.writer(buffer)
    writer.writerow(["Title", "Summary", "Source", "URL"])
    for article in favorites:
        writer.writerow([
            article['title'],
            article['summary'],
            article['source'],
            article['url']
        ])
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="favorites.csv", mimetype="text/csv")

# Auto-launch in browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False)
