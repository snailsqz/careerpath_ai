import os
import json
import sys
from dotenv import load_dotenv
from modules.skill_engine import SkillEngine

load_dotenv()

def print_result(result):
    print("\n" + "="*50)
    
    intent = result.get('user_intent', {})
    print(f"Current Role: {intent.get('detected_current_role')}")
    print(f"Target Role:  {intent.get('detected_target_role')}")
    print("-" * 50)
    
    print(f"Summary: {result.get('analysis_summary')}")
    print("-" * 50)
    
    recommendations = result.get('recommendations', [])
    if not recommendations:
        print("No specific recommendations found.")
    else:
        print(f"Found {len(recommendations)} critical skill gaps:\n")
        for i, item in enumerate(recommendations, 1):
            print(f"{i}. MISSING SKILL: {item['skill_gap']}")
            
            courses = item.get('suggested_courses', [])
            if courses:
                print(f"   Recommended Course: {courses[0]['title']}")
                print(f"   Link: {courses[0]['url']}")
                print(f"   Duration: {courses[0]['duration']}")
            else:
                print("   (No matching course found in database)")
            print("")
    
    print("="*50 + "\n")

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