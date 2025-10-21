# job_board/utils.py

import requests
import json
import os

def generate_job_suggestions(title: str) -> dict:
    """
    Generates AI-suggested job description and skills based on the job title
    by sending a prompt to a completion API (e.g., Gemini).
    """
    # --- Configuration for your AI API ---
    # Replace with your actual Gemini API endpoint and API key
    GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "https://api.gemini.com/v1/completions")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY") # Store securely, e.g., in environment variables

    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
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
        "model": "text-davinci-003", # Replace with the actual Gemini model you intend to use (e.g., "gemini-pro")
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
