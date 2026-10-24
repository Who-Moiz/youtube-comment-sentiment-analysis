
import os
import re
import random
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
MAX_COMMENTS_TO_COLLECT = 5000
TARGET_SAMPLE_SIZE = 2000
RANDOM_SEED = 42

OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

if not API_KEY:
    raise ValueError(
        "YouTube API key missing. Add YOUTUBE_API_KEY to your .env file."
    )


# --------------------------------------------------
# 2. Extract the YouTube video ID
# --------------------------------------------------

def extract_video_id(url):
    patterns = [
        r"(?:youtube\.com/watch\?.*?v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube URL. Please check the video link.")


# --------------------------------------------------
# 3. Collect YouTube comments
# --------------------------------------------------

def collect_comments(youtube, video_id):
    comments = []
    page_token = None

    while len(comments) < MAX_COMMENTS_TO_COLLECT:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=page_token,
            textFormat="plainText",
            order="relevance"
        )

        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]

            comment_text = snippet.get("textOriginal", "").strip()

            if comment_text:
                comments.append(comment_text)

            if len(comments) >= MAX_COMMENTS_TO_COLLECT:
                break

        print(f"Comments collected: {len(comments)}")

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    # Remove duplicate comment text
    comments = list(dict.fromkeys(comments))

    return comments


# --------------------------------------------------
# 4. Sentiment analysis
# --------------------------------------------------

def classify_sentiment(text, analyzer):
    score = analyzer.polarity_scores(text)["compound"]

    if score >= 0.05:
        label = "Positive"
    elif score <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    return score, label


# --------------------------------------------------
# 5. Generate visualizations
# --------------------------------------------------

def generate_charts(df):
    categories = ["Positive", "Neutral", "Negative"]

    counts = df["sentiment"].value_counts().reindex(
        categories, fill_value=0
    )

    # Bar chart
    plt.figure(figsize=(8, 5))
    counts.plot(kind="bar")
    plt.title("YouTube Comment Sentiment Distribution")
    plt.xlabel("Sentiment")
    plt.ylabel("Number of Comments")
    plt.xticks(rotation=0)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "sentiment_distribution.png",
        dpi=300
    )
    plt.close()

    # Pie chart
    plt.figure(figsize=(7, 7))
    plt.pie(
        counts,
        labels=categories,
        autopct="%1.1f%%",
        startangle=90
    )
    plt.title("Sentiment Percentage Distribution")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "sentiment_percentages.png",
        dpi=300
    )
    plt.close()

    return counts


# --------------------------------------------------
# 6. Create a Markdown report
# --------------------------------------------------

def generate_report(
    title, url, video_id, collected_count, df, counts
):
    total = len(df)
    percentages = counts / total * 100
    average_score = df["compound_score"].mean()

    report = f"""# YouTube Comment Sentiment Analysis Report

## 1. Video Information

- Video title: {title}
- Video URL: {url}
- Video ID: {video_id}
- Analysis date: {datetime.now().strftime("%Y-%m-%d")}

## 2. Dataset

- Unique comments collected: {collected_count}
- Comments analyzed: {total}
- Sampling: Random sampling with fixed seed {RANDOM_SEED}
- Comment type: Top-level comments

## 3. Methodology

Comments were retrieved through YouTube Data API v3.
Duplicate comment text was removed before random sampling.

VADER was used to calculate compound sentiment scores.
Scores >= 0.05 were labeled Positive, scores <= -0.05
were labeled Negative, and intermediate scores were
labeled Neutral.

## 4. Results

| Sentiment | Count | Percentage |
|---|---:|---:|
| Positive | {counts["Positive"]} | {percentages["Positive"]:.2f}% |
| Neutral | {counts["Neutral"]} | {percentages["Neutral"]:.2f}% |
| Negative | {counts["Negative"]} | {percentages["Negative"]:.2f}% |

Average compound score: {average_score:.4f}

## 5. Interpretation

The largest sentiment category was {counts.idxmax()}.
The labels estimate the emotional polarity expressed
in the comments; they do not establish the quality of
the video or the opinions of every viewer.

## 6. Limitations

VADER is primarily designed for English social-media text.
Sarcasm, slang, context, and other languages can affect
classification quality. Results represent the analyzed
sample, not necessarily all viewers.

The final sample may contain fewer than 2,000 comments
if fewer unique accessible comments are available.

## 7. Conclusion

This project demonstrates data collection, random sampling,
sentiment analysis, visualization, and automated reporting
using Python.

## 8. Output Files

- youtube_comments.csv
- youtube_sentiment_results.csv
- sentiment_distribution.png
- sentiment_percentages.png
- sentiment_report.md
"""

    (OUTPUT_DIR / "sentiment_report.md").write_text(
        report, encoding="utf-8"
    )

    return report


# --------------------------------------------------
# 7. Run the complete project
# --------------------------------------------------

def main():
    url = input("Paste a YouTube video URL: ").strip()
    video_id = extract_video_id(url)

    youtube = build(
        "youtube", "v3", developerKey=API_KEY
    )

    # Fetch video title
    video_response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    if not video_response.get("items"):
        raise ValueError(
            "Video not found or unavailable through the API."
        )

    title = video_response["items"][0]["snippet"]["title"]
    print(f"\nVideo: {title}")

    # Collect comments
    comments = collect_comments(youtube, video_id)

    if not comments:
        raise ValueError(
            "No accessible comments found. Check whether comments "
            "are enabled and the video is accessible."
        )

    print(f"\nUnique comments available: {len(comments)}")

    # Randomly select comments
    sample_size = min(TARGET_SAMPLE_SIZE, len(comments))

    random.seed(RANDOM_SEED)
    sampled_comments = random.sample(comments, sample_size)

    # Save raw comments
    comments_df = pd.DataFrame({
        "comment": sampled_comments
    })

    comments_df.to_csv(
        OUTPUT_DIR / "youtube_comments.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Analyze sentiment
    analyzer = SentimentIntensityAnalyzer()
    scores = [
        classify_sentiment(comment, analyzer)
        for comment in sampled_comments
    ]

    df = pd.DataFrame({
        "comment": sampled_comments,
        "compound_score": [s[0] for s in scores],
        "sentiment": [s[1] for s in scores]
    })

    df.to_csv(
        OUTPUT_DIR / "youtube_sentiment_results.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Charts and report
    counts = generate_charts(df)

    report = generate_report(
        title, url, video_id, len(comments), df, counts
    )

    print("\n--- Sentiment Results ---")
    print(counts)
    print("\nSentiment percentages:")
    print((counts / len(df) * 100).round(2))
    print(f"\nComments analyzed: {len(df)}")
    print(f"\nResults saved in: {OUTPUT_DIR.resolve()}")
    print("\n--- Report ---")
    print(report)


if __name__ == "__main__":
    try:
        main()
    except HttpError as error:
        print("\nYouTube API request failed.")
        print("Check your API key, quota, video URL, and comment access.")
        print(error)
    except (ValueError, RuntimeError) as error:
        print(f"\nError: {error}")
