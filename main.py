import sys

# Deferred import to allow faster startup feedback
# from src.engine.skill_engine import SkillEngine
from src.config import GOOGLE_API_KEY


def print_result(result):
    print("\n" + "=" * 60)

    intent = result.get("user_intent", {})
    c_role = intent.get("detected_current_role", "Unknown")
    t_role = intent.get("detected_target_role", "Unknown")

    print(f"CAREER GOAL: {c_role}  >>>  {t_role}")
    print("=" * 60)

    # Section 1: Strategic Roadmap
    print("\n[ STRATEGIC ROADMAP ]")
    summary = result.get("analysis_summary", "")
    # Format for readability
    formatted_summary = summary.replace("Phase", "\n• Phase").replace(
        "ระยะ", "\n• ระยะ"
    )
    print(formatted_summary.strip())
    print("-" * 60)

    # Section 2: Execution
    recommendations = result.get("recommendations", [])

    if not recommendations:
        print("No specific recommendations found.")
    else:
        print(f"\n[ RECOMMENDED LEARNING PATH (Step-by-Step) ]")
        print(
            f"Follow this sequence to close your {len(recommendations)} skill gaps:\n"
        )

        for i, item in enumerate(recommendations, 1):
            skill_name = item["skill_gap"]

            print(f"STEP {i}: {skill_name}")

            courses = item.get("suggested_courses", [])
            if courses:
                course = courses[0]  # Take the top result
                print(f"Course:   {course['title']}")
                print(f"Link:     {course['url']}")
                print(f"Duration: {course['duration']}")
            else:
                print("(Please search for this skill manually)")

            print("   " + "." * 40 + "\n")

    print("=" * 60 + "\n")


def main():
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in environment variables or .env file.")
        sys.exit(1)

    print("Importing core modules...")
    from src.engine.skill_engine import SkillEngine

    print("Initializing AI Engine...")
    try:
        engine = SkillEngine()
        if engine.db is None:
            print("Warning: Vector Database not found.")
            print("Please run the update pipeline first to populate the database.")
    except Exception as e:
        print(f"Failed to initialize engine: {e}")
        sys.exit(1)

    print("System Ready! (Type 'exit' to quit)")
    print("-" * 30)

    while True:
        try:
            user_input = input("User: ").strip()

            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting...")
                break

            if not user_input:
                continue

            print("Thinking...")
            # Use a static session ID for the CLI to maintain history throughout the run
            result = engine.analyze_and_recommend(user_input, session_id="cli_user_01")
            print_result(result)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error processing request: {e}")


if __name__ == "__main__":
    main()
