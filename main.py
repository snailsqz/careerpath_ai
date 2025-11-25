import os
import json
import sys
from dotenv import load_dotenv
from modules.skill_engine import SkillEngine

load_dotenv()

def print_result(result):
    print("\n" + "="*60)
    
    intent = result.get('user_intent', {})
    c_role = intent.get('detected_current_role', 'Unknown')
    t_role = intent.get('detected_target_role', 'Unknown')
    
    print(f"CAREER GOAL: {c_role}  >>>  {t_role}")
    print("="*60)
    
    # ส่วนที่ 1: แผนที่นำทาง (Strategy)
    print("\n[ STRATEGIC ROADMAP ]")
    summary = result.get('analysis_summary', '')
    # จัด Format ให้สวยงาม ถ้ามีคำว่า Phase ให้ขึ้นบรรทัดใหม่
    formatted_summary = summary.replace("Phase", "\n• Phase").replace("ระยะ", "\n• ระยะ")
    print(formatted_summary.strip())
    print("-" * 60)
    
    # ส่วนที่ 2: ลำดับการเรียน (Execution)
    recommendations = result.get('recommendations', [])
    
    if not recommendations:
        print("No specific recommendations found.")
    else:
        print(f"\n[ RECOMMENDED LEARNING PATH (Step-by-Step) ]")
        print(f"Follow this sequence to close your {len(recommendations)} skill gaps:\n")
        
        for i, item in enumerate(recommendations, 1):
            skill_name = item['skill_gap']
            
            print(f"STEP {i}: {skill_name}") 
            
            courses = item.get('suggested_courses', [])
            if courses:
                course = courses[0] # เอาแค่อันแรกที่คะแนนดีสุด
                print(f"Course:   {course['title']}")
                print(f"Link:     {course['url']}")
                print(f"Duration: {course['duration']}")
            else:
                print("(Please search for this skill manually)")
            
            print("   " + "." * 40 + "\n")
    
    print("="*60 + "\n")

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env file.")
        print("Please create .env file and add your key.")
        sys.exit(1)

    print("Initializing AI Engine...")
    try:
        engine = SkillEngine(google_api_key=api_key)
        if engine.db is None:
            print("Warning: Vector Database not found.")
            print("Please run 'python update_pipeline.py' or 'modules/vector_manager.py' first.")
    except Exception as e:
        print(f"Failed to initialize engine: {e}")
        sys.exit(1)

    print("System Ready! (Type 'exit' to quit)")
    print("-" * 30)

    while True:
        try:
            user_input = input("User: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Exiting...")
                break
            
            if not user_input:
                continue

            print("Thinking...")
            result = engine.analyze_and_recommend(user_input)
            print_result(result)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error processing request: {e}")

if __name__ == "__main__":
    main()