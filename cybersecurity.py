import os
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# Output directories
CSV_DIR = os.path.join('assets', 'csv')
IMG_DIR = os.path.join('assets', 'images', 'cs_images')  # Store images in assets/images/cs_images
CSV_PATH = os.path.join(CSV_DIR, 'thehackernews_articles.csv')
BASE_URL = 'https://thehackernews.com/'

# Ensure output directories exist
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def sanitize_filename(title):
    # Remove invalid filename characters
    return re.sub(r'[^\w\-_\. ]', '_', title)[:100]

def download_image(img_url, title):
    if not img_url or img_url.startswith('data:'):
        return ''
    try:
        # Always use .jpg if extension is missing or not an image
        ext = os.path.splitext(urlparse(img_url).path)[-1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'
        filename = sanitize_filename(title) + ext
        img_path = os.path.join(IMG_DIR, filename)
        # Always re-download to ensure image is present and not a broken file
        resp = requests.get(img_url, timeout=15)
        if resp.status_code == 200 and resp.headers.get('content-type', '').startswith('image'):
            with open(img_path, 'wb') as f:
                f.write(resp.content)
            return img_path
        else:
            print(f"Image not downloaded or not an image: {img_url}")
            return ''
    except Exception as e:
        print(f"Failed to download image {img_url}: {e}")
        return ''

def extract_articles(soup):
    articles = []
    # Target the main article division for homepage news
    main_div = soup.find('div', class_='blog-posts clear')
    if not main_div:
        print('Main article division not found!')
        return articles
    # Find all direct children that are article containers (div.body-post.clear or section.body-post.clear.newsfeed.nf1)
    for post in main_div.find_all(['div', 'section'], recursive=False):
        # Only process if it has the correct class
        classes = post.get('class', [])
        if not (('body-post' in classes and 'clear' in classes) or ('body-post' in classes and 'clear' in classes and 'newsfeed' in classes and 'nf1' in classes)):
            continue
        a_tag = post.find('a', class_='story-link')
        if not a_tag:
            continue
        link = a_tag.get('href')
        # Title
        title_tag = post.find('h2', class_='home-title')
        title = title_tag.get_text(strip=True) if title_tag else ''
        # Date
        date_tag = post.find('span', class_='h-datetime')
        date = date_tag.get_text(strip=True) if date_tag else ''
        # Tags
        tags_tag = post.find('span', class_='h-tags')
        tags = tags_tag.get_text(strip=True) if tags_tag else ''
        # Summary
        desc_tag = post.find('div', class_='home-desc')
        summary = desc_tag.get_text(strip=True) if desc_tag else ''
        # Image
        img_tag = post.find('img', class_='home-img-src')
        img_url = img_tag.get('src') if img_tag else ''
        if img_url and not img_url.startswith('http'):
            img_url = urljoin(BASE_URL, img_url)
        img_path = download_image(img_url, title)
        articles.append({
            'title': title,
            'link': link,
            'date': date,
            'tags': tags,
            'summary': summary,
            'image_path': img_path
        })
    return articles

def main():
    print('Scraping The Hacker News homepage...')
    resp = requests.get(BASE_URL, timeout=15)
    if resp.status_code != 200:
        print(f"Failed to fetch {BASE_URL}: {resp.status_code}")
        return
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = extract_articles(soup)
    if not articles:
        print('No articles found.')
        return
    # Write to CSV
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['title', 'link', 'date', 'tags', 'summary', 'image_path'])
        writer.writeheader()
        for art in articles:
            writer.writerow(art)
    print(f"Saved {len(articles)} articles to {CSV_PATH}")

if __name__ == '__main__':
    main()
