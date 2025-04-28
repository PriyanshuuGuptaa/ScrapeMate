import urllib.robotparser
import time
import csv
from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import requests

# HEADERS (for robots.txt check)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}

# Function to get user inputs
def get_user_inputs():
    print("\n🚀 Welcome to the Selenium Scraper CLI\n")
    
    site_url = input("Enter the website URL: ").strip()

    name_class = input("Enter the NAME class (example: 'g1qv1ctd atm_u80d3j_1li1fea'): ").strip()
    price_class = input("Enter the PRICE class: ").strip()
    rating_class = input("Enter the RATING class (or type 'NA' if not available): ").strip()

    next_page_selector = input("Enter the NEXT page button selector (example: a[aria-label='Next']): ").strip()

    return {
        "site_url": site_url,
        "name_class": name_class,
        "price_class": price_class,
        "rating_class": rating_class,
        "next_page_selector": next_page_selector
    }

# Function to check robots.txt for scraping permissions
def check_robots(url):
    base_url = "/".join(url.split("/")[:3])
    robot_url = base_url + "/robots.txt"
    
    print(f"\n🔍 Checking robots.txt at: {robot_url}")

    try:
        response = requests.get(robot_url, headers=HEADERS, timeout=10)
        if response.status_code == 404:
            print("No robots.txt found. Proceed with caution!")
            return True
        
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(response.text.splitlines())

        if rp.can_fetch("*", url):
            print("✅ Scraping allowed by robots.txt.\n")
            return True
        else:
            print("❌ Scraping NOT allowed by robots.txt. Exiting.\n")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error fetching robots.txt: {e}")
        return False

# Function to setup selenium driver
def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to extract data using selenium
def extract_data(driver, name_class, price_class, rating_class, next_page_selector):
    time.sleep(5)  
    data = []

    # Convert class names to CSS selectors
    name_selector = "." + ".".join(name_class.split())
    price_selector = "." + ".".join(price_class.split())
    rating_selector = None
    if rating_class.lower() != "na":
        rating_selector = "." + ".".join(rating_class.split())

    while True:
        time.sleep(2)
        name_elements = driver.find_elements(By.CSS_SELECTOR, name_selector)
        price_elements = driver.find_elements(By.CSS_SELECTOR, price_selector)
        rating_elements = driver.find_elements(By.CSS_SELECTOR, rating_selector) if rating_selector else []

        print(f"📦 Found {len(name_elements)} names, {len(price_elements)} prices, {len(rating_elements)} ratings on this page.\n")

        max_len = max(len(name_elements), len(price_elements), len(rating_elements) if rating_selector else 0)

        for i in range(max_len):
            try:
                name = name_elements[i].text.strip() if i < len(name_elements) else "N/A"
            except:
                name = "N/A"

            try:
                price = price_elements[i].text.strip() if i < len(price_elements) else "N/A"
            except:
                price = "N/A"

            try:
                if rating_selector:
                    rating = rating_elements[i].text.strip() if i < len(rating_elements) else "N/A"
                else:
                    rating = "N/A"
            except:
                rating = "N/A"

            data.append([name, price, rating])

        # Try to click next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, next_page_selector)
            if next_button:
                print("➡️ Moving to next page...\n")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(4)
            else:
                print("🚫 No Next button found. Finished scraping.\n")
                break
        except:
            print("🚫 No Next button found. Finished scraping.\n")
            break

    return data

# Function to save data into CSV
def save_to_csv(data, filename="scraped_data.csv"):
    headers = ["Name", "Price", "Rating"]
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)
    print(f"\n✅ Data saved to {filename}\n")

# Main controller function
def main():
    user_inputs = get_user_inputs()

    url = user_inputs["site_url"]
    name_class = user_inputs["name_class"]
    price_class = user_inputs["price_class"]
    rating_class = user_inputs["rating_class"]
    next_page_selector = user_inputs["next_page_selector"]

    if not url.startswith("http"):
        print("Please enter a valid URL that starts with http:// or https://")
        return

    if check_robots(url):
        driver = setup_driver()
        print("🌐 Opening the website...\n")
        driver.get(url)

        data = extract_data(driver, name_class, price_class, rating_class, next_page_selector)
        driver.quit()

        if data:
            print("\n📝 Data Extracted:\n")
            print(tabulate(data, headers=["Name", "Price", "Rating"], tablefmt="pretty"))
            save_to_csv(data)
        else:
            print("❗ No data found.")
    else:
        print("🛑 Scraping not allowed. Stopping program.")

if __name__ == "__main__":
    main()
