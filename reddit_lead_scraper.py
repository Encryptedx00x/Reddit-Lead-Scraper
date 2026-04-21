import os, praw, json, time, random
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent="GEOAgency/1.0 by u/" + os.getenv("REDDIT_USERNAME")
)

KEYWORDS = ["need seo", "ai search", "generative seo", "marketing help", "singapore business", "visibility drop"]
SUBREDDITS = ["SEO", "marketing", "Entrepreneur", "singapore", "smallbusiness", "startups"]
LOOKBACK_DAYS = 7

def scrape_leads():
    leads = []
    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    for sub in SUBREDDITS:
        for submission in reddit.subreddit(sub).new(limit=100):
            if submission.created_utc < cutoff.timestamp():
                continue
            text = (submission.title + " " + submission.selftext).lower()
            if any(kw in text for kw in KEYWORDS):
                leads.append({
                    "id": submission.id,
                    "subreddit": sub,
                    "title": submission.title,
                    "url": submission.url,
                    "author": str(submission.author),
                    "score": submission.score,
                    "timestamp": submission.created_utc
                })
            time.sleep(random.uniform(0.5, 1.2))
    with open("leads_queue.json", "w") as f:
        json.dump(leads, f, indent=2)
    print(f"✅ {len(leads)} leads capturados.")

if __name__ == "__main__":
    scrape_leads()