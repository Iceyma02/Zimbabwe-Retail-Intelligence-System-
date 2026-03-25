# 🛒 ZimRetail IQ — Retail Intelligence Platform

> A full-stack retail analytics dashboard built for ZimRetail IQ.  
> 17 modules covering inventory, supply chain, financials, workforce, ML forecasting and more.  
> **Stack:** Python · Plotly Dash · SQLite · Pandas · Scikit-learn · Railway

---

## 📸 What This Is

A production-grade retail intelligence platform designed specifically for the **Zimbabwean FMCG market**. Built as a portfolio project demonstrating enterprise-level data engineering, analytics, and dashboard development.

All data is **simulated** for demonstration purposes. Logos and brand names used under fair use for portfolio/educational work only.

---

## 🗂️ Module Index

| # | Module | Description |
|---|--------|-------------|
| 1 | **National Overview** | CEO pulse — KPIs, alerts, revenue trends across all 9 stores |
| 2 | **Map View** | Interactive Zimbabwe map with store pins color-coded by revenue |
| 3 | **Store Performance** | Revenue, profit, margin rankings and trend analysis |
| 4 | **Store P&L Engine** | Full profit & loss per store — revenue minus every cost layer |
| 5 | **Inventory Monitor** | Stock levels, expiry tracking, red/amber/green status alerts |
| 6 | **Stock Movement** | Why stock is moving — sales, delivery, damage patterns |
| 7 | **Demand Forecasting** | ML-powered 30-day demand predictions per product per store |
| 8 | **Reorder Optimizer** | Auto-ranked reorder queue with urgency scoring |
| 9 | **Supply Chain Pipeline** | End-to-end order visibility from supplier to shelf |
| 10 | **Supplier Credit & Risk** | Accounts payable × stock urgency — who to pay first |
| 11 | **Promotions ROI** | Revenue lift vs margin impact for every promotion |
| 12 | **Competitor Watch** | Price comparison vs Choppies, OK Zimbabwe, Spar, TM |
| 13 | **Customer Sentiment** | NPS scores, complaint trends, satisfaction heatmaps |
| 14 | **Workforce Intelligence** | Staff costs, overtime, labour % of revenue by store |
| 15 | **Shrinkage & Loss** | Theft, damage, expiry losses tracked and visualised |
| 16 | **Zimbabwe Market Watch** | USD/ZiG rate, inflation, fuel, load shedding, seasonal calendar |
| 17 | **Executive Reports** | One-click boardroom-ready summary with risks & recommendations |

---

## 🚀 Quick Start (Local)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/zimretail-iq.git
cd zimretail-iq
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate the database
```bash
python data/generate_data.py
```
This creates `data/zimretail_iq.db` with ~500,000 rows of realistic retail data.

### 5. Run the app
```bash
python app.py
```

Open your browser at **http://localhost:8050**

---

## ☁️ Deploy to Railway

### One-click deploy
1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select this repo
4. Railway auto-detects the config from `railway.json`
5. Your app will be live at `https://YOUR-APP.railway.app`

### Manual deploy via Railway CLI
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

> The `railway.json` `startCommand` auto-runs data generation before starting gunicorn.

---

## 🗃️ Project Structure

```
zimretail-iq/
├── app.py                  # Main Dash app + sidebar navigation
├── data/
│   ├── generate_data.py    # Full data generation script
│   ├── db.py               # Central database access layer
│   └── zimretail_iq.db     # SQLite database (auto-generated)
├── pages/                  # All 17 dashboard pages (Dash multi-page)
│   ├── overview.py
│   ├── map_view.py
│   ├── store_performance.py
│   ├── store_pnl.py
│   ├── inventory.py
│   ├── stock_movement.py
│   ├── forecasting.py
│   ├── reorder.py
│   ├── supply_chain.py
│   ├── supplier_credit.py
│   ├── promotions.py
│   ├── competitor.py
│   ├── sentiment.py
│   ├── workforce.py
│   ├── shrinkage.py
│   ├── market_watch.py
│   └── reports.py
├── components/
│   └── shared.py           # Reusable UI components + chart config
├── assets/
│   ├── style.css           # Global dark theme stylesheet
│   └── logos/              # Brand logos (add manually)
├── requirements.txt
├── Procfile
├── railway.json
└── README.md
```

---

## 🧠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Dashboard | Plotly Dash 2.17 + Dash Bootstrap Components |
| Maps | Plotly Mapbox (Carto Dark Matter tiles) |
| Charts | Plotly Express + Graph Objects |
| ML Forecasting | Custom trend + seasonal decomposition (Prophet-compatible logic) |
| Database | SQLite + Pandas |
| Data Generation | Faker + NumPy |
| Deployment | Railway + Gunicorn |
| Styling | Custom CSS + Google Fonts (Syne + DM Sans) |

---

## 🇿🇼 Zimbabwe-Specific Features

- **9 real ZimRetail IQ store locations** with accurate coordinates
- **Local product catalogue** — Dendairy, Olivine, National Foods, Lobels, Colcom, Tanganda, Mazoe etc.
- **Zimbabwe Economic Layer** — USD/ZiG exchange rate, inflation, fuel, load shedding
- **Seasonal calendar** — Independence Day, Heroes Day, Easter, Christmas demand patterns
- **Local competitor tracking** — Choppies, OK Zimbabwe, Spar, TM Supermarkets

---

## 📝 Disclaimer

> This project uses simulated data and real brand names/logos for **portfolio and educational purposes only**.  
> It is not affiliated with, endorsed by, or connected to Pick n Pay Group, TM Supermarkets, or any other brand mentioned.  
> All revenue figures, store data, supplier information and performance metrics are entirely fictional.

---

## 👤 Author

**Anesu Manjengwa (Icey)**  
BCA Final Year | Full-Stack Developer | Zimbabwe 🇿🇼  
[GitHub](https://github.com/YOUR_USERNAME) · [LinkedIn](https://linkedin.com/in/YOUR_PROFILE)

---

*Built with 🔥 as a portfolio project — March 2025*
