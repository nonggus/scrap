# 📊 BKK Financial Statements Scraper API

This project provides a FastAPI-based web service that scrapes **financial statements** (Income Statement, Balance Sheet, and Cash Flow Statement) from [StockAnalysis.com](https://stockanalysis.com) for companies listed on the **Bangkok Stock Exchange (BKK)**.

## 🚀 Features

- Fetches:
  - Income Statement
  - Balance Sheet
  - Cash Flow Statement
- Scrapes and transforms table data into clean JSON
- Built with FastAPI for high-performance API services

## 🗂️ Project Structure

```
scrap/
├── main.py               # Main FastAPI app
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## 📦 Installation & Running

1. **Clone the repository**

```bash
git clone https://github.com/nonggus/scrap.git
cd scrap
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Run the FastAPI server**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Access the API at: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Network Access: http://{your-ip}:8000

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/{symbol}/income/`       | Get Income Statement |
| `/{symbol}/balancesheet/` | Get Balance Sheet Statement |
| `/{symbol}/cashflow/`     | Get Cash Flow Statement |

### Example:

```
GET http://localhost:8000/ptt/income/
OR
GET http://<your-ip>:8000/ptt/income/
```

## 📤 Sample Response (JSON)

```json
{
  "Income Statement": [
    {
      "symbol": "PTT",
      "item": "revenue",
      "period": "FY",
      "date": "2023-12-31",
      "value": 2230000000.0,
      "created_at": "2025-05-12 13:45:00"
    },
    ...
  ]
}
```

## ⚠️ Notes

- If data is unavailable on the target site, an empty list or error message is returned.
- Dates are formatted as `YYYY-MM-DD`.
- The scraper relies on the current HTML structure of StockAnalysis.com, which may change.
- Values without decimal points are in millions.
- Values with decimals are those that were previously converted to percentages and then converted to float.

## 🙋 Author

- GitHub: [@nonggus](https://github.com/nonggus)
