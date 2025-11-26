import gradio as gr
from modules.skill_engine import SkillEngine
from dotenv import load_dotenv
import time
import re

load_dotenv()
engine = SkillEngine()

def career_advisor(user_message):
    yield "*AI กำลังวิเคราะห์สกิลและค้นหาคอร์สเรียน... (อาจใช้เวลา 5-10 วินาที)*"
    try:
        result = engine.analyze_and_recommend(user_message)
        
        intent = result.get('user_intent', {})
        c_role = intent.get('detected_current_role', 'Unknown')
        t_role = intent.get('detected_target_role', 'Unknown')
        
        output_text = f"CAREER GOAL: {c_role} ➔ {t_role}\n"
        output_text += "---\n\n"
        
        output_text += "### STRATEGIC ROADMAP\n"
        summary = result.get('analysis_summary', '')

        clean_summary = summary.replace("**", "").replace("```", "")

        clean_summary = re.sub(r"^\s+", "", clean_summary, flags=re.MULTILINE)

        # 3. ใช้ Regex จัดการหัวข้อ Phase/ระยะ เหมือนเดิม
        formatted_summary = re.sub(
            r"(?:^|\n)\s*[\*\-•◦]?\s*(Phase|ระยะ)",
            r"\n\n### \1",
            clean_summary
        )
        
        output_text += f"{formatted_summary}\n\n"
        
        output_text += "### RECOMMENDED LEARNING PATH (Step-by-Step)\n"
        recommendations = result.get('recommendations', [])
        
        if not recommendations:
            output_text += "*No specific recommendations found.*"
        else:
            for i, item in enumerate(recommendations, 1):
                skill_name = item['skill_gap']
                
                output_text += f"#### STEP {i}: {skill_name}\n"
                
                courses = item.get('suggested_courses', [])
                if courses:
                    course = courses[0]                    
                    output_text += f"- **Course:** [{course['title']}]({course['url']})\n"
                    output_text += f"- **Duration:** {course['duration']}\n"
                else:
                    output_text += "- *(Please search for this skill manually)*\n"
                
                output_text += "\n"

        chunk_size = 50 
        for i in range(0, len(output_text), chunk_size):
            # ส่งข้อความทีละท่อนใหญ่ๆ
            yield output_text[:i+chunk_size]
            # ไม่ต้อง sleep หรือ sleep น้อยมากๆ
            time.sleep(0.01) 
            
        yield output_text

    except Exception as e:
        yield f"Error: {str(e)}"

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
    iface.launch(theme=gr.themes.Soft())