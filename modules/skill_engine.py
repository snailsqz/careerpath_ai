from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

class SkillEngine:
    def __init__(self, google_api_key=None, db_path="./vector_store", model_name="gemini-2.5-flash"):
        # ใช้ Model ตัวใหม่ (Multilingual)
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        
        try:
            current_path = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            current_path = os.getcwd()
            
        project_root = current_path
        while True:
            possible_path = os.path.join(project_root, 'vector_store')
            if os.path.exists(possible_path):
                real_db_path = possible_path
                break
            parent = os.path.dirname(project_root)
            if parent == project_root:
                real_db_path = os.path.join(os.getcwd(), 'vector_store')
                break
            project_root = parent

        if os.path.exists(real_db_path):
            self.db = Chroma(persist_directory=real_db_path, embedding_function=self.embedding_model)
        else:
            self.db = None

        api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API Key not found.")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0
        )

    def _is_thai_content(self, text):
        return bool(re.search(r'[\u0E00-\u0E7F]', str(text)))

    def _extract_and_analyze(self, user_message):
        parser = JsonOutputParser()
        
        prompt = PromptTemplate(
            template="""
            You are an expert Career Advisor AI.
            
            User Message: "{user_message}"
            
            Task:
            1. STRICTLY Detect the language of the user's message (TH or EN).
            2. Extract Current & Target roles.
            3. Analyze the technical skill gap.
            4. Create a "Strategic Action Roadmap".
            5. Identify TOP 5 CRITICAL missing skills.
            
            ### LANGUAGE ENFORCEMENT RULES ###
            - If the user writes in English, ALL output text MUST be in ENGLISH.
            - If the user writes in Thai, ALL output text MUST be in THAI.
            
            ### SEARCH TERM RULES ###
            - 'search_term_en': Must be specific and focused. Use ENGLISH only.
            - 'search_term_th': If user speaks Thai, translate skill to Thai.
            - BAD: "Node.js Python Java"
            - GOOD: "Node.js Backend Development"
            - RULE: If there are multiple choices, PICK THE SINGLE MOST SUITABLE ONE.
            
            ### OUTPUT FORMAT RULES ###
            - 'summary': Write a motivating roadmap.
            - 'missing_skills': Extract exactly 5 skills.
            
            Return ONLY a JSON object:
            {{
                "detected_language": "TH" or "EN",
                "current_role": "...",
                "target_role": "...",
                "summary": "...",
                "missing_skills": [
                    {{ 
                        "display_name": "...", 
                        "search_term_en": "...", 
                        "search_term_th": "..." 
                    }},
                    ...
                ]
            }}
            """,
            input_variables=["user_message"]
        )
        safe_message = user_message.replace("{", "(").replace("}", ")")
        chain = prompt | self.llm | parser
        return chain.invoke({"user_message": safe_message})

    def analyze_and_recommend(self, user_message):
        analysis_result = self._extract_and_analyze(user_message)
        user_lang = analysis_result.get("detected_language", "TH").upper()
        
        missing_skills_data = analysis_result.get("missing_skills", [])[:5]
        recommendations = []
        
        if self.db:
            for item in missing_skills_data:
                term_en = item.get('search_term_en', '')
                term_th = item.get('search_term_th', '')
                display_name = item.get('display_name', term_en)
                
                print(f"[DEBUG] Searching: EN='{term_en}' | TH='{term_th}'")
                
                results = []
                try:
                    # ใช้ similarity_search_with_score (คืนค่า Distance: ยิ่งน้อยยิ่งดี)
                    if term_en:
                        res_en = self.db.similarity_search_with_score(term_en, k=5)
                        results.extend(res_en)
                    
                    if term_th and term_th != term_en:
                        res_th = self.db.similarity_search_with_score(term_th, k=5)
                        results.extend(res_th)
                        
                except Exception as e:
                    print(f"Search Error: {e}")
                    results = []

                unique_results = {}
                for doc, score in results:
                    url = doc.metadata.get("url")
                    # Logic: ถ้าเจอซ้ำ ให้เอาตัวที่ Score ต่ำกว่า (Distance น้อยกว่า = เหมือนกว่า)
                    if url not in unique_results or score < unique_results[url][1]:
                        unique_results[url] = (doc, score)
                
                final_results = [(doc, score) for doc, score in unique_results.values()]

                thai_courses = []
                other_courses = []
                
                for doc, score in final_results:
                    # Threshold Distance: ยิ่งน้อยยิ่งดี
                    # สำหรับ Multilingual Model ค่า L2 Distance อาจจะกว้าง (10-20) หรือแคบ (0-1)
                    # ลองเริ่มที่ 15.0 (ถ้า L2) หรือ 1.0 (ถ้า Cosine)
                    # แนะนำให้รันดูค่าจริงก่อน
                    
                    print(f"   --> Found: [{score:.4f}] {doc.metadata.get('title')}")

                    if score > 15.0: # ปรับเลขนี้ตามหน้างานจริง
                        continue
                    
                    raw_duration = str(doc.metadata.get("duration", ""))
                    if raw_duration.lower() == 'nan' or not raw_duration:
                        display_duration = "Self-paced"
                    else:
                        display_duration = raw_duration
                    
                    course_data = {
                        "title": doc.metadata.get("title"),
                        "url": doc.metadata.get("url"),
                        "level": doc.metadata.get("level"),
                        "category": doc.metadata.get("category", "General"),
                        "duration": display_duration,
                        "image_url": doc.metadata.get("image_url", ""),
                        "source": doc.metadata.get("source", ""),
                        "score": score
                    }

                    source = course_data["source"]
                    title = course_data["title"]
                    
                    if source in ['SkillLane', 'FutureSkill'] or self._is_thai_content(title):
                        thai_courses.append(course_data)
                    else:
                        other_courses.append(course_data)
                
                final_selection = []
                # เรียงจาก น้อยไปมาก (Distance น้อย = ดี)
                thai_courses.sort(key=lambda x: x['score'])
                other_courses.sort(key=lambda x: x['score'])

                if user_lang == 'TH':
                    final_selection.extend(thai_courses)
                    if len(final_selection) < 2:
                        needed = 2 - len(final_selection)
                        final_selection.extend(other_courses[:needed])
                else:
                    final_selection.extend(other_courses)
                    if len(final_selection) < 2:
                        needed = 2 - len(final_selection)
                        final_selection.extend(thai_courses[:needed])

                best_courses = final_selection[:2]

                if not best_courses:
                    encoded_query = term_en.replace(" ", "%20")
                    best_courses = [{
                        "title": f"Search '{display_name}' on Google",
                        "url": f"https://www.google.com/search?q={encoded_query}+course",
                        "level": "External Search",
                        "duration": "-",
                        "score": 0,
                        "image_url": ""
                    }]
                
                recommendations.append({
                    "skill_gap": display_name,
                    "suggested_courses": best_courses
                })

        return {    
            "user_intent": {
                "detected_current_role": analysis_result.get("current_role"),
                "detected_target_role": analysis_result.get("target_role")
            },
            "analysis_summary": analysis_result.get("summary"),
            "recommendations": recommendations
        }

if __name__ == "__main__":
    try:
        engine = SkillEngine()
        user_input = "อยากเรียนการตลาด"
        result = engine.analyze_and_recommend(user_input)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        print(f"Error: {e}")