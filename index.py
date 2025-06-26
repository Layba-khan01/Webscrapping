import requests
from bs4 import BeautifulSoup
import csv
import os
import re

url = "http://bair.berkeley.edu/blog/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def sanitize_filename(name):
    # Remove invalid filename characters
    return re.sub(r'[^\w\-_\. ]', '_', name)

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

results = []
image_folder = "assets/images"
os.makedirs(image_folder, exist_ok=True)

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
    # Thumbnail image (first <img> in post or from meta tag)
    img_url = None
    img_tag = post.find("img")
    if not img_tag:
        # Try to find meta og:image or twitter:image
        meta_img = post.find_previous("meta", attrs={"property": "og:image"})
        if not meta_img:
            meta_img = post.find_previous("meta", attrs={"name": "twitter:image"})
        if meta_img and meta_img.has_attr("content"):
            img_url = meta_img["content"]
    else:
        img_url = img_tag["src"] if img_tag.has_attr("src") else None
    img_path = ""
    if img_url:
        if not img_url.startswith("http"):
            img_url = f"http://bair.berkeley.edu{img_url}"
        img_name = sanitize_filename(title) + os.path.splitext(img_url.split("?")[0])[1]
        img_path = os.path.join(image_folder, img_name)
        try:
            img_data = requests.get(img_url, headers=headers, timeout=10)
            if img_data.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(img_data.content)
        except Exception as e:
            img_path = ""
    results.append({
        "Title": title,
        "Link": link,
        "Authors": authors_str,
        "Date": date,
        "Summary": summary,
        "Image": img_path if img_path else "No image"
    })

csv_path = "assets/csv/bair_blog_articles.csv"
with open(csv_path, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["Title", "Link", "Authors", "Date", "Summary", "Image"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"Scraped {len(results)} articles and saved to {csv_path}. Images saved to {image_folder}.")
