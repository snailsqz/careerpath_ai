import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import random

def fetch_khan_academy():
    # URL ของ Sitemap หลักที่เก็บรายชื่อวิชา (Topics)
    # Khan แยก Sitemap ไว้หลายไฟล์ เราจะเจาะไปที่ตัวหลัก
    sitemap_url = "https://www.khanacademy.org/sitemap.xml"
    
    print(f"🚀 Starting fetch Khan Academy (Sitemap Strategy)...")
    
    all_courses = []
    
    try:
        # 1. ดึง Sitemap แม่
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(sitemap_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error fetching sitemap: {response.status_code}")
            return []

        # 2. หา Sitemap ย่อยที่เป็นภาษาอังกฤษ (en)
        # XML ของ Khan จะมี <loc>https://.../sitemap-en.xml</loc>
        root = ET.fromstring(response.content)
        target_sitemap = None
        
        # Namespace ของ Sitemap XML
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for sitemap in root.findall('sm:sitemap', ns):
            loc = sitemap.find('sm:loc', ns).text
            # เราหาไฟล์ที่ชื่อเกี่ยวกับ topics หรือ content ภาษาอังกฤษ
            # ปกติจะเป็น sitemap-en-topic.xml หรือคล้ายๆ กัน
            if 'en' in loc and 'topic' in loc: 
                target_sitemap = loc
                break
        
        # Fallback: ถ้าหาไม่เจอ ให้ลอง URL มาตรฐาน
        if not target_sitemap:
            target_sitemap = "https://www.khanacademy.org/sitemap-en-topic.xml"

        print(f"   📂 Reading Sub-Sitemap: {target_sitemap}")
        
        # 3. ดึงข้อมูลจาก Sitemap ย่อย
        resp_sub = requests.get(target_sitemap, headers=headers)
        if resp_sub.status_code != 200:
            print("❌ Failed to read sub-sitemap.")
            return []

        root_sub = ET.fromstring(resp_sub.content)
        urls = root_sub.findall('sm:url', ns)
        
        print(f"   🔍 Found {len(urls)} links. Filtering courses...")

        for url_tag in urls:
            loc = url_tag.find('sm:loc', ns).text
            
            # --- LOGIC กรองคอร์ส (สำคัญ) ---
            # URL ของ Khan จะเป็น: https://www.khanacademy.org/math/algebra
            # เราต้องการระดับ Course ซึ่งมักจะมี Slash (/) ประมาณ 4-5 อัน
            
            parts = loc.replace("https://www.khanacademy.org/", "").split('/')
            
            # กรองเอาเฉพาะหมวดหลักๆ
            valid_domains = ['math', 'science', 'computing', 'economics-finance-domain']
            if parts[0] not in valid_domains:
                continue
                
            # กรองความลึก: 
            # /math (Domain) -> ไม่เอา
            # /math/algebra (Subject/Course) -> เอา ✅
            # /math/algebra/x2f... (Lesson) -> ไม่เอา (ลึกไป)
            
            if len(parts) == 2: # เอาเฉพาะระดับ Subject
                
                # สร้างชื่อคอร์สจาก URL (เพราะ Sitemap ไม่มี Title)
                # math/algebra-basics -> Algebra Basics
                raw_title = parts[1].replace('-', ' ').title()
                
                # สร้าง ID
                c_id = f"ka_{parts[1]}"
                
                course_info = {
                    "id": c_id,
                    "title": raw_title,
                    "description": f"Learn {raw_title} for free on Khan Academy.",
                    "instructor": "Khan Academy",
                    "price": "Free",
                    "duration": "Self-paced",
                    "category": parts[0].capitalize(), # เช่น Math
                    "image_url": "", 
                    "url": loc,
                    "source": "Khan Academy"
                }
                all_courses.append(course_info)

    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

    return all_courses

if __name__ == "__main__":
    courses = fetch_khan_academy()
    if courses:
        df = pd.DataFrame(courses)
        # ลบตัวซ้ำเผื่อมี
        df = df.drop_duplicates(subset=['url'])
        df.to_csv("khan_dataset.csv", index=False, encoding='utf-8-sig')
        print(f"\n✅ Completed! Extracted {len(df)} courses.")