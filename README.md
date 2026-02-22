# How to run
```
pip install -r requirements.txt
streamlit run app.py  
```

# Functionarities

## Price history
You can register ticker symbols. The app downloads data from Yahoo Finance and lets you choose which tickers to display on the graph.

You can also select the time range using the slider at the top.

<img width="1266" height="734" alt="price_history" src="https://github.com/user-attachments/assets/9e6c849e-c414-4f09-8c79-847d6607b6df" />

## Sharpe ratio

You can set the risk-free rate and the rolling window size.

<img width="1266" height="501" alt="sharpe_ratio" src="https://github.com/user-attachments/assets/f113b9f2-ec22-4398-95fa-e3d27f72bc91" />

## Summary

Displays the Sharpe ratio and return for all registered tickers.

<img width="1266" height="709" alt="summary" src="https://github.com/user-attachments/assets/66ceea4e-0eb3-46f7-b872-2ada5c55a81d" />

---

### Thanks

I asked Claude Code to build this app, and it did all the work in 30 minuts. I didn’t write any code. Thanks, CC. :)
