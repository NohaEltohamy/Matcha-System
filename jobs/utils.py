# job_board/utils.py

import requests
import json
import os
GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "https://api.gemini.com/v1/completions")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDKp4bMo8-Br-iHGMAIe0EpHn-xmk2LcYw") # Store securely, e.g., in environment variables

def generate_job_suggestions(title: str) -> dict:
    """
    Generates AI-suggested job description and skills based on the job title
    by sending a prompt to a completion API (e.g., Gemini).
    """
    # --- Configuration for your AI API ---   
    if GEMINI_API_KEY == "AIzaSyDKp4bMo8-Br-iHGMAIe0EpHn-xmk2LcYw":
        print("WARNING: Gemini API Key is not set. Using mock suggestions.")
        # Fallback to mock suggestions if API key is not configured
        return _generate_mock_suggestions(title)

    # Construct the prompt for the AI model
    prompt = f"""
    Generate a job description and a list of 5-10 required skills for a job with the title: "{title}".
    The output should be a JSON object with two keys: "description" (string) and "skills" (array of strings).
    Example:
    {{
        "description": "We are looking for an experienced Software Engineer...",
        "skills": ["Python", "Django", "SQL", "AWS", "Git"]
    }}
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}" # Or whatever authentication method your API uses
    }

    # Assuming a simple request body structure for a completion API
    data = {
        "model": "gemini-2.5-flash",
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        completion_response = response.json()

        # Assuming the completion API returns the generated text directly in a 'text' field
        # and you need to parse the JSON string from it.
        # Adjust this parsing based on the actual structure of your Gemini API response.
        if "choices" in completion_response and completion_response["choices"]:
            generated_text = completion_response["choices"][0].get("text", "")
            try:
                # Attempt to parse the generated text as JSON
                suggestions = json.loads(generated_text)
                return {
                    "description": suggestions.get("description", "Could not generate description."),
                    "skills": suggestions.get("skills", ["Could not generate skills."])
                }
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from AI response: {generated_text}")
                return _generate_mock_suggestions(title)
        else:
            print(f"No 'choices' found in AI response: {completion_response}")
            return _generate_mock_suggestions(title)

    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        return _generate_mock_suggestions(title)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return _generate_mock_suggestions(title)


def _generate_mock_suggestions(title: str) -> dict:
    """
    Helper function for mock suggestions when AI API is not configured or fails.
    """
    mock_descriptions = {
        "Software Engineer": "We are looking for a talented Software Engineer to join our dynamic team. You will be responsible for designing, developing, and maintaining high-quality software solutions. Experience with Python/Django and React is a plus.",
        "Data Scientist": "Join our data science team to analyze complex datasets, build predictive models, and extract actionable insights. Proficiency in Python, R, and machine learning frameworks is required.",
        "Product Manager": "Seeking an experienced Product Manager to lead the lifecycle of our innovative products. You will define product vision, strategy, and roadmap, working closely with engineering, design, and marketing teams.",
        "Marketing Specialist": "We need a creative Marketing Specialist to develop and execute marketing campaigns across various channels. Strong understanding of digital marketing, SEO, and social media is essential.",
    }

    mock_skills = {
        "Software Engineer": ["Python", "Django", "REST APIs", "SQL", "Git", "Cloud Platforms"],
        "Data Scientist": ["Python", "R", "Machine Learning", "SQL", "Estadística", "Data Visualization"],
        "Product Manager": ["Product Lifecycle", "Agile Methodologies", "Market Research", "Stakeholder Management", "UX/UI"],
        "Marketing Specialist": ["Digital Marketing", "SEO", "SEM", "Social Media", "Content Creation", "Analytics"],
    }

    suggested_description = "A dynamic role within a growing company. Responsibilities include various tasks related to " + title.lower() + "."
    suggested_skills = ["Communication", "Problem-solving", "Teamwork"]

    for key in mock_descriptions:
        if key.lower() in title.lower():
            suggested_description = mock_descriptions[key]
            suggested_skills = mock_skills[key]
            break

    return {
        "description": suggested_description,
        "skills": suggested_skills,
    }




def generate_cv_evaluation(cv, job):
    """
    Generates AI evaluation of a CV against a job posting
    Returns a dictionary with scores and analysis
    """
     
    if GEMINI_API_KEY == "AIzaSyDKp4bMo8-Br-iHGMAIe0EpHn-xmk2LcYw":
        print("WARNING: Gemini API Key is not set. Using mock evaluation.")
        return _generate_mock_cv_evaluation(cv, job)
    
    # Construct the prompt for CV evaluation
    prompt = f"""
    Evaluate this CV against the job posting and provide a comprehensive analysis.
    
    JOB POSTING:
    Title: {job.title}
    Description: {job.description}
    Required Skills: {', '.join(job.skills)}
    
    CV INFORMATION:
    Candidate: {cv.candidate.name}
    CV Title: {cv.title}
    File: {cv.file_name}
    
    Please provide a JSON response with the following structure:
    {{
        "genai_score": 85.5,
        "skills_match_score": 80.0,
        "experience_match_score": 90.0,
        "overall_fit_score": 85.0,
        "ai_analysis": "Detailed analysis of the candidate's fit for this position, including strengths, weaknesses, and recommendations."
    }}
    
    Score ranges: 0-100 (higher is better)
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    
    data = {
        "model": "gemini-2.5-flash",
        "prompt": prompt,
        "max_tokens": 800,
        "temperature": 0.3,
    }
    
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        
        completion_response = response.json()
        
        if "choices" in completion_response and completion_response["choices"]:
            generated_text = completion_response["choices"][0].get("text", "")
            try:
                evaluation = json.loads(generated_text)
                return {
                    "genai_score": float(evaluation.get("genai_score", 0)),
                    "skills_match_score": float(evaluation.get("skills_match_score", 0)),
                    "experience_match_score": float(evaluation.get("experience_match_score", 0)),
                    "overall_fit_score": float(evaluation.get("overall_fit_score", 0)),
                    "ai_analysis": evaluation.get("ai_analysis", "Analysis not available.")
                }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to decode JSON from AI response: {generated_text}")
                return _generate_mock_cv_evaluation(cv, job)
        else:
            print(f"No 'choices' found in AI response: {completion_response}")
            return _generate_mock_cv_evaluation(cv, job)
            
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        return _generate_mock_cv_evaluation(cv, job)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return _generate_mock_cv_evaluation(cv, job)


def _generate_mock_cv_evaluation(cv, job):
    """
    Helper function for mock CV evaluation when AI API is not configured or fails.
    """
    import random
    
    # Generate realistic mock scores based on job title matching
    base_score = 60
    if cv.title.lower() in job.title.lower() or job.title.lower() in cv.title.lower():
        base_score = 85
    
    # Add some randomness
    genai_score = max(0, min(100, base_score + random.randint(-15, 15)))
    skills_score = max(0, min(100, genai_score + random.randint(-10, 10)))
    experience_score = max(0, min(100, genai_score + random.randint(-10, 10)))
    overall_score = (genai_score + skills_score + experience_score) / 3
    
    analysis = f"""
    Candidate Analysis for {job.title}:
    
    STRENGTHS:
    - Relevant experience in {cv.title}
    - Strong technical background
    - Good communication skills
    
    AREAS FOR IMPROVEMENT:
    - Could benefit from additional experience in specific technologies
    - Consider highlighting relevant projects
    
    RECOMMENDATION:
    {'Strong candidate' if genai_score > 80 else 'Moderate fit' if genai_score > 60 else 'Consider other candidates'}
    
    Overall compatibility: {genai_score:.1f}%
    """
    
    return {
        "genai_score": round(genai_score, 1),
        "skills_match_score": round(skills_score, 1),
        "experience_match_score": round(experience_score, 1),
        "overall_fit_score": round(overall_score, 1),
        "ai_analysis": analysis.strip()
    }


#interview
# Add this function to your utils.py file after the _generate_mock_cv_evaluation function

def generate_interview_prompt(candidate, job, interview_type="technical"):
    """
    Generates AI interview prompt/questions for a scheduled interview
    Returns a dictionary with interview questions and guidance
    """
    
    if GEMINI_API_KEY == "AIzaSyDKp4bMo8-Br-iHGMAIe0EpHn-xmk2LcYw":
        print("WARNING: Gemini API Key is not set. Using mock interview prompt.")
        return _generate_mock_interview_prompt(candidate, job, interview_type)
    
    # Construct the prompt for interview questions generation
    prompt = f"""
    Generate a comprehensive interview prompt and questions for a {interview_type} interview.
    
    JOB POSTING:
    Title: {job.title}
    Description: {job.description}
    Required Skills: {', '.join(job.skills) if job.skills else 'Not specified'}
    
    CANDIDATE:
    Name: {candidate.name}
    
    Please provide a JSON response with the following structure:
    {{
        "interview_prompt": "Introduction and overview of the interview process...",
        "questions": [
            {{
                "question": "Sample question about experience?",
                "category": "experience",
                "expected_answer_points": "Key points to look for"
            }}
        ],
        "evaluation_criteria": "What to look for in answers",
        "interview_tips": "Tips for conducting the interview",
        "duration_estimate": 30
    }}
    
    Generate 5-8 relevant {interview_type} questions based on the job requirements.
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    
    data = {
        "model": "gemini-2.5-flash",
        "prompt": prompt,
        "max_tokens": 1500,
        "temperature": 0.5,
    }
    
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        
        completion_response = response.json()
        
        if "choices" in completion_response and completion_response["choices"]:
            generated_text = completion_response["choices"][0].get("text", "")
            try:
                interview_data = json.loads(generated_text)
                return interview_data
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to decode JSON from AI response: {generated_text}")
                return _generate_mock_interview_prompt(candidate, job, interview_type)
        else:
            return _generate_mock_interview_prompt(candidate, job, interview_type)
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return _generate_mock_interview_prompt(candidate, job, interview_type)


def _generate_mock_interview_prompt(candidate, job, interview_type):
    """
    Helper function for mock interview prompt when AI API is not configured or fails.
    """
    import random
    
    questions = []
    
    if interview_type == "technical":
        questions = [
            {
                "question": f"Tell me about your experience with {', '.join(job.skills[:3]) if job.skills else 'the required technologies'}.",
                "category": "technical",
                "expected_answer_points": "Look for proficiency in key technologies, real-world applications, problem-solving examples"
            },
            {
                "question": "Describe a challenging project you worked on and how you overcame obstacles.",
                "category": "problem-solving",
                "expected_answer_points": "Problem identification, approach taken, solutions implemented, lessons learned"
            },
            {
                "question": "How do you stay updated with the latest technologies in your field?",
                "category": "learning",
                "expected_answer_points": "Continuous learning habits, specific resources, practical application of new knowledge"
            },
            {
                "question": "Walk me through how you would approach solving [describe a relevant technical problem].",
                "category": "problem-solving",
                "expected_answer_points": "Methodology, critical thinking, technical knowledge, practical approach"
            }
        ]
    elif interview_type == "behavioral":
        questions = [
            {
                "question": "Tell me about a time when you had to work under pressure. How did you handle it?",
                "category": "pressure",
                "expected_answer_points": "Stress management, time management, team collaboration, results achieved"
            },
            {
                "question": "Describe a situation where you had to resolve a conflict with a team member.",
                "category": "collaboration",
                "expected_answer_points": "Conflict resolution approach, communication skills, empathy, outcome"
            },
            {
                "question": "What motivates you in your work?",
                "category": "motivation",
                "expected_answer_points": "Personal drive, alignment with company values, growth mindset"
            },
            {
                "question": "Can you give an example of a time you had to learn something new quickly?",
                "category": "adaptability",
                "expected_answer_points": "Learning ability, willingness to adapt, problem-solving under pressure"
            }
        ]
    else:
        # Mix of both
        questions = [
            {
                "question": f"Why are you interested in this {job.title} position?",
                "category": "motivation",
                "expected_answer_points": f"Alignment with {job.title} role, career goals, passion for the work"
            },
            {
                "question": "Tell me about a relevant project from your experience.",
                "category": "experience",
                "expected_answer_points": "Technical depth, problem-solving, results achieved, lessons learned"
            },
            {
                "question": "How do you handle feedback and criticism?",
                "category": "growth",
                "expected_answer_points": "Openness to feedback, ability to adapt, growth mindset"
            }
        ]
    
    interview_prompt = f"""
    Welcome to the interview for the {job.title} position at our company.
    
    TODAY'S AGENDA:
    We'll discuss your experience, skills in {', '.join(job.skills[:5]) if job.skills else 'relevant technologies'}, and how you can contribute to our team.
    
    STRUCTURE:
    - Introduction (5 minutes)
    - Technical/Behavioral Questions (20 minutes)
    - Your Questions (5 minutes)
    
    Let's begin with a brief introduction about yourself and your background.
    """
    
    evaluation_criteria = f"""
    EVALUATION CRITERIA FOR {job.title}:
    
    1. Technical Competence (40%)
       - Proficiency in required skills
       - Problem-solving ability
       - Practical experience with relevant technologies
    
    2. Communication Skills (20%)
       - Clarity of expression
       - Ability to explain technical concepts
       - Listening and understanding
    
    3. Cultural Fit (20%)
       - Alignment with company values
       - Team collaboration
       - Growth mindset
    
    4. Relevant Experience (20%)
       - Past projects and achievements
       - Industry knowledge
       - Practical application of skills
    """
    
    interview_tips = f"""
    INTERVIEW TIPS FOR {interview_type.upper()} INTERVIEW:
    
    1. Create a comfortable environment for open discussion
    2. Focus on assessing practical skills and problem-solving
    3. Ask follow-up questions based on candidate's responses
    4. Observe communication style and team fit
    5. Provide clear feedback about next steps after the interview
    """
    
    return {
        "interview_prompt": interview_prompt.strip(),
        "questions": questions,
        "evaluation_criteria": evaluation_criteria.strip(),
        "interview_tips": interview_tips.strip(),
        "duration_estimate": 30
    }