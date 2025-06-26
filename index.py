import requests
from bs4 import BeautifulSoup
import csv

url = "http://bair.berkeley.edu/blog/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

results = []
# Use CSS selector for more robust selection
post_divs = soup.select("div.measure div.home div.posts div.post")
print(f"Found {len(post_divs)} posts.")
if not post_divs:
    print("No posts found. Printing a snippet of the HTML for debugging:")
    print(soup.prettify()[:2000])
for post in post_divs:
    # Title
    title_tag = post.find("h1", class_="post-title")
    link_tag = title_tag.find("a") if title_tag else None
    title = link_tag.get_text(strip=True) if link_tag else "No title"
    link = link_tag["href"] if link_tag and link_tag.has_attr("href") else "No link"
    if link and not link.startswith("http"):
        link = f"http://bair.berkeley.edu{link}"
    # Authors
    authors = []
    h5_tag = post.find("h5")
    if h5_tag:
        author_spans = h5_tag.find_all("span", class_="post-meta")
        for span in author_spans:
            for a in span.find_all("a"):
                authors.append(a.get_text(strip=True))
        if not authors:
            authors = [span.get_text(strip=True) for span in author_spans]
    authors_str = ", ".join(authors) if authors else "No authors"
    # Date
    date = "No date"
    if h5_tag:
        date_spans = h5_tag.find_all("span", class_="post-meta")
        if len(date_spans) > 1:
            date = date_spans[-1].get_text(strip=True)
    # Summary
    summary_tag = post.find("p", class_="post-summary")
    summary = summary_tag.get_text(strip=True) if summary_tag else "No summary"
    results.append({
        "Title": title,
        "Link": link,
        "Authors": authors_str,
        "Date": date,
        "Summary": summary
    })

csv_path = "assets/csv/bair_blog_articles.csv"
with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["Title", "Link", "Authors", "Date", "Summary"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"Scraped {len(results)} articles and saved to {csv_path}.")
