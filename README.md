_**Financial Risk Dashboard**_

This project is an end-to-end financial risk analytics platform built with Python. It ingests live stock price data (Alpha Vantage API) and financial news (Marketaux API), computes rolling volatility and sentiment scores (using NLTK VADER), and stores everything in a SQL database. A custom risk engine combines these signals into daily risk scores, which are visualized in an interactive Streamlit dashboard.

Risk in this context is defined as the following: A combination of price volatility and news sentiment. A stock is riskier if it has higher price swings and more negative news coverage compared to peers. The dashboard shows which stocks’ risk profiles are rising or falling day by day.

Key features:

Automated ETL pipelines for prices and news

Sentiment analysis on financial headlines

Rolling volatility and z-score normalization for fair comparison

Interactive charts and “Top Risk Movers” view for insights at a glance

See a Live Demo here (Refresh Data to restart the data) : https://stock-analysis-python-project-fsqfcnqsb4ojqtsujzkyxy.streamlit.app/
