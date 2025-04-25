import urllib.robotparser
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

def check_robots(url):
    base_url = "/".join(url.split("/")[:3])
    print(base_url)
    robot_url = base_url + "/robots.txt"
    print(robot_url)

    try:
        response = requests.get(robot_url)
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(response.text.splitlines())

        if rp.can_fetch("*",url):
            print("Scrapping allowed by robots.txt")
            return True
        else:
            print("Scrapping not allowed by robots.txt")
            return False
    except requests.exceptions.RequestException as e:
        print("Error with robots.txt")
        return False

def fetching_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print("Error fetching HTML")
        return None

# url = "https://webscraper.io/test-sites/e-commerce/allinone"
# check_robots(url)
# html = fetching_html(url)


def extract_tags(html):
    soup = BeautifulSoup(html,"html.parser")
    all_tags = soup.find_all(True)
    tag_info= []
    for tag in all_tags:
        tag_name = tag.name
        tag_class = " ".join(tag.get("class",[]))
        tag_text = tag.get_text(strip=True)[:100]

        tag_info.append((tag_name,tag_class,tag_text))

    return tag_info
    
# extract_tags(html)

def main():
    url = input("Enter URL to scrape").strip()

    if not url.startswith("http"):
        print("Please enter a valid URL that starts with http or https")
        return
    if check_robots(url):
        html= fetching_html(url)
        if html:
            tags = extract_tags(html)
            if tags:
                print(tabulate(tags,headers=["Tags"],tablefmt="Pretty"))
            else:
                print("No tags to print")
    else :
        print("Can not scrape due to robots.txt restrictions")
main()