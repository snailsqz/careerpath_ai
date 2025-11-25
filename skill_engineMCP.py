from mcp.server.fastmcp import FastMCP
from modules.skill_engine import SkillEngine
from dotenv import load_dotenv
import os

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
        
        summary = result.get('analysis_summary', 'No summary provided.')
        
        output = f"--- CAREER ANALYSIS REPORT ---\n"
        output += f"{summary}\n\n"
        output += f"--- RECOMMENDED COURSES ---\n"
        
        recommendations = result.get('recommendations', [])
        if not recommendations:
            output += "No specific recommendations found based on the database.\n"
        else:
            for i, item in enumerate(recommendations, 1):
                skill = item.get('skill_gap', 'Unknown Skill')
                output += f"{i}. Missing Skill: {skill}\n"
                
                courses = item.get('suggested_courses', [])
                if courses:
                    course = courses[0]
                    output += f"   - Course: {course['title']}\n"
                    output += f"   - URL: {course['url']}\n"
                    output += f"   - Duration: {course['duration']}\n"
                else:
                    output += "   - No course found in database.\n"
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