# [เปลี่ยน] จาก import requests เป็นอันนี้
from curl_cffi import requests 
import pandas as pd
import time
import random
import re
import json
import os

def remove_html_tags(text):
    if not text: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', str(text)).strip()

def fetch_futureskill(limit_pages=5):
    base_url = "https://futureskill.co/fs-content-api/courses/all-course-and-learning-path"
    
    # Headers ให้ใส่เหมือน Browser จริง
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://futureskill.co",
        "Referer": "https://futureskill.co/"
    }

    all_courses = []
    page = 1
    limit_per_req = 10
    
    print(f"Starting fetch FutureSkill (Impersonating Chrome)...")
    
    while page <= limit_pages:
        params = {
            "sort": '{"createdAt":"DESC"}',
            "search": "",
            "page": page,
            "limit": limit_per_req,
            "type": '{"provider":"FUTURESKILL"}'
        }
        
        try:
            # [จุดสำคัญ] เพิ่ม parameter: impersonate="chrome"
            # คำสั่งนี้จะทำให้ Python ของเราแปลงร่างเป็น Chrome 100%
            response = requests.get(
                base_url, 
                params=params, 
                headers=headers, 
                impersonate="chrome" 
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # ... (Logic แกะ JSON เหมือนเดิมเป๊ะ) ...
                items = data.get('data', {}).get('items', {}).get('courses', [])
                
                if not items:
                    print("No more data.")
                    break
                
                for item in items:
                    title = item.get('name', 'Untitled')
                    desc = remove_html_tags(item.get('description', ''))
                    
                    instructor_info = item.get('instructor', {})
                    instructor_name = instructor_info.get('name', 'FutureSkill Instructor') if instructor_info else 'FutureSkill Instructor'

                    cats = item.get('categories', [])
                    category = cats[0].get('name', 'General') if cats else 'General'

                    image_url = item.get('thumbnailUrl', '')
                    
                    # Duration เป็นวินาที หาร 60
                    duration_sec = item.get('duration', 0)
                    duration_str = format_duration(duration_sec)

                    course_id = item.get('id')
                    url = f"https://futureskill.co/course/detail/{course_id}"

                    course_info = {
                        "id": f"fs_{course_id}",
                        "title": title,
                        "description": desc,
                        "instructor": instructor_name,
                        "price": "Subscription",
                        "duration": duration_str,
                        "category": category,
                        "image_url": image_url,
                        "url": url,
                        "source": "FutureSkill"
                    }
                    all_courses.append(course_info)
                
                print(f"   Page {page}: Fetched {len(items)} items.")
                page += 1
                time.sleep(random.uniform(2.0, 4.0)) # พักนานนิดนึง
                
            else:
                print(f"❌ Error: {response.status_code}")
                # ถ้ายัง 403 อีก อาจจะต้องพักยาว
                break
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            break

    return all_courses

def format_duration(milliseconds):
    if not milliseconds: return "Self-paced"
    
    seconds = milliseconds // 1000 
    
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

def save_to_csv(courses, filename="futureskill_dataset.csv"):
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
    courses = fetch_futureskill(limit_pages=100)
    if courses:
        df = pd.DataFrame(courses)
        save_to_csv(courses, "futureskill_dataset.csv")
        print(f"Success! Fetched {len(df)} courses.")