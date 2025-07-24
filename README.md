## News Summarizer App
A Flask-based web application that fetches, summarizes, and analyzes news articles from various sources, with sentiment analysis and export options.
## Description
The News Summarizer App is designed to provide users with concise summaries of news articles, leveraging the Hugging Face API for summarization and sentiment analysis. It supports news from India, world headlines, and custom searches by city or state. Users can save favorites and export them as PDF or CSV files.
## Features

Fetch news articles from multiple sources using the NewsAPI.
Summarize articles using the Hugging Face BART model.
Analyze sentiment with a pre-trained DistilBERT model.
Filter news by category (e.g., Technology, Sports).
Save and manage favorite articles.
Export favorites as PDF or CSV.
Responsive web interface built with Bootstrap.

## Prerequisites

Python 3.10 or higher
Git (for version control)
A Hugging Face API key
A NewsAPI key

## Installation

1. Clone the repository:
```
git clone https://github.com/AbbuRehan-SD/news-summarizer.git
cd news-summarizer
```

2. Create a virtual environment and activate it:
```
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```
(Note: Create a requirements.txt file with pip freeze > requirements.txt after installing dependencies like flask, requests, python-dotenv, reportlab.)

4. Set up environment variables:
Create a .env file in the project root.
Add your API keys:
```
HF_API_KEY=your_hf_api_key
NEWS_API_KEY=your_news_api_key
```

## Usage

1. Run the application:
```python app.py
```

2. Open your browser and go to http://127.0.0.1:5000.
3. Explore news categories (India, World) or search by keyword.
4. Save articles to favorites and export them as needed.

## Development

Frontend: HTML, CSS (Bootstrap), JavaScript
Backend: Python (Flask)
APIs: NewsAPI, Hugging Face Inference API

## Contributing
Feel free to fork this repository, make improvements, and submit pull requests. Issues and feature requests are welcome!
## License
MIT License (Add a LICENSE file if desired, e.g., copy from choosealicense.com).
## Acknowledgements

NewsAPI for news data.
Hugging Face for NLP models.
Bootstrap for the UI framework.
