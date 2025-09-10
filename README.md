_**Financial Risk Dashboard**_

This project is an end-to-end financial risk analytics platform built with Python. It ingests live stock price data (Alpha Vantage API) and financial news (Marketaux API), computes rolling volatility and sentiment scores (using NLTK VADER), and stores everything in a SQL database. A custom risk engine combines these signals into daily risk scores, which are visualized in an interactive Streamlit dashboard.

Key features:

Automated ETL pipelines for prices and news

Sentiment analysis on financial headlines

Rolling volatility and z-score normalization for fair comparison

Interactive charts and “Top Risk Movers” view for insights at a glance

See a Live Demo here: https://stock-analysis-python-project-fsqfcnqsb4ojqtsujzkyxy.streamlit.app/
