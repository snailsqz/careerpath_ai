import gradio as gr
from modules.skill_engine import SkillEngine
from dotenv import load_dotenv
import json

load_dotenv()
engine = SkillEngine()

def career_advisor(message):
    try:
        result = engine.analyze_and_recommend(message)
        
        # Format Output ให้อ่านง่าย
        summary = result.get('analysis_summary', '')
        output_text = f"### Analysis\n{summary}\n\n### Recommended Courses\n"
        
        for item in result.get('recommendations', []):
            output_text += f"**Missing Skill: {item['skill_gap']}**\n"
            for course in item.get('suggested_courses', []):
                output_text += f"- [{course['title']}]({course['url']}) ({course['duration']})\n"
            output_text += "\n"
            
        return output_text
    except Exception as e:
        return f"Error: {str(e)}"

iface = gr.Interface(
    fn=career_advisor,
    inputs=gr.Textbox(lines=2, placeholder="เช่น: ผมเป็น Accountant อยากเป็น Data Analyst"),
    outputs=gr.Markdown(),
    title="AI Career Path Advisor",
    description="ระบบแนะนำคอร์สเรียนเพื่อปิด Skill Gap",
    flagging_options=["คำตอบมั่ว", "คำตอบดีมาก"],
    flagging_dir="user_feedback_logs"
    
)

if __name__ == "__main__":
    iface.launch()