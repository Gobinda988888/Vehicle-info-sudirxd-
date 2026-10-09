from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import quote

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

app = Flask(__name__)

DEVELOPER_INFO = {
    "github": "https://www.github.com/Sudhirxd",
    "instagram": "https://www.instagram.com/sudhirxd.in",
    "name": "Sudhirxd",
    "telegram": "https://t.me/Sudhirxd",
    "website": "https://www.sudhirxd.in"
}

DESIRED_ORDER = [
    "Owner Name", "Father's Name", "Owner Serial No", "Model Name", "Maker Model",
    "Vehicle Class", "Fuel Type", "Fuel Norms", "Registration Date", "Insurance Company",
    "Insurance No", "Insurance Expiry", "Insurance Upto", "Fitness Upto", "Tax Upto",
    "PUC No", "PUC Upto", "Financier Name", "Registered RTO", "Address", "City Name", "Phone"
]

LABEL_ALIASES = {
    "owner name": "Owner Name",
    "father's name": "Father's Name",
    "father name": "Father's Name",
    "owner serial no": "Owner Serial No",
    "code": "Owner Serial No",
    "model name": "Model Name",
    "modal name": "Model Name",
    "maker model": "Maker Model",
    "vehicle class": "Vehicle Class",
    "fuel type": "Fuel Type",
    "fuel norms": "Fuel Norms",
    "registration date": "Registration Date",
    "insurance company": "Insurance Company",
    "insurance no": "Insurance No",
    "insurance expiry": "Insurance Expiry",
    "insurance upto": "Insurance Upto",
    "fitness upto": "Fitness Upto",
    "tax upto": "Tax Upto",
    "puc no": "PUC No",
    "puc expiry in": "PUC Upto",
    "puc upto": "PUC Upto",
    "financier name": "Financier Name",
    "registered rto": "Registered RTO",
    "address": "Address",
    "city name": "City Name",
    "phone": "Phone",
    "website": "Website",
}


def normalize_label(text):
    if not text:
        return None
    cleaned = re.sub(r'\s+', ' ', str(text)).strip().lower()
    cleaned = cleaned.replace('’', "'")
    return LABEL_ALIASES.get(cleaned, cleaned.title())


def clean_value(value):
    if not value:
        return value
    cleaned = re.sub(r'\s+', ' ', str(value)).strip()
    cleaned = re.sub(r'\s+(Vehicle RC Check|RTO Information Portal|RenewRegistration|Check & Pay Challan|Insurance Already Expired|PUC Already Expired)$', '', cleaned, flags=re.I)
    return cleaned


def get_vahan_result_url(rc_clean, headers):
    search_url = "https://vahanx.in/rc-search"
    try:
        landing = requests.get(search_url, headers=headers, timeout=12)
        landing.raise_for_status()
        match = re.search(r'window\.VX_ST\s*=\s*\{.*?rc\s*:\s*"([^"]+)"', landing.text, re.S)
        token = match.group(1) if match else None
    except requests.exceptions.RequestException:
        token = None

    result_url = f"{search_url}/{rc_clean}"
    if token:
        result_url = f"{result_url}?t={quote(token)}"
    return result_url


def get_vehicleinfo_result_url(rc_clean):
    return f"https://vehicleinfo.app/rc-details/{rc_clean}?rc_no={rc_clean}"


def fetch_vahan_result_html(rc_clean):
    if sync_playwright is None:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                ],
            )
            context = browser.new_context(
                viewport={"width": 1440, "height": 1200},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            page.goto('https://vahanx.in/rc-search', wait_until='domcontentloaded', timeout=30000)
            page.fill('#search-input', rc_clean)
            search_button = page.locator('button:has-text("Search")')
            if search_button.count():
                search_button.click()
            else:
                page.locator('form#search-form').evaluate("form => form.requestSubmit()")
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def fetch_vehicleinfo_browser_html(rc_clean):
    if sync_playwright is None:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
            page.goto(
                get_vehicleinfo_result_url(rc_clean),
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def fetch_vehicleinfo_html(rc_clean, headers):
    try:
        response = requests.get(
            get_vehicleinfo_result_url(rc_clean),
            headers=headers,
            timeout=12,
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return None


def extract_result_details(soup):
    data = {}
    seen = set()
    allowed = {
        "owner name", "father's name", "father name", "owner serial no", "code",
        "model name", "modal name", "maker model",
        "vehicle class", "fuel type", "fuel norms", "registration date",
        "insurance company", "insurance no", "insurance expiry", "insurance upto",
        "fitness upto", "tax upto", "puc no", "puc upto", "puc expiry in",
        "financier name", "registered rto", "address", "city name", "phone",
        "website", "insurance expiry in"
    }

    label_elements = soup.select("span, .label")
    for tag in label_elements:
        raw_label = tag.get_text(" ", strip=True)
        label = normalize_label(raw_label)
        if not label or label in seen:
            continue

        normalized_key = re.sub(r'\s+', ' ', str(label)).strip().lower().replace("'", "")
        if normalized_key not in allowed and raw_label.strip().lower() not in allowed:
            continue

        parent = tag.find_parent("div")
        value = None
        if parent:
            for p in parent.select("p"):
                text = p.get_text(" ", strip=True)
                if text and text.lower() != raw_label.strip().lower():
                    value = text
                    break

        if value is None:
            next_p = tag.find_next("p")
            if next_p:
                value = next_p.get_text(" ", strip=True)

        if value:
            cleaned_value = clean_value(value)
            if cleaned_value:
                data[label] = cleaned_value
                seen.add(label)

    key_aliases = {
        "Code": "Owner Serial No",
        "Model Name": "Model Name",
        "Modal Name": "Model Name",
        "Registered RTO": "Registered RTO",
        "Insurance Expiry In": "Insurance Expiry",
        "PUC Expiry In": "PUC Upto",
    }
    for label, canonical in key_aliases.items():
        if label in data and canonical not in data:
            data[canonical] = data[label]
            del data[label]

    return data


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "service": "Vehicle RC Intelligence Flask API",
        "developer": DEVELOPER_INFO,
        "endpoints": {
            "query_rc_param": "/api/vehicle?rc=BR03H5690",
            "query_rc_path": "/lookup/BR03H5690"
        }
    })

@app.route('/api/vehicle', methods=['GET'])
@app.route('/lookup/<path:rc_number>', methods=['GET'])
def vehicle_lookup(rc_number=None):
    if not rc_number:
        rc_number = request.args.get('rc') or request.args.get('number') or request.args.get('code')
    
    if not rc_number:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": "Parameter 'rc' is required. Example: /api/vehicle?rc=BR03H5690"
        }), 400

    # Clean and uppercase RC number
    rc_clean = re.sub(r'[^A-Za-z0-9]', '', str(rc_number)).upper()
    
    if len(rc_clean) < 4:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": "Invalid RC registration number format."
        }), 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    vehicleinfo_html = fetch_vehicleinfo_html(rc_clean, headers)
    parsed = (
        extract_result_details(BeautifulSoup(vehicleinfo_html, "html.parser"))
        if vehicleinfo_html
        else {}
    )

    if not parsed:
        vehicleinfo_browser_html = fetch_vehicleinfo_browser_html(rc_clean)
        if vehicleinfo_browser_html:
            parsed = extract_result_details(
                BeautifulSoup(vehicleinfo_browser_html, "html.parser")
            )

    if not parsed:
        target_url = get_vahan_result_url(rc_clean, headers)
        try:
            res = requests.get(target_url, headers=headers, timeout=12)
            res.raise_for_status()
            parsed = extract_result_details(BeautifulSoup(res.text, "html.parser"))
        except requests.exceptions.RequestException:
            parsed = {}

    if not parsed:
        browser_html = fetch_vahan_result_html(rc_clean)
        if browser_html:
            parsed = extract_result_details(BeautifulSoup(browser_html, "html.parser"))

    if not parsed:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": f"No vehicle details found or upstream service unavailable for RC: {rc_clean}"
        }), 502

    data = {}
    for key in DESIRED_ORDER:
        if key in parsed:
            data[key] = parsed[key]

    if not data and parsed:
        data = parsed

    if data:
        return jsonify({
            "status": "success",
            "developer": DEVELOPER_INFO,
            "rc": rc_clean,
            "data": data
        }), 200
    else:
        return jsonify({
            "status": "error",
            "developer": DEVELOPER_INFO,
            "message": f"No vehicle details found or invalid RC number: {rc_clean}"
        }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
