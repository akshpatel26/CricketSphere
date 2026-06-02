# 🏏 CricketSphere — Cricket Analytics Hub

> An interactive multi-format cricket analytics dashboard built with **Streamlit**, covering IPL, T20 Internationals, ODIs, and Test cricket.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.x-purple?logo=plotly)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 Preview

| IPL Dashboard | T20 Analytics | Test Rankings |
|---|---|---|
| Team H2H, Win Predictor, Points Table | Career Arc, Ball Heatmap, Matchups | Dot Ball Analysis, Country/Venue Stats |

---

## ✨ Features

### 🏏 IPL (Indian Premier League)
- **Overview** — Season-wise match counts, KPIs (runs, wickets, sixes, fours), toss analysis, IPL Champions wall (2008–2025)
- **Team Analysis** — Season performance, H2H records, toss impact, rivalry insights for all 10 franchises
- **Player Analysis** — Top 10 batsmen & bowlers (all-time), deep-dive metrics, season-wise run charts
- **Tournament Insights** — Points tables (every season 2008–2025), venue stats, season winners with Orange/Purple Cap
- **Win Predictor** — Gradient Boosting model with accuracy metrics, feature importance, and confusion matrix

### ⚡ T20 International
- Host countries & venue breakdown with chase/toss win %
- Top wicket-takers with economy-vs-wickets scatter
- Top run-scorers with career arc (batting & bowling journey)
- Sixes & fours by player and by team
- Team rankings with win % treemap
- **Advanced Insights** — Head-to-head, ball heatmap, batsman–bowler matchup matrix, seasonal trends with anomaly detection

### 🌏 ODI International
- Countries & venues analysis
- Wicket-takers and run-scorers with comparative charts
- Sixes & fours (player + team level)
- Team rankings with win % treemap

### 🎩 Test Cricket
- Countries & top venues by matches hosted
- Top wicket-takers (filters: team, innings, min wickets) with average vs SR scatter
- Top run-scorers with centuries/fifties grouped bar and average vs SR scatter
- Team rankings — wins/losses/draws stacked bar + win %
- Dot ball analysis by bowler or team

---

## 🗂️ Project Structure

```
CricketSphere/
│
├── app.py                  # Main Streamlit entry point
│
├── data/                   # Raw CSV datasets
│   ├── ipl_matches.csv
│   ├── ipl_deliveries.csv
│   ├── t20_*.csv
│   ├── odi_*.csv
│   └── test_*.csv
│
├── utils/
│   ├── data_loader.py      # IPL data loading & stat computation
│   ├── t20_analysis.py     # T20I analysis functions
│   ├── odi_loader.py       # ODI data loading
│   ├── odi_analysis.py     # ODI analysis functions
│   ├── test_loader.py      # Test data loading
│   └── test_analysis.py    # Test analysis functions
│
└── models/
    └── predictor.py        # Gradient Boosting win predictor
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/cricketsphere.git
cd cricketsphere

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📦 Dependencies

```txt
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
scikit-learn>=1.3.0
```

You can generate the file with:

```bash
pip freeze > requirements.txt
```

---

## 📊 Data Sources

| Format | Coverage | Source |
|--------|----------|--------|
| IPL | 2008 – 2025 | [Kaggle IPL Dataset](https://www.kaggle.com/datasets/patrickb1912/ipl-complete-dataset-20082020) |
| T20I | 2005 – 2024 | [Cricsheet](https://cricsheet.org/) |
| ODI | 1971 – 2024 | [Cricsheet](https://cricsheet.org/) |
| Test | 1877 – 2024 | [Cricsheet](https://cricsheet.org/) |

> **Note:** Place all downloaded CSV files inside the `/data` directory before running the app.

---

## 🔮 Win Predictor (IPL)

The predictor uses a **Gradient Boosting Classifier** trained on historical IPL match data. Features include:

- Team encodings
- Toss winner & toss decision
- Venue
- Historical win percentages and head-to-head stats

Model performance is displayed live in the app (Accuracy, Precision, Recall, F1-Score).

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Built with ❤️ for cricket fans and data enthusiasts.

---

*"Cricket is not just a game — it's a data goldmine."*