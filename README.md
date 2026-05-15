# 🏏 IPL Data Analysis Dashboard & Match Predictor


### 📌 Overview

This project is a comprehensive IPL (Indian Premier League) analytics system that provides in-depth insights into teams, players, and tournament performance from **2008 to 2025**.
It also includes a machine learning-based **Match Win Predictor** that forecasts match outcomes using historical data.



## 🚀 Key Features

### (a) Overview Dashboard

* Total matches, seasons, teams
* Total runs, wickets, sixes, fours
* Highest & lowest team scores
* Season-wise trends and team success comparison

### (b) Team Analysis

* Matches played, wins, losses, win %
* Season-wise performance
* Toss impact analysis
* Head-to-head comparison
* Rivalry insights

### (C) Player Analysis

#### 🟢 Batsmen

* Top 10 run-scorers
* Stats: average, strike rate, boundaries, centuries
* Player deep-dive with season performance

#### 🔴 Bowlers

* Top 10 wicket-takers
* Stats: economy, bowling average, 4W/5W hauls
* Individual performance analysis



### (d) Tournament Insights

* Year-wise points table (NRR, points, wins)
* Venue analysis (avg score, batting friendliness)
* Season winners, Orange Cap & Purple Cap holders


### (e) Match Win Predictor

A machine learning model that predicts match outcomes based on match conditions.

### 📊 Model Details

* **Algorithm:** Gradient Boosting Classifier
* **Accuracy:** ~81%
* **Precision:** ~81%
* **Recall:** ~81%
* **F1-Score:** ~81%

### 🔍 Input Features

* Teams (Team 1 & Team 2)
* Toss winner
* Toss decision (bat/field)
* Venue

### 📈 Key Insights

* Venue-specific performance is the most influential factor
* Toss decisions significantly impact match outcomes
* Context-based features outperform overall team statistics



## 📁 Project Structure

```
IPL-Data-Analysis/
├── assets/
├── data/
│   ├── deliveries.csv
│   └── matches.csv
├── models/
│   └── predictor.py
├── utils/
│   ├── data_loader.py
│   └── generate_data.py
├── app.py
├── analysis.ipynb
├── requirements.txt
└── README.md
```

---

### 🛠️ Tech Stack

* Python
* Pandas, NumPy
* Matplotlib, Seaborn
* Scikit-learn (Gradient Boosting)



---

### 📊 Results & Performance

* Achieved strong predictive performance with balanced evaluation metrics
* Model shows consistent results across both teams (no bias)
* Feature importance highlights the significance of venue and match conditions

---

### 🔮 Future Improvements

* Real-time IPL data integration
* Advanced explainability (SHAP)
* Improved UI/UX
* Deployment as a web application

---

### 🎯 Conclusion

This project combines **data analysis, visualization, and machine learning** to deliver a complete IPL analytics platform with both insights and predictive capabilities.
