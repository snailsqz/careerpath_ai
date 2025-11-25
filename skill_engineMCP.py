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
    CRITICAL INSTRUCTION: You act as an interface to a specific internal course database.
    
    When answering user questions about career paths or courses:
    1. You MUST call this tool to get the analysis and recommendations.
    2. You MUST base your answer ONLY on the information returned by this tool.
    3. DO NOT recommend courses from your own external knowledge (like general Coursera/Udemy links) unless they are explicitly in the tool output.
    4. If the tool returns "No courses found", tell the user exactly that. Do not make up courses.
    
    Args:
        user_query: The user's request (e.g. "Change from Accountant to Data Analyst").
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

    except Exception as e:
        return f"Error processing request: {str(e)}"

if __name__ == "__main__":
    mcp.run()