# YouTube Comment Sentiment Analysis Report

## 1. Video Information

- Video title: Lose 150 Lbs Together, Win $250,000
- Video URL: https://youtu.be/RE3_PGwDwhw?si=vzwLxURj4xPMA6dJ
- Video ID: RE3_PGwDwhw
- Analysis date: 2026-10-24

## 2. Dataset

- Unique comments collected: 1139
- Comments analyzed: 1139
- Sampling: Random sampling with fixed seed 42
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
| Positive | 592 | 51.98% |
| Neutral | 372 | 32.66% |
| Negative | 175 | 15.36% |

Average compound score: 0.2489

## 5. Interpretation

The largest sentiment category was Positive.
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
