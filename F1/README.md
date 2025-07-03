# 🏁 F1 Podium Prediction Engine (2020–2024)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/yourusername/f1-podium-predictor?style=social)](https://github.com/yourusername/f1-podium-predictor/stargazers)
[![Issues](https://img.shields.io/github/issues/yourusername/f1-podium-predictor)](https://github.com/yourusername/f1-podium-predictor/issues)

Predict podium finishers for Formula 1 races using historical performance, qualifying results, driver form, and track-specific metrics. Built with Python, `scikit-learn`, and `xgboost`, this engine combines handcrafted features and ML modeling to deliver interpretable predictions for 2020–2024 seasons.

---

## 📦 Features

- ✅ Predict podium finishers for any race between 2020–2024
- 🧹 Cleans and normalizes large F1 JSON datasets
- 🧠 Enhanced feature engineering (recent form, qualifying score, DNF rate, hot streaks)
- 📊 Built with Random Forest and XGBoost (classification)
- 💬 Interpretable results with top prediction confidence and reasoning
- 🏎️ Track-specific stats for smarter forecasting

---

## 📈 Tech Stack

| Area                   | Tools / Libraries                |
| ---------------------- | -------------------------------- |
| Language               | Python 3.10+                     |
| Data Processing        | `pandas`, `numpy`                |
| Machine Learning       | `scikit-learn`, `xgboost`        |
| CLI & Arguments        | `argparse`                       |
| Visualization (Future) | `matplotlib`, `plotly` (planned) |

---

## 🧠 Machine Learning Details

### Feature Engineering Highlights:

- **`quali_score`**: Normalized from P1–P20
- **`recent_form`**: Weighted score from last 3–5 races
- **`avg_pos_change`**: Race improvement over starting grid
- **`hot_streak`**: Detects upward momentum
- **`track_podiums`**: Track-specific podium count
- **`dnf_rate`**: Weighted down to reflect reliability

### Model:

- ✅ `RandomForestClassifier` with `class_weight=balanced`
- 📉 Output is **podium probability** per driver
- 🔍 Ranked by probability with full explanation for each prediction

---

## 🗃️ Example Output

```json
{
  "race_predicted": "Monaco Grand Prix",
  "predicted_podium": ["VER", "NOR", "LEC"],
  "confidence_level": 84.7,
  "key_factors": {
    "VER": "On hot streak, Strong recent form, 2 past podiums at this track",
    "NOR": "Race day improver, Good qualifier",
    ...
  }
}
🚀 Getting Started
1. Clone the Repo
bash
Copy
Edit
git clone https://github.com/yourusername/f1-podium-predictor.git
cd f1-podium-predictor
2. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
3. Predict a Race
bash
Copy
Edit
python podium_predictor.py --race "Monaco"
Optional:

bash
Copy
Edit
--db_dir ./DataBase --history_years 2021 2022 2023
🗂️ Folder Structure
bash
Copy
Edit
F1-Podium-Predictor/
├── podium_predictor.py         # Main script
├── DataBase/                   # Cleaned JSONs: 2020–2024
│   ├── F1_Seasons_Cleaned_2020.json
│   ├── ...
├── race_prediction_2024.json   # Example output
├── README.md
📊 2025 Upgrade in Progress
We've cleaned and structured a complete 2025 dataset, with plans to:

🎯 Train a new model on early 2025 season trends

📉 Include weather, safety car, and penalty data

📈 Shift from binary podium prediction → regression of full race order

🌐 Deploy as a web dashboard using Streamlit + GitHub Pages

Stay tuned! 🚦

🤝 Contributions Welcome
Pull requests are welcome for:

🏎️ Improved features

🤖 Alternate models (e.g. LGBM, CatBoost)

📊 Visualization or dashboard integrations

If you find this helpful, please ⭐ the repo and share it!

📄 License
This project is licensed under the MIT License. See LICENSE for details.

👨‍💻 Author
Joseph N. Nimyel
F1 enthusiast | AI & Data Engineer | Creator of this project
GitHub • LinkedIn

“The data never lies — but F1 qualifying does.”
```
