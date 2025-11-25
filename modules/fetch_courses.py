import requests
import pandas as pd
import time
import random

def fetch_courses(limit_per_page=100, max_pages=5):
    base_url = "https://api.coursera.org/api/courses.v1"
    
    fields = "name,description,slug,level,primaryLanguages,workload,domainTypes,certificates"
    
    # [เพิ่ม] Headers เพื่อปลอมตัวเป็น Browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    all_courses = []
    start = 0
    page_count = 0
    
    print(f"Starting fetch process (Stealth Mode)...")
    
    while page_count < max_pages:
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
                        "url": f"https://www.coursera.org/learn/{item.get('slug')}"
                    }
                    all_courses.append(course_info)
                    filtered_count += 1
                
                print(f"Page {page_count + 1}: Kept {filtered_count} courses.")
                
                if 'paging' in data and 'next' in data['paging']:
                    start = int(data['paging']['next'])
                    page_count += 1
                else:
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
        print("No data to save.")
        return

    df = pd.DataFrame(courses)
    df = df.dropna(subset=['description']) 
    
    if 'category' in df.columns:
        df['category'] = df['category'].str.replace('-', ' ').str.title()

    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} courses to {filename}")

if __name__ == "__main__":
    courses = fetch_courses(max_pages=50)
    save_to_csv(courses)