from mcp.server.fastmcp import FastMCP
from modules.skill_engine import SkillEngine
from dotenv import load_dotenv
import re

load_dotenv()

mcp = FastMCP("Career Path Advisor")

try:
    engine = SkillEngine()
    print("SkillEngine Loaded for MCP System")
except Exception as e:
    print(f"Error loading SkillEngine: {e}")
    engine = None

@mcp.tool()
def get_career_advice(user_query: str) -> str:
    """
    [ชื่อ Tool]: Career Path Advisor & Course Recommender
    
    [หน้าที่]: Use this tool when a user asks for:
    - Career guidance or switching career paths (e.g., "Admin to Data Analyst").
    - Skill gap analysis for a specific role.
    - Recommended courses for specific skills (Python, Management, etc.).
    
    [Input]: 'user_query' should be the full context of the user's career question.
    [Output]: Returns a strategic roadmap and list of recommended courses with links.
    
    [ข้อห้าม]: DO NOT use this tool for general questions like "What is the weather?" or simple coding help.
    """
    if not engine:
        return "System Error: SkillEngine is not initialized. Please check server logs."

    try:   
        result = engine.analyze_and_recommend(user_query)
        
        intent = result.get('user_intent', {})
        c_role = intent.get('detected_current_role', 'Unknown')
        t_role = intent.get('detected_target_role', 'Unknown')
        
        output = f"# CAREER GOAL: {c_role} -> {t_role}\n\n"
        
        # 3. จัดการ Summary (ใช้ Regex ล้างขยะเหมือนใน Demo UI)
        summary = result.get('analysis_summary', '')
        
        # ล้างตัวหนาและ Code Block
        clean_summary = summary.replace("**", "").replace("```", "")
        # ลบย่อหน้าเกิน
        clean_summary = re.sub(r"^\s+", "", clean_summary, flags=re.MULTILINE)
        # จัดหัวข้อ Phase สวยๆ
        formatted_summary = re.sub(
            r"(?:^|\n)\s*[\*\-•◦]?\s*(Phase|ระยะ)",
            r"\n\n### \1",
            clean_summary
        )
        
        output += f"{formatted_summary.strip()}\n\n"
        output += "---\n\n"
        output += "### RECOMMENDED LEARNING PATH\n"
        
        # 4. จัดการ Course List
        recommendations = result.get('recommendations', [])
        
        if not recommendations:
            output += "No specific recommendations found in the database.\n"
        else:
            for i, item in enumerate(recommendations, 1):
                skill_name = item.get('skill_gap', 'Unknown Skill')
                output += f"#### Step {i}: {skill_name}\n"
                
                courses = item.get('suggested_courses', [])
                if courses:
                    course = courses[0]
                    # ส่งกลับเป็น Markdown Link เพื่อให้ Claude แสดงผลสวยๆ
                    output += f"- **Course:** [{course['title']}]({course['url']})\n"
                    output += f"- **Duration:** {course['duration']}\n"
                else:
                    output += "- (No specific course found in database)\n"
                
                output += "\n"
                
        print(f"DEBUG OUTPUT TO CLAUDE:\n{output}")
        return output

    except TimeoutError:
        return "Error: The database took too long to respond. Please ask the user to try again."
        
    except ValueError as e:
        return f"Error: Invalid input data ({str(e)}). Please ask the user for more details."
        
    except Exception as e:
        return f"System Error: An unexpected error occurred in the Career Tool. Details: {str(e)}"

if __name__ == "__main__":
    mcp.run()