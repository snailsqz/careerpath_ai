from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
import json

load_dotenv()

class SkillEngine:
    def __init__(self, google_api_key=None, db_path="./vector_store", model_name="gemini-2.5-flash"):
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
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

    def _extract_and_analyze(self, user_message):
        parser = JsonOutputParser()
        
        prompt = PromptTemplate(
            template="""
            You are an expert Career Advisor AI.
            
            User Message: "{user_message}"
            
            Task:
            1. STRICTLY Detect the language of the user's message.
            2. Extract Current & Target roles.
            3. Analyze the technical skill gap.
            4. Create a "Strategic Action Roadmap".
            5. Identify TOP 5 CRITICAL missing skills.
            
            ### LANGUAGE ENFORCEMENT RULES (CRITICAL) ###
            - If the user writes in English, ALL output text MUST be in ENGLISH.
            - If the user writes in Thai, ALL output text MUST be in THAI.
            - DO NOT output other languages.
            
            ### SEARCH TERM RULES (CRITICAL) ###
            - 'search_term_en': Must be specific and focused. Use ENGLISH only.
            - BAD: "Node.js Python Java" (Do NOT list alternatives)
            - BAD: "Server-side (Node.js)" (No brackets)
            - BAD: "Linear Algebra Statistics Calculus" (Do NOT list multiple subjects)
            - GOOD: "Mathematics for Machine Learning" (Use an Umbrella term)
            - GOOD: "Node.js Backend Development" (Pick ONE best tool)
            - RULE: If there are multiple choices, PICK THE SINGLE MOST SUITABLE ONE based on user's background.
            - RULE: If the skill involves multiple topics (e.g. Math + Stats), use a broader category name like "Mathematics for AI".
            
            ### OUTPUT FORMAT RULES ###
            - 'summary': Write a motivating roadmap in the DETECTED LANGUAGE.
               Use bullet points for phases:
               - Phase 1: Foundation
               - Phase 2: Core Skills
               - Phase 3: Advanced/Specialization
            
            - 'missing_skills': Extract exactly 5 skills. 
               - 'display_name': In DETECTED LANGUAGE.
               - 'search_term_en': Max 3-4 keywords per skill.
            
            Return ONLY a JSON object:
            {{
                "current_role": "...",
                "target_role": "...",
                "summary": "...",
                "missing_skills": [
                    {{ "display_name": "...", "search_term_en": "..." }},
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
        
        missing_skills_data = analysis_result.get("missing_skills", [])[:5]
        
        recommendations = []
        if self.db:
            for item in missing_skills_data:
                search_query = item.get('search_term_en', '')
                display_name = item.get('display_name', search_query)
                print(f"[DEBUG] Search Term: {search_query}")

                valid_courses = []
                best_courses = [] 
                
                try:
                    results = self.db.similarity_search_with_relevance_scores(search_query, k=3)
                except Exception as e:
                    print(f"Search Error for {search_query}: {e}")
                    results = []

                for doc, score in results:
                    print(f"   --> Found: [{score:.4f}] {doc.metadata.get('title')}")
                    if score < 0.3:
                        continue
                    
                    raw_duration = str(doc.metadata.get("duration", ""))
                    
                    if raw_duration.lower() == 'nan' or not raw_duration:
                        display_duration = "Self-paced"
                    else:
                        display_duration = raw_duration

                    valid_courses.append({
                        "title": doc.metadata.get("title"),
                        "url": doc.metadata.get("url"),
                        "level": doc.metadata.get("level"),
                        "duration": display_duration, # ใช้ค่าใหม่ที่แก้แล้ว
                        "score": score
                    })
                
                if valid_courses:
                    best_courses = sorted(valid_courses, key=lambda x: x['score'], reverse=True)[:2]
                else:
                    # [เพิ่มตรงนี้] ถ้าหาไม่เจอเลย ให้สร้างลิงก์ค้นหาอัตโนมัติ
                    encoded_query = search_query.replace(" ", "%20")
                    best_courses = [{
                        "title": f"Search '{display_name}' on Coursera",
                        "url": f"https://www.coursera.org/search?query={encoded_query}",
                        "level": "External Search",
                        "duration": "-",
                        "score": 0
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
        
        user_input = "ผมเป็น ai engineer อยากไปเป็น project manager ต้องทำยังไง"
        
        print(f"User asking: {user_input}\nProcessing...")
        result = engine.analyze_and_recommend(user_input)
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(f"Error: {e}")