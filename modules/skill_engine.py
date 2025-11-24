from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv

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
            1. Detect the language of the user's message.
            2. Extract CURRENT role/skills. (Default: 'General Beginner')
            3. Extract TARGET role/goal.
            4. Analyze the technical skill gap.
            5. Identify TOP 3 CRITICAL missing skills.
            
            IMPORTANT RULES:
            - 'display_name': Must be in the USER'S language (Thai or English).
            - 'search_term_en': Must ALWAYS be in English (for database search).
            - 'summary': Must be in the USER'S language.
            
            Return ONLY a JSON object:
            {{
                "current_role": "...",
                "target_role": "...",
                "summary": "...",
                "missing_skills": [
                    {{
                        "display_name": "Skill name in user language (e.g. การเขียนโปรแกรม)",
                        "search_term_en": "Keywords in English (e.g. Python Programming)"
                    }},
                    {{
                        "display_name": "...",
                        "search_term_en": "..."
                    }}
                ]
            }}
            """,
            input_variables=["user_message"]
        )

        chain = prompt | self.llm | parser
        return chain.invoke({"user_message": user_message})

    def analyze_and_recommend(self, user_message):
        analysis_result = self._extract_and_analyze(user_message)
        
        missing_skills_data = analysis_result.get("missing_skills", [])[:3]
        
        recommendations = []
        if self.db:
            for item in missing_skills_data:
                search_query = item.get('search_term_en', '')
                display_name = item.get('display_name', search_query)
                print(f"[DEBUG] Search Term: {search_query}")
                # 1. ล้างค่าตัวแปร list ก่อนเริ่มค้นหาใหม่ทุกครั้ง
                valid_courses = []
                best_courses = [] 
                
                try:
                    results = self.db.similarity_search_with_relevance_scores(search_query, k=5)
                except Exception as e:
                    print(f"Search Error for {search_query}: {e}")
                    results = []

                # 3. กรองคะแนน
                for doc, score in results:
                    if score < 0.35:
                        continue
                    
                    valid_courses.append({
                        "title": doc.metadata.get("title"),
                        "url": doc.metadata.get("url"),
                        "level": doc.metadata.get("level"),
                        "duration": doc.metadata.get("duration"),
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
        
        # จำลอง Chat Input
        user_input = "ผมเป็น ai engineer อยากไปเป็น project manager ต้องทำยังไง"
        
        print(f"User asking: {user_input}\nProcessing...")
        result = engine.analyze_and_recommend(user_input)
        
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(f"Error: {e}")