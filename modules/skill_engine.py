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

    def analyze_and_recommend(self, user_message):
        analysis_result = self._extract_and_analyze(user_message)
        
        missing_skills = analysis_result.get("missing_skills", [])[:3]
        
        recommendations = []
        if self.db:
            for skill in missing_skills:
                courses = self.db.similarity_search(skill, k=1)
                
                skill_courses = []
                for doc in courses:
                    skill_courses.append({
                        "title": doc.metadata.get("title"),
                        "url": doc.metadata.get("url"),
                        "level": doc.metadata.get("level"),
                        "duration": doc.metadata.get("duration")
                    })
                
                recommendations.append({
                    "skill_gap": skill,
                    "suggested_courses": skill_courses
                })

        return {
            "user_intent": {
                "detected_current_role": analysis_result.get("current_role"),
                "detected_target_role": analysis_result.get("target_role")
            },
            "analysis_summary": analysis_result.get("summary"),
            "recommendations": recommendations
        }

    def _extract_and_analyze(self, user_message):
        parser = JsonOutputParser()
        
        # แก้ Prompt ให้ทำหน้าที่ Extract + Analyze
        prompt = PromptTemplate(
            template="""
            You are an expert Career Advisor AI.
            
            User Message: "{user_message}"
            
            Task:
            1. Detect the language of the user's message (Thai or English).
            2. Extract the user's CURRENT role/skills. (If not specified, assume 'General Beginner')
            3. Extract the TARGET role/goal.
            4. Analyze the technical skill gap between Current and Target.
            5. Identify the TOP 3 MOST CRITICAL missing skills.
            
            IMPORTANT LANGUAGE RULES:
            - If the user inputs in Thai, ALL VALUES in the JSON output MUST be in Thai.
            - If the user inputs in English, use English.
            - The JSON KEYS (e.g., "summary", "missing_skills") must ALWAYS be in English.
            
            Return ONLY a JSON object with this structure:
            {{
                "current_role": "extracted current role (in user's language)",
                "target_role": "extracted target role (in user's language)",
                "summary": "Brief explanation of the gap (in user's language)",
                "missing_skills": ["Critical Skill 1", "Critical Skill 2", "Critical Skill 3"]
            }}
            """,
            input_variables=["user_message"]
        )

        chain = prompt | self.llm | parser
        return chain.invoke({"user_message": user_message})

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