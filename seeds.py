import json
import os
from collections import defaultdict

user_sentiments = [
    "Disappointed", "Indifferent", "Proud", "Grateful", "Hesitant", 
    "Calm", "Cautious", "Lonely", "Hopeful", "Skeptical", "Nostalgic", 
    "Uncertain", "Frustrated", "Pessimistic", "Optimistic", "Angry", 
    "Confident", "Anxious", "Content", "Overwhelmed", "Confused", "Sad", 
    "Contemplative", "Curious", "Excited", "Happy"
]

with open(os.path.join('seed_data', 'user_sentiments.json'), 'w') as f:
    json.dump(user_sentiments, f, indent=4)


personality_traits = [
    "Openness to Experience",
    "Conscientiousness",
    "Extraversion",
    "Agreeableness",
    "Neuroticism"
]

with open(os.path.join('seed_data', 'personality_traits.json'), 'w') as f:
    json.dump(personality_traits, f, indent=4)

topics_contexts_1 = {
    "Technology": [
        "Device malfunctions and troubleshooting (e.g., smartphones, laptops)",
        "Software bugs and error messages",
        "Connectivity issues (e.g., Wi-Fi, network outages)"
    ],
    "Health & Wellness": [
        "Minor physical symptoms (e.g., headaches, fatigue)",
        "Mental health concerns (e.g., stress, anxiety)",
        "Lifestyle guidance (e.g., nutrition, exercise, sleep patterns)"
    ],
    "Politics & Social Issues": [
        "Policy debates and political opinions",
        "Social justice and activism discussions",
        "Government performance and public sentiment"
    ],
    "Entertainment & Media": [
        "Film and TV recommendations and reviews",
        "Music, art, and cultural commentary",
        "Gaming and streaming experiences"
    ],
    "Academic & Career Guidance": [
        "Academic advising and course selection",
        "Career planning and job search strategies",
        "Research tips and study techniques"
    ],
    "Finance & Investment": [
        "Stock market trends and analysis",
        "Personal budgeting and financial planning",
        "Investment strategies and risk management"
    ],
    "Customer Service & Complaints": [
        "Product issues and defect troubleshooting",
        "Service failures and support resolution",
        "Feedback collection and complaint management"
    ]
}

topics_contexts_2 = {
    "Career Advice": [
        "Choosing between two job offers",
        "Dealing with workplace conflict",
        "Struggling with job satisfaction"
    ],
    "Relationships": [
        "Doubts about a romantic relationship",
        "Navigating a friendship conflict",
        "Asking for dating advice"
    ],
    "Health & Fitness": [
        "Trying to lose weight but struggling with motivation",
        "Recovering from an injury and feeling frustrated",
        "Debating between different workout routines"
    ],
    "Personal Finance": [
        "Struggling with budgeting and saving money",
        "Deciding whether to invest in stocks or crypto",
        "Dealing with financial stress and anxiety"
    ],
    "Technology & AI": [
        "Excitement about a new AI model release",
        "Concerns about AI replacing jobs",
        "Debating ethical issues in AI development"
    ],
    "Mental Health": [
        "Feeling overwhelmed with life responsibilities",
        "Experiencing social anxiety in public situations",
        "Seeking ways to improve self-confidence"
    ],
    "Philosophy & Ethics": [
        "Debating the meaning of happiness",
        "Discussing the morality of lying in certain situations",
        "Exploring free will vs. determinism"
    ],
    "Politics & Society": [
        "Frustration with government policies",
        "Debating the role of social media in elections",
        "Discussing wealth inequality and capitalism"
    ],
    "Hobbies & Interests": [
        "Struggling to stay consistent with a new hobby",
        "Looking for recommendations on books/movies",
        "Comparing different musical genres and preferences"
    ]
}

merged_topics_contexts = {**topics_contexts_1, **topics_contexts_2}
combined_topics_contexts = defaultdict(list)
for topic_dict in [topics_contexts_1, topics_contexts_2]:
    for topic, contexts in topic_dict.items():
        combined_topics_contexts[topic].extend(contexts)

# Convert back to a regular dictionary if needed
combined_topics_contexts = dict(combined_topics_contexts)

with open(os.path.join("seed_data", "seed_topics.json"), "w") as f:
    json.dump(combined_topics_contexts, f, indent=4)


chatbot_personas = {
    "Default Chatbot": [],
    "Pragmatist": ["Direct", "Solution-Focused", "Efficient", "Minimal Emotional Support"],
    "Tough Mentor": ["Honest", "Critical", "Challenges the User", "Pushes for Growth"],
    "Empathetic Friend": ["Warm", "Compassionate", "Validating", "Reassuring"],
    "Skeptic": ["Questions Assumptions", "Plays Devil’s Advocate", "Rarely Agrees Outright"],
    "AI Therapist": ["Uses Open-Ended Questions", "Encourages Self-Reflection", "Guides Instead of Answering"],
    "Devil’s Advocate": ["Always Challenges User", "Pushes for Critical Thinking"],
    "Corporate Bot": ["Formal", "Professional", "To-the-Point", "Structured Responses"],
    "Encouraging Coach": ["Highly Motivational", "Goal-Oriented", "Pushes User to Take Action"],
    "Humorous Companion": ["Uses Jokes and Sarcasm", "Lighthearted", "Engaging"]
}

with open(os.path.join("seed_data", "chatbot_personas.json"), "w") as f:
    json.dump(chatbot_personas, f, indent=4)