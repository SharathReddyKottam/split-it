# 💸 Split It

🌐 **Live Demo:** [split-it.streamlit.app](https://split-it.streamlit.app)
> Split bills, track spending and settle debts — built with Python, Streamlit & Pandas

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red?style=flat-square)
![Pandas](https://img.shields.io/badge/Pandas-Latest-green?style=flat-square)
![Plotly](https://img.shields.io/badge/Plotly-Latest-purple?style=flat-square)
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow?style=flat-square)

---

## 📖 About

**Split It** is a full-featured group expense splitting web app inspired by Splitwise.
Built entirely with Python and Streamlit, it lets you create groups, track shared expenses,
visualize spending patterns, and settle debts — all from a clean interactive dashboard.

---

## ✨ Features

### Core
- 👥 **Groups** — Create groups and manage members
- 🧾 **Expenses** — Add expenses with flexible split options
- ✅ **Member Selection** — Tick only the people involved in each transaction
- ⚖️ **Balances** — See exactly who owes who across all expenses
- ✅ **Settle Up** — Mark full or partial payments as settled

### Analytics
- 📊 **Dashboard** — Spending breakdown by category, member and time
- 📅 **Monthly Report** — Track and compare spending month by month
- 🏆 **Leaderboard** — Rankings, records and fun spending stats
- 🗓️ **Heatmap** — GitHub-style calendar view of daily spending

### Productivity
- 🔍 **Search & Filter** — Find any expense by name, date, amount or category
- 📥 **Import Excel** — Upload bank or card statements and auto-import transactions
- ⬇️ **Export CSV** — Download reports and filtered results

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web app framework |
| Pandas | Data manipulation |
| Plotly | Interactive charts |
| Calplot | Calendar heatmap |
| Matplotlib | Chart rendering |
| OpenPyXL | Excel file handling |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/SharathReddyKottam/split-it.git
cd split-it
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```

### 4. Open in browser
```
http://localhost:8501
```

---

## 📁 Project Structure

```
split-it/
│
├── app.py                      # Home page & quick stats
│
├── pages/
│   ├── 1_Groups.py             # Create & manage groups
│   ├── 2_Expenses.py           # Add & split expenses
│   ├── 3_Balances.py           # Who owes who
│   ├── 4_Settle_Up.py          # Mark debts as paid
│   ├── 5_Dashboard.py          # Spending analytics
│   ├── 6_Monthly_Report.py     # Monthly trends
│   ├── 7_Leaderboard.py        # Rankings & stats
│   ├── 8_Heatmap.py            # Calendar heatmap
│   ├── 9_Search_Filter.py      # Search & filter
│   └── 10_Import_Excel.py      # Import from Excel
│
├── utils/
│   ├── file_helpers.py         # CSV read/write functions
│   └── calculations.py        # Balance calculations
│
├── data/                       # CSV storage (auto created)
│   ├── groups.csv
│   ├── expenses.csv
│   └── settlements.csv
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 📱 How to Use

1. **Create a Group** — Go to Groups page, add a group name and members
2. **Add Expenses** — Go to Expenses, select your group, tick involved members and add the bill
3. **Check Balances** — Go to Balances to see who owes who
4. **Settle Up** — Go to Settle Up and click Settle next to any debt
5. **Import from Excel** — Go to Import Excel, upload your bank statement and auto-import
6. **Explore Analytics** — Visit Dashboard, Monthly Report, Leaderboard and Heatmap

---

## 📸 Pages Overview

| Page | Description |
|---|---|
| 🏠 Home | Quick stats overview |
| 👥 Groups | Create and manage friend groups |
| 🧾 Expenses | Add expenses with flexible splits |
| ⚖️ Balances | Net balance per person |
| ✅ Settle Up | Clear outstanding debts |
| 📊 Dashboard | Full spending analytics |
| 📅 Monthly Report | Month by month trends |
| 🏆 Leaderboard | Spending rankings |
| 🗓️ Heatmap | Calendar spending view |
| 🔍 Search & Filter | Find any expense |
| 📥 Import Excel | Upload bank statements |

---

## 👨‍💻 Author

**SharathReddy**
- GitHub: [@SharathReddyKottam](https://github.com/SharathReddyKottam)
- LinkedIn: [SharathReddy](https://www.linkedin.com/in/sharathreddyk/)

---

## 📄 License

MIT License — feel free to use, modify and distribute!

---

## 🗺️ Roadmap

- [ ] Edit & Delete expenses
- [ ] Export to PDF
- [ ] Export to Excel
- [ ] Dark / Light mode toggle
- [ ] Recurring expenses
- [ ] Currency support
- [ ] Data backup & restore

---

*Built with ❤️ using Python & Streamlit*
