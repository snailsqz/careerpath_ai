import requests
import pandas as pd
import time
import random
from langdetect import detect, LangDetectException
import os
from dotenv import load_dotenv 

load_dotenv()

def fetch_courses(limit_per_page=100, max_pages=5, start_page_num=1):
    base_url = os.getenv("URL_COURSERA_API")
    
    fields = "name,description,slug,level,primaryLanguages,workload,domainTypes,certificates,photoUrl"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    all_courses = []
    start = (start_page_num - 1) * limit_per_page
    
    current_page = start_page_num
    pages_fetched = 0
    
    print(f"Starting fetch process (Stealth Mode)...")
    
    while pages_fetched < max_pages:
        params = {
            "start": start,
            "limit": limit_per_page,
            "fields": fields
        }
        
        try:
            # [แก้ไข] ใส่ headers เข้าไปใน request
            response = requests.get(base_url, params=params, headers=headers)
            
            # [เพิ่ม] ดักจับ Error 429 (Rate Limit)
            if response.status_code == 429:
                print("Rate limit hit. Pausing for 60 seconds...")
                time.sleep(60)
                continue

            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                if not elements:
                    print("No more data available.")
                    break
                
                filtered_count = 0
                for item in elements:
                    languages = item.get("primaryLanguages", [])
                    if 'en' not in languages:
                        continue
                    
                    title = item.get("name", "")
                    description = item.get("description", "")
                    text_to_check = f"{title} {description}"[:500] 
                    
                    try:
                        detected_lang = detect(text_to_check)
                        
                        # Allow only English (en) and Thai (th)
                        # This removes French, Spanish, etc. even if metadata says 'en'
                        if detected_lang not in ['en', 'th']:
                            continue
                            
                    except LangDetectException:
                        pass

                    domains = item.get("domainTypes", [])
                    if domains:
                        category = domains[0].get("subdomainId") or domains[0].get("domainId") or "General"
                    else:
                        category = "General"

                    certs = item.get("certificates", [])
                    cert_str = ", ".join(certs) if certs else "Standard Course Certificate"

                    course_info = {
                        "id": item.get("id"),
                        "title": item.get("name"),
                        "description": item.get("description"),
                        "level": item.get("level", "Not Specified"),
                        "duration": item.get("workload", "Self-paced"),
                        "category": category,
                        "certificate_type": cert_str,
                        "url": f"https://www.coursera.org/learn/{item.get('slug')}",
                        "image_url": item.get("photoUrl")
                    }
                    all_courses.append(course_info)
                    filtered_count += 1
                
                print(f"Page {current_page}: Fetched {len(elements)} items (Kept {filtered_count}).")
                
                if 'paging' in data and 'next' in data['paging']:
                    start = int(data['paging']['next'])
                    current_page += 1
                    pages_fetched += 1
                else:
                    print("End of catalog reached.")
                    break
                
                # [แก้ไข] สุ่มเวลาพัก 2.0 - 5.0 วินาที (จากเดิม 1 วิ)
                sleep_time = random.uniform(2.0, 5.0)
                time.sleep(sleep_time)
                
            else:
                print(f"Error: {response.status_code}")
                break
                
        except Exception as e:
            print(f"Exception: {e}")
            break

    return all_courses

def save_to_csv(courses, filename="coursera_dataset.csv"):
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
    courses = fetch_courses(max_pages=40)
    save_to_csv(courses)