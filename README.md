# Career Path AI Recommender Module

This module provides an AI-powered skill gap analysis and course recommendation engine (RAG).
It integrates data from Coursera and SkillLane to suggest learning paths based on user career goals.

## Prerequisites

- Python 3.8+
- Google Gemini API Key

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create .env with GOOGLE_API_KEY inside it
3. Run it
   ```bash
   python -u demo_ui.py
   ```

## Example Questions

Try asking the AI these questions to see how it analyzes skill gaps and recommends courses:

### English Prompts

- **Career Switch:** "I am a Frontend Developer, but I want to switch to Backend Development. What should I learn?"
- **Upskilling:** "I am a Junior Data Scientist. How can I become a Senior Data Scientist?"
- **Cross-Domain:** "I am an Accountant, but I want to transition into an AI Engineer role."
- **Leadership:** "I am a Senior Developer looking to become a CTO or Tech Lead. What skills am I missing?"
- **Specific Tech:** "I want to master MLOps and CI/CD pipelines. Where should I start?"

### Thai Prompts

- **ย้ายสายงาน:** "ตอนนี้เป็น Admin แต่อยากย้ายสายไปทำ Data Analyst ต้องเริ่มยังไงครับ"
- **เลื่อนตำแหน่ง:** "ผมเป็น AI Engineer อยากขยับไปเป็น Project Manager ต้องรู้อะไรเพิ่มบ้าง"
- **ข้ามสาย:** "ไม่ได้จบสายคอมมา แต่อยากทำงานเป็น Software Engineer เริ่มจากศูนย์ได้ไหม"
- **เป้าหมายกว้างๆ:** "อยากได้งานสาย Tech ที่เงินเดือนสูงๆ แนะนำหน่อย"
- **เจาะจงสกิล:** "แนะนำคอร์สเรียน Python และ Machine Learning สำหรับมือใหม่หน่อย"
