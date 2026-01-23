from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
import hashlib
import urllib.parse
import os
from dotenv import load_dotenv 

load_dotenv()

def clean_text_from_dict(data):
    """Extract text from dictionary like {'en-US': '...'}"""
    if isinstance(data, dict):
        return data.get('en-US') or data.get('en') or list(data.values())[0]
    return str(data) if data else ""

def fetch_datacamp_courses(max_pages=20):
    base_url = os.getenv("URL_DATACAMP_API")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    all_courses = []
    page = 1
    
    print(f"Starting fetch DataCamp (Robust Parser)...")
    
    while page <= max_pages:
        # Use URL for pagination
        if page == 1:
            target_url = base_url
        else:
            target_url = f"{base_url}/page/{page}"
            
        try:
            print(f"   Scraping Page {page}...", end="")
            
            response = requests.get(target_url, headers=headers, impersonate="chrome")
            
            if response.status_code == 404:
                print(" -> End of pages.")
                break
            
            if response.status_code != 200:
                print(f" -> Error: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            next_data_tag = soup.find('script', id='__NEXT_DATA__')
            
            if not next_data_tag:
                print(" -> No Data found.")
                break

            json_data = json.loads(next_data_tag.string)
            
            # Drill down to find hits
            items = []
            try:
                props = json_data.get('props', {}).get('pageProps', {})
                # Path 1: Search results
                items = props.get('hits', [])
                # Path 2: Content list
                if not items:
                    items = props.get('content', {}).get('courses', [])
                # Path 3: Algolia results
                if not items:
                    items = props.get('initialState', {}).get('hits', [])
            except:
                pass

            if not items:
                print(" -> No items found on this page.")
                break

            count_new = 0
            for item in items:
                # 1. Clean Title/Desc
                title = clean_text_from_dict(item.get('title'))
                if not title: continue

                desc = clean_text_from_dict(item.get('excerpt') or item.get('description') or item.get('summary') or title)
                
                # 2. Fix ID (Hash if missing)
                raw_id = item.get('objectID') or item.get('id')
                if raw_id:
                    c_id = str(raw_id)
                else:
                    # Generate ID from Title
                    c_id = hashlib.md5(title.encode()).hexdigest()[:10]

                # 3. Fix URL (Fallback to search if no slug)
                raw_slug = item.get('slug') or item.get('url') or item.get('relative_url')
                
                if raw_slug:            
                    slug_str = str(raw_slug).strip().rstrip('/')
                    clean_slug = slug_str.split('/')[-1] # ตัดเอาแค่ตัวหลังสุด
                    course_url = f"https://www.datacamp.com/courses/{clean_slug}"
                else:
                    # Fallback ถ้าไม่มีข้อมูลจริงๆ
                    encoded_title = urllib.parse.quote(title)
                    course_url = f"https://www.datacamp.com/search?q={encoded_title}"

                # Duration & Tech
                duration_val = item.get('duration_hours')
                duration = f"{duration_val} hours" if duration_val else "Self-paced"
                technology = item.get('technology') or 'Data Science'
                
                # Image
                image_url = (
                    item.get('image_url') or 
                    item.get('cap_image_url') or 
                    item.get('thumbnail_url') or
                    ""
                )

                course_info = {
                    "id": f"dc_{c_id}",
                    "title": title,
                    "description": desc,
                    "instructor": "DataCamp Instructor",
                    "price": "Subscription",
                    "duration": str(duration),
                    "category": technology,
                    "image_url": image_url,
                    "url": course_url,
                    "source": "DataCamp"
                }
                all_courses.append(course_info)
                count_new += 1
            
            print(f" -> Got {count_new} items. (Total: {len(all_courses)})")
            
            page += 1
            time.sleep(random.uniform(1.0, 2.0))
            
        except Exception as e:
            print(f"\nException: {e}")
            break

    return all_courses

def save_to_csv(courses, filename="datacamp_dataset.csv"):
    if not courses:
        print("⚠️ No data to save.")
        return

    current_file_path = os.path.abspath(__file__)
    
    modules_dir = os.path.dirname(current_file_path)
    
    project_root = os.path.dirname(modules_dir)
    
    data_dir = os.path.join(project_root, 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created folder: {data_dir}")

    # 5. รวมร่าง Path กับชื่อไฟล์
    full_path = os.path.join(data_dir, filename)
    
    # 6. บันทึกไฟล์
    df = pd.DataFrame(courses)
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    
    print(f"Saved {len(df)} courses to: {full_path}")

if __name__ == "__main__":
    # Fetch 10 pages
    courses = fetch_datacamp_courses(max_pages=25)
    if courses:
        df = pd.DataFrame(courses)
        save_to_csv(courses, filename="datacamp_dataset.csv")
        print(f"\nCompleted! Saved {len(df)} courses.")