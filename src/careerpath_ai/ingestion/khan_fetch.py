import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_single_sitemap(url, headers):
    extracted_courses = []
    try:
        # ใช้ requests ธรรมดา เพราะ debug ผ่านแล้ว
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.content)
        # Namespace ของ Sitemap (สำคัญมาก บางทีไม่มี namespace ก็ต้องดัก)
        # เราจะใช้วิธี findall แบบไม่สน namespace เพื่อความชัวร์ (ท่าไม้ตาย)
        
        # ค้นหา tag <loc> ทั้งหมดในไฟล์ (ไม่สน namespace)
        all_locs = [elem.text for elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        if not all_locs:
            # Fallback ถ้า namespace เปลี่ยน
            all_locs = [elem.text for elem in root.findall('.//loc')]

        for loc in all_locs:
            if not loc: continue
            
            # --- Logic กรองคอร์ส ---
            path = loc.replace("https://www.khanacademy.org/", "")
            parts = path.split('/')
            
            # 1. กรองความลึก (เอาเฉพาะหน้าวิชาหลัก)
            if len(parts) > 3: continue
            
            # 2. กรองหน้าทั่วไป
            if any(x in path for x in ['profile', 'login', 'donate', 'about', 'teacher', 'sat', 'test-prep']): continue

            slug = parts[-1]
            if len(slug) < 3: continue
            
            # 3. กรองหลักสูตรเฉพาะทาง (ภาษาอื่น/หลักสูตรท้องถิ่น)
            if any(x in slug for x in ['in-hindi', 'ncert', 'matatag', 'class-', 'grade-']):
                # ข้ามพวก Class 1-10 ของอินเดีย/ปินส์ เพื่อเอาเนื้อหา Global
                continue

            title = slug.replace('-', ' ').title()
            category = parts[0].capitalize() 

            course_info = {
                "id": f"ka_{slug}",
                "title": title,
                "description": f"Learn {title} for free on Khan Academy.",
                "instructor": "Khan Academy",
                "price": "Free",
                "duration": "Self-paced",
                "category": category,
                "image_url": "", 
                "url": loc,
                "source": "Khan Academy"
            }
            extracted_courses.append(course_info)
            
    except Exception:
        return []
        
    return extracted_courses

def fetch_khan_academy(limit_courses=2000, max_workers=20):
    sitemap_index_url = "https://www.khanacademy.org/sitemap.xml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    print(f"🚀 Starting fetch Khan Academy (High Patience Mode)...")
    print(f"💡 Press Ctrl+C to stop safely.")
    
    all_courses = []
    seen_ids = set()
    
    try:
        response = requests.get(sitemap_index_url, headers=headers)
        root = ET.fromstring(response.content)
        
        target_sitemaps = []
        wanted_keywords = ['math', 'science', 'computing', 'economics']
        
        # หา Link ทั้งหมดใน Index
        all_locs = [elem.text for elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        
        for loc in all_locs:
            if any(k in loc for k in wanted_keywords) and ('es-' not in loc and 'pt-' not in loc):
                target_sitemaps.append(loc)
                
        print(f"📋 Found {len(target_sitemaps)} sitemaps to scan.")
        
    except Exception as e:
        print(f"❌ Error getting index: {e}")
        return []

    print(f"⚡ Processing with {max_workers} threads...")
    
    executor = ThreadPoolExecutor(max_workers=max_workers)
    future_to_url = {}
    
    try:
        for url in target_sitemaps:
            future = executor.submit(fetch_single_sitemap, url, headers)
            future_to_url[future] = url
            
        completed_count = 0
        consecutive_empty_scans = 0
        
        for future in as_completed(future_to_url):
            try:
                data = future.result()
                if data:
                    found_new = False
                    for item in data:
                        if item['id'] not in seen_ids:
                            all_courses.append(item)
                            seen_ids.add(item['id'])
                            found_new = True
                    
                    if found_new:
                        consecutive_empty_scans = 0
                        # เจอของแล้ว! ปริ้นบอกหน่อย
                        print(f"   🎉 Found: {data[0]['title']} ({len(data)} items)")
                    else:
                        consecutive_empty_scans += 1
                else:
                    consecutive_empty_scans += 1
                
                # [แก้] เพิ่มความอดทนเป็น 3000
                if consecutive_empty_scans > 3000:
                    print("\n🛑 No new courses found for 3000 sitemaps. Stopping early.")
                    for f in future_to_url: f.cancel()
                    break
                
                completed_count += 1
                if completed_count % 100 == 0:
                    print(f"   Scanning... {completed_count}/{len(target_sitemaps)} (Total Found: {len(all_courses)})")
                
                if len(all_courses) >= limit_courses:
                    print("🛑 Reached limit.")
                    for f in future_to_url: f.cancel()
                    break

            except Exception:
                continue

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted! Saving data...")
        executor.shutdown(wait=False, cancel_futures=True)
        return all_courses

    finally:
        executor.shutdown(wait=False)

    return all_courses

def save_to_csv(courses, filename="khan_dataset.csv"):
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
    start_time = time.time()
    courses = fetch_khan_academy(limit_courses=2000, max_workers=20)
    end_time = time.time()
    save_to_csv(courses, "khan_dataset.csv")
    print(f"\n⏱️  Fetching completed in {end_time - start_time:.2f} seconds.")