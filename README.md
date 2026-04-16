# 📊 PhonePe Transaction Insights Dashboard

An interactive data analytics dashboard built using **Streamlit**, **MySQL**, and **Bokeh** to analyze PhonePe transaction data across India.

---

## 🚀 Features

* 📌 Overview Dashboard with key metrics
* 🗺️ State-wise Transaction Map (India Geo Visualization)
* 📈 Transaction Trend Analysis (Quarter-wise)
* 🎯 Dynamic filtering (Year & Quarter)
* ⚡ Optimized performance using caching

---

## 🛠 Tech Stack

* Python
* Streamlit
* MySQL
* Bokeh
* Plotly
* Pandas

---

## 📂 Project Structure

```
PhonePe-Transaction-Insights/
│
├── app.py
├── requirements.txt
├── README.md
```

---

## ▶️ Run Locally

### 1. Clone repository

```
git clone https://github.com/gokulraj-5/phonepe-transaction-insights.git
cd phonepe-transaction-insights
```

---

### 2. Install dependencies

```
pip install -r requirements.txt
```

---

### 3. Run application

```
streamlit run app.py
```

---

## ⚙️ Configuration

Update your database credentials using Streamlit secrets:

Create `.streamlit/secrets.toml`

```
db_user = "your_user"
db_password = "your_password"
db_host = "localhost"
db_name = "phonepe"
```

---

## 📦 Dataset

Dataset sourced from PhonePe Pulse GitHub:

```
https://github.com/PhonePe/pulse
```

Clone dataset manually:

```
git clone https://github.com/PhonePe/pulse.git
```

---

## ⚠️ Notes

* Do NOT upload `.streamlit/secrets.toml` (contains credentials)
* Ensure MySQL server is running before starting app

---

## 👨‍💻 Author

Gokulraj V
AI & ML Enthusiast

---

## ⭐ If you like this project, give it a star!
