import urllib.robotparser
import time
import csv
from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}

def get_user_inputs():
    print("\n🚀 Welcome to the Selenium Scraper CLI\n")
    
    site_url = input("Enter the website URL: ").strip()
    name_class = input("Enter the NAME class: ").strip()
    price_class = input("Enter the PRICE class: ").strip()
    rating_class = input("Enter the RATING class (or type 'NA' if not available): ").strip()

    mode = input("Choose navigation method - type 'pagination' or 'load_more': ").strip().lower()
    
    if mode == "pagination":
        nav_selector = input("Enter the NEXT page button selector (example: a[aria-label='Next']): ").strip()
    elif mode == "load_more":
        nav_selector = input("Enter the LOAD MORE button selector (example: button.load-more): ").strip()
    else:
        print("Invalid mode selected. Defaulting to pagination.")
        mode = "pagination"
        nav_selector = input("Enter the NEXT page button selector (example: a[aria-label='Next']): ").strip()

    return {
        "site_url": site_url,
        "name_class": name_class,
        "price_class": price_class,
        "rating_class": rating_class,
        "mode": mode,
        "nav_selector": nav_selector
    }

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

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_data(driver, name_selector, price_selector, rating_selector, nav_selector, mode):
    time.sleep(5)
    data = []

    while True:
        time.sleep(2)
        name_elements = driver.find_elements(By.CSS_SELECTOR, name_selector)
        price_elements = driver.find_elements(By.CSS_SELECTOR, price_selector)
        rating_elements = driver.find_elements(By.CSS_SELECTOR, rating_selector) if rating_selector else []

        print(f"📦 Found {len(name_elements)} names, {len(price_elements)} prices, {len(rating_elements)} ratings")

        max_len = max(len(name_elements), len(price_elements), len(rating_elements))
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
                rating = rating_elements[i].text.strip() if i < len(rating_elements) else "N/A"
            except:
                rating = "N/A"
            data.append([name, price, rating])

        try:
            nav_button = driver.find_element(By.CSS_SELECTOR, nav_selector)
            prev_count = len(name_elements)

            if mode == "pagination":
                print("➡️ Moving to next page...\n")
                driver.execute_script("arguments[0].click();", nav_button)
                time.sleep(4)

            elif mode == "load_more":
                print("⬇️ Clicking Load More...\n")
                driver.execute_script("arguments[0].click();", nav_button)
                for _ in range(10):
                    time.sleep(1)
                    new_count = len(driver.find_elements(By.CSS_SELECTOR, name_selector))
                    if new_count > prev_count:
                        print(f"📥 Loaded {new_count - prev_count} new items.")
                        break
                else:
                    print("⚠️ Timeout: No new items loaded.")
                    break

        except:
            print("🚫 No more navigation possible. Finishing up.")
            break

    return data

def save_to_csv(data, filename="scraped_data.csv"):
    headers = ["Name", "Price", "Rating"]
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)
    print(f"\n✅ Data saved to {filename}\n")

def main():
    inputs = get_user_inputs()

    url = inputs["site_url"]
    name_class = "." + ".".join(inputs["name_class"].split())
    price_class = "." + ".".join(inputs["price_class"].split())
    rating_class = "." + ".".join(inputs["rating_class"].split()) if inputs["rating_class"].lower() != "na" else None
    nav_selector = inputs["nav_selector"]
    mode = inputs["mode"]

    if not url.startswith("http"):
        print("❗ Invalid URL. Please include http:// or https://")
        return

    if check_robots(url):
        driver = setup_driver()
        print("🌐 Opening website...")
        driver.get(url)

        data = extract_data(driver, name_class, price_class, rating_class, nav_selector, mode)
        driver.quit()

        if data:
            print("\n📋 Final Data:\n")
            print(tabulate(data, headers=["Name", "Price", "Rating"], tablefmt="pretty"))
            save_to_csv(data)
        else:
            print("❗ No data extracted.")
    else:
        print("🛑 Scraping not allowed. Exiting.")

if __name__ == "__main__":
    main()
