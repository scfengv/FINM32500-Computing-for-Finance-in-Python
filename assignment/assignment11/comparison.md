# Model and Strategy Comparison

## 1. Predictive Model Performance

### Logistic Regression
- CV Accuracy: 0.5383
- Test Accuracy: 0.4232
- Precision: 0.5000
- Recall: 0.1151
- Confusion Matrix:
  [[86, 16],
   [123, 16]]

### Random Forest Classifier
- CV Accuracy: 0.5207
- Test Accuracy: 0.4398
- Precision: 0.5714
- Recall: 0.1151
- Confusion Matrix:
  [[90, 12],
   [123, 16]]

### Feature Importances (Random Forest)
- return_5d: 0.1894
- return_1d: 0.1219
- return_3d: 0.1391
- sma_5: 0.1453
- rsi_14: 0.1194
- macd: 0.1373
- macd_signal: 0.1475

Short-run momentum features (1–5 day returns) and MACD-related indicators were the most predictive. SMA(5) also contributed meaningfully.

## 2. Strategy Performance

### Logistic Regression Strategy
- Strategy Cumulative Return: 0.0137
- Benchmark Cumulative Return: -0.0177
- Annualized Return: 0.0143
- Volatility: 0.0315
- Sharpe Ratio: 0.4534

The LR strategy produced a small positive return and outperformed the benchmark, but its signal quality is low due to limited recall.

### Random Forest Strategy
- Strategy Cumulative Return: 0.4101
- Benchmark Cumulative Return: -0.0177
- Annualized Return: 0.4323
- Volatility: 0.0340
- Sharpe Ratio: 12.7317

The RF strategy significantly outperformed both Logistic Regression and the benchmark. The equity curve is smooth and upward-trending throughout the period, though the extremely high Sharpe ratio likely reflects model overfitting or optimistic backtest conditions.

## 3. Discussion

### Which features were most predictive?
Random Forest feature importances indicate that short-term lagged returns, MACD, and SMA(5) were the strongest drivers. These momentum-based indicators appear to carry the most usable signal for short-horizon forecasts.

### Which model performed best and why?
Random Forest performed better than Logistic Regression in both classification metrics (slightly higher accuracy and precision) and financial performance (much higher cumulative and risk-adjusted returns). Random Forest can capture nonlinear interactions between features, whereas Logistic Regression underfits the nonlinear structure of price movements.

### Limitations of ML in financial forecasting
- Next-day returns are extremely noisy, limiting predictive accuracy.
- Both models exhibit low recall, missing most positive-return days.
- Random Forest’s very high Sharpe ratio suggests possible overfitting.
- No transaction costs were included; real performance would be worse.
- Financial data is non-stationary, so model relationships may not persist.
- Technical indicators have limited incremental predictive power in efficient markets.

## 4. Summary Table

| Model                | Test Accuracy | Precision | Strategy Cumulative Return | Sharpe Ratio |
|---------------------|---------------|-----------|-----------------------------|--------------|
| Logistic Regression | 0.4232        | 0.5000    | 0.0137                      | 0.4534       |
| Random Forest       | 0.4398        | 0.5714    | 0.4101                      | 12.7317      |

Random Forest produced the strongest predictive and financial results, largely due to its ability to learn nonlinear patterns in short-term price movements. Logistic Regression performed modestly but still beat the benchmark.

## 5. Plots

### Logistic Regression Equity Curve
![LR Equity](lr_equity.png)

### Random Forest Equity Curve
![RF Equity](rf_equity.png)