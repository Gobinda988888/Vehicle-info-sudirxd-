# 🚘 Vehicle Info Intelligence API

High-speed, serverless-ready Flask API to lookup vehicle RC (Registration Certificate) details in India. Designed for easy deployment on **Vercel**, **Render**, or **local environments**.

---

## ⚡ Features

- 🏎️ **Fast RC Lookup**: Scrapes and parses vehicle details accurately.
- 🌐 **Vercel Serverless Ready**: Configured out-of-the-box with `vercel.json` and python runtime handlers.
- 🛡️ **Input Sanitization**: Clean formatting and normalization for all registration numbers.
- 📦 **Structured Output**: Standardized JSON responses with developer branding.

---

## 🚀 Endpoints

### 1. Root Status Check
- **`GET /`**
- Returns API online status, developer details, and example routes.

### 2. Vehicle RC Lookup
- **`GET /api/vehicle?rc=BR03H5690`**
- **`GET /lookup/BR03H5690`**

#### 📋 Example Response:
```json
{
  "status": "success",
  "developer": {
    "name": "Sudhirxd",
    "github": "https://www.github.com/Sudhirxd",
    "instagram": "https://www.instagram.com/sudhirxd.in",
    "telegram": "https://t.me/Sudhirxd",
    "website": "https://www.sudhirxd.in"
  },
  "rc": "BR03H5690",
  "data": {
    "Owner Name": "...",
    "Maker Model": "...",
    "Vehicle Class": "...",
    "Fuel Type": "...",
    "Registration Date": "...",
    "Insurance Expiry": "...",
    "Registered RTO": "..."
  }
}
```

---

## 🛠️ Local Installation & Testing

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sudhirxd/Vehicle-info-sudirxd-.git
   cd Vehicle-info-sudirxd-
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the local server:**
   ```bash
   python api/index.py
   ```

4. **Test endpoint:**
   Open `http://127.0.0.1:5000/api/vehicle?rc=BR03H5690` in your browser or Postman.

---

## 👨‍💻 Developer & Credits

Crafted by **Sudhirxd**.
- **Website:** [sudhirxd.in](https://www.sudhirxd.in)
- **Telegram:** [@Sudhirxd](https://t.me/Sudhirxd)
- **Instagram:** [@sudhirxd.in](https://www.instagram.com/sudhirxd.in)
- **GitHub:** [Sudhirxd](https://github.com/Sudhirxd)