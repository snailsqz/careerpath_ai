from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import random

def fetch_datacamp_courses(max_limit=1000): # ตั้งเผื่อไว้เยอะๆ
    base_url = "https://www.datacamp.com/courses-all"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    all_courses = []
    page = 1
    total_pages = 1 # ค่าเริ่มต้น เดี๋ยวจะอัปเดตจากข้อมูลจริง
    
    print(f"Starting fetch DataCamp (All Pages)...")
    
    while page <= total_pages:
        # ใส่ param page เข้าไป
        params = {
            "page": page
        }
        
        try:
            print(f"   Scraping Page {page}...", end="")
            
            response = requests.get(base_url, params=params, headers=headers, impersonate="chrome")
            
            if response.status_code != 200:
                print(f" -> Error: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            next_data_tag = soup.find('script', id='__NEXT_DATA__')
            
            if not next_data_tag:
                print(" -> No Data found.")
                break

            json_data = json.loads(next_data_tag.string)
            
            # เจาะหาข้อมูล (ตาม Key ที่คุณให้มาล่าสุด)
            try:
                # เข้าไปที่ props -> pageProps
                props = json_data.get('props', {}).get('pageProps', {})
                
                hits = props.get('hits', [])
                
                # หาจำนวนหน้าทั้งหมด (เพื่อเอามาคุม Loop)
                # ปกติ Algolia จะมี key 'nbPages' หรือคำนวณจาก 'nbHits'
                if 'nbPages' in props:
                    total_pages = props['nbPages']
                
                # ถ้าหา nbPages ไม่เจอ ลองคำนวณเอง
                elif 'nbHits' in props and page == 1:
                    # สมมติหน้าละ 30
                    import math
                    total_pages = math.ceil(props['nbHits'] / 30)
                    print(f" (Total items: {props['nbHits']} -> Est. Pages: {total_pages})")

            except Exception as e:
                print(f" -> Structure Error: {e}")
                break

            if not hits:
                print(" -> No more courses.")
                break

            # วนลูปเก็บข้อมูลในหน้านั้น
            count_in_page = 0
            for item in hits:
                # Logic แกะข้อมูลเดิม
                title_raw = item.get('title')
                if isinstance(title_raw, dict):
                    title = title_raw.get('en-US', 'Untitled')
                else:
                    title = title_raw

                if not title: continue

                desc = item.get('summary') or item.get('excerpt') or title
                
                technology = item.get('technology') or 'Data Science'
                
                duration_val = item.get('duration_hours')
                duration = f"{duration_val} hours" if duration_val else "Self-paced"
                
                # URL & ID
                slug = item.get('slug') or item.get('url')
                if slug and str(slug).startswith('http'):
                    course_url = slug
                else:
                    course_url = f"https://www.datacamp.com{slug}" if slug else "https://www.datacamp.com"
                
                # ID (Algolia ใช้ objectID)
                c_id = item.get('objectID') or item.get('id')

                course_info = {
                    "id": f"dc_{c_id}",
                    "title": title,
                    "description": desc,
                    "instructor": "DataCamp Instructor",
                    "price": "Subscription",
                    "duration": str(duration),
                    "category": technology,
                    "image_url": item.get('image_url') or item.get('cap_image_url'),
                    "url": course_url,
                    "source": "DataCamp"
                }
                all_courses.append(course_info)
                count_in_page += 1
            
            print(f" -> Got {count_in_page} items. (Total: {len(all_courses)})")
            
            # เช็ค limit ที่เราตั้งเอง (เผื่อไม่อยากดึงหมด)
            if len(all_courses) >= max_limit:
                print("Reached user limit.")
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.0)) # พักสักนิด

        except Exception as e:
            print(f"\nCritical Exception: {e}")
            break

    return all_courses

def save_to_csv(courses, filename="datacamp_dataset.csv"):
    if not courses:
        print("No data to save.")
        return

    current_file_path = os.path.abspath(__file__)
    
    modules_dir = os.path.dirname(current_file_path)
    
    project_root = os.path.dirname(modules_dir)
    
    data_dir = os.path.join(project_root, 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created folder: {data_dir}")

    full_path = os.path.join(data_dir, filename)
    
    df = pd.DataFrame(courses)
    df.to_csv(full_path, index=False, encoding='utf-8-sig')
    
    print(f"Saved {len(df)} courses to: {full_path}")

if __name__ == "__main__":
    courses = fetch_datacamp_courses(max_limit=1000)
    if courses:
        df = pd.DataFrame(courses)
        print(f"\nExtracted {len(df)} courses successfully!")
        save_to_csv(courses, "datacamp_dataset.csv")