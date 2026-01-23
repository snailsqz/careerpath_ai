import sys
import io
import builtins
import re

# Redirect stderr for UTF-8 (Windows fix)
sys.stderr.reconfigure(encoding='utf-8')

# Monkey patch print to stderr to avoid breaking MCP JSON protocol on stdout
original_print = builtins.print

def safe_print(*args, **kwargs):
    kwargs['file'] = sys.stderr 
    original_print(*args, **kwargs)

builtins.print = safe_print

from mcp.server.fastmcp import FastMCP
from src.careerpath_ai.engine.skill_engine import SkillEngine
from src.careerpath_ai.config import GOOGLE_API_KEY

mcp = FastMCP("Career Path Advisor")

try:
    print("Loading SkillEngine...")
    if GOOGLE_API_KEY:
        engine = SkillEngine()
        print("SkillEngine Loaded for MCP System")
    else:
        print("Error: Google API Key missing.")
        engine = None
except Exception as e:
    print(f"Error loading SkillEngine: {e}")
    engine = None

@mcp.tool()
def get_career_advice(user_query: str) -> str:
    """
    *** CRITICAL INSTRUCTION FOR AI MODEL ***
    You are a DATA REPORTER. You are NOT an editor.
    
    Your ONLY job is to copy-paste the output from this tool to the user.
    
    RULES:
    1. DO NOT summarize, group, or re-organize the courses.
    2. DO NOT add your own descriptions or commentary to the courses.
    3. DISPLAY EVERY LINK provided by the tool. Do not skip any.
    4. If the tool output has "Step 1", "Step 2", keep that structure exactly.
    
    Args:
        user_query: The user's request.
    """
    if not engine:
        return "System Error: SkillEngine is not initialized. Please check server logs and API Key."

    try:   
        result = engine.analyze_and_recommend(user_query)
        
        intent = result.get('user_intent', {})
        c_role = intent.get('detected_current_role', 'Unknown')
        t_role = intent.get('detected_target_role', 'Unknown')
        
        output = f"# CAREER GOAL: {c_role} -> {t_role}\n\n"
        
        # Summary Formatting
        summary = result.get('analysis_summary', '')
        
        # Clean formatting
        clean_summary = summary.replace("**", "").replace("```", "")
        clean_summary = re.sub(r"^\s+", "", clean_summary, flags=re.MULTILINE)
        
        formatted_summary = re.sub(
            r"(?:^|\n)\s*[\*\-\•◦]?\s*(Phase|ระยะ)",
            r"\n\n### \1",
            clean_summary
        )
        
        output += f"{formatted_summary.strip()}\n\n"
        output += "---\n\n"
        output += "### RECOMMENDED LEARNING PATH\n"
        
        # Recommendations
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
                    # Markdown Link
                    output += f"- **Course:** [{course['title']}]({course['url']})\n"
                    output += f"- **Duration:** {course['duration']}\n"
                else:
                    output += "- (No specific course found in database)\n"
                
                output += "\n"
                
        print(f"DEBUG OUTPUT TO CLAUDE:\n{output}")
        return output
    
    except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

    except TimeoutError:
        return "Error: The database took too long to respond. Please ask the user to try again."
        
    except ValueError as e:
        return f"Error: Invalid input data ({str(e)}). Please ask the user for more details."
        
    except Exception as e:
        return f"System Error: An unexpected error occurred in the Career Tool. Details: {str(e)}"

if __name__ == "__main__":
    mcp.run()
