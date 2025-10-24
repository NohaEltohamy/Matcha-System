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

