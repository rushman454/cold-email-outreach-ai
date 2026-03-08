import os
import re
import requests
import google.generativeai as genai
from urllib.parse import quote_plus, unquote
from google.colab import userdata

# === API Keys ===
# Paste your real keys here before running locally
GEMINI_API_KEY = userdata.get('gak')
SERP_API_KEY = userdata.get('sak')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# === Form Input ===
form_data = {
    "fullName": "Aaroosh Badkar",
    "school": "University of Indiana, Kelly School ",
    "outreachGoal": "Investment Banking",
    "Target Role/Title": "Summer Analyst",
    "Target Companies": "Goldman Sachs, Morgan Stanley, Bank of America",
    "Shared Interest": "Golf, Poker, Skiing",
    "clubs": "DECA, Investment Club, Finance Scholars Club"
}

# === Build Google Search Query ===
role = quote_plus(form_data["Target Role/Title"])
companies = [c.strip() for c in form_data["Target Companies"].split(",") if c.strip()]
school = quote_plus(form_data["school"])
company = quote_plus(companies[0]) if companies else ""
query = f'site:linkedin.com/in {role} {company} {school}'

# === Call SerpAPI ===
def get_linkedin_profiles_from_serpapi(query, api_key):
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f" Error calling SerpAPI: {e}")
        return []

    links = []
    for result in data.get("organic_results", []):
        link = result.get("link", "")
        if re.match(r"https://(www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+", link):
            links.append(link)
        if len(links) >= 10:
            break
    return links


linkedin_links = get_linkedin_profiles_from_serpapi(query, SERP_API_KEY)

# === Gemini Email Generator ===
def generate_email(contact_name, linkedin_url):
    prompt = f"""
Write a short, warm cold email from {form_data['fullName']}, a student at {form_data['school']}, to {contact_name}, a professional at {companies[0]}.

Context:
- The student's goal: {form_data['outreachGoal']}
- Shared interest: {form_data['Shared Interest']}
- Club/Org affiliations: {form_data['clubs']}
- The LinkedIn URL: {linkedin_url}

Instructions:
- Keep it under 300 words
- Do not mention scraping or automation
- Make it genuine, friendly, and respectful
- Use the contacts first name when greeting
- When asking to chat, use the phrase coffee chat
- 
    """.strip()

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        # Handle both .text and .candidates responses depending on version
        if hasattr(response, "text"):
            return response.text.strip()
        elif hasattr(response, "candidates"):
            return response.candidates[0].content.parts[0].text.strip()
        else:
            return " Could not generate email text."
    except Exception as e:
        return f"❌ Gemini API Error: {e}"


# === Extract Name from LinkedIn URL ===
def extract_name_from_linkedin_url(url):
    match = re.search(r"linkedin\.com/in/([a-zA-Z0-9\-_%]+)", url)
    if match:
        name = unquote(match.group(1)).replace('-', ' ').replace('_', ' ').title()
        return name
    return "Contact"


# === Generate and Print Emails ===
print(" Cold Outreach Emails Generated:\n")

if not linkedin_links:
    print(" No LinkedIn links found. Try a broader company/role/school combo.")
else:
    for i, link in enumerate(linkedin_links, 1):
        name = extract_name_from_linkedin_url(link)
        email_body = generate_email(name, link)
        print(f"--- Email {i} to {name} ({link}) ---")
        print(email_body)
        print("\n" + "-"*70 + "\n")
