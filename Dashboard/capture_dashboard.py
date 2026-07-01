import os
import subprocess
import time
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from PIL import Image

# Output directory for screenshots
output_dir = r"d:\BlueStock.in\Dashboard"
os.makedirs(output_dir, exist_ok=True)

# 1. Start Streamlit Server in background
print("Starting Streamlit server...")
streamlit_proc = subprocess.Popen(
    ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
    cwd=output_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# 2. Wait for Streamlit server to start
server_ready = False
url = "http://localhost:8501"
print("Waiting for server to become responsive...")
for i in range(20):
    try:
        response = urllib.request.urlopen(url, timeout=2)
        if response.status == 200:
            server_ready = True
            print("Streamlit server is up and running!")
            break
    except Exception:
        time.sleep(1)

if not server_ready:
    print("Error: Streamlit server failed to start in time.")
    streamlit_proc.terminate()
    exit(1)

# Give a little extra buffer time
time.sleep(2)

# 3. Setup Selenium WebDriver
print("Setting up Headless Chrome via Selenium...")
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
        'width': 1920,
        'height': 1080,
        'deviceScaleFactor': 1,
        'mobile': False
    })
except Exception as e:
    print(f"Error initializing Chrome WebDriver: {e}")
    streamlit_proc.terminate()
    exit(1)

# List to keep track of captured screenshot paths
screenshot_paths = []

# Page filenames
page_names = [
    "page_1_industry_overview.png",
    "page_2_fund_performance.png",
    "page_3_investor_analytics.png",
    "page_4_sip_market_trends.png"
]

# 4. Capture Screenshots of all 4 Pages
print("Starting dashboard pages capture...")
for idx in range(1, 5):
    page_url = f"http://localhost:8501/?page={idx}"
    filename = page_names[idx - 1]
    filepath = os.path.join(output_dir, filename)
    
    print(f"Navigating to Page {idx}: {page_url}...")
    driver.get(page_url)
    
    # Wait for the charts, animations and data to load completely
    print(f"Waiting 6 seconds for page {idx} components to render...")
    time.sleep(6)
    
    print(f"Capturing screenshot: {filepath}...")
    driver.save_screenshot(filepath)
    screenshot_paths.append(filepath)

# 5. Close Selenium
print("Closing Selenium browser...")
driver.quit()

# 6. Stop Streamlit Server
print("Stopping Streamlit server...")
streamlit_proc.terminate()
try:
    streamlit_proc.wait(timeout=5)
except subprocess.TimeoutExpired:
    streamlit_proc.kill()
print("Streamlit server stopped.")

# 7. Compile Screenshots into a Multi-page PDF
pdf_path = os.path.join(output_dir, "Dashboard.pdf")
print(f"Compiling screenshots into PDF: {pdf_path}...")

try:
    # Use exact screenshot dimensions (1920x1080) for the PDF pages
    c = canvas.Canvas(pdf_path, pagesize=(1920, 1080))
    for path in screenshot_paths:
        if os.path.exists(path):
            c.drawImage(path, 0, 0, 1920, 1080)
            c.showPage()
    c.save()
    print(f"Successfully generated {pdf_path}!")
except Exception as e:
    print(f"Error compiling PDF: {e}")

print("\n--- Dashboard Capture and PDF Compilation Completed! ---")
