import random
import json
import pandas as pd
import os

from models import LLM

# Define multiple LLMs
llm_models = ["GPT-4o", "GPT-4o-mini", "CLAUDE-3.7-SONNET", "CLAUDE-3.5-HAIKU"]

# Load data from seed files
def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# Load all seed data
seed_data_dir = os.path.join(os.path.dirname(__file__), 'seed_data')
topics = load_json_file(os.path.join(seed_data_dir, 'topics.json'))
chatbot_personas = load_json_file(os.path.join(seed_data_dir, 'chatbot_personas.json'))
user_sentiments = load_json_file(os.path.join(seed_data_dir, 'user_sentiments.json'))
personality_traits = load_json_file(os.path.join(seed_data_dir, 'personality_traits.json'))

# Number of total conversations to generate
n_iterations = 10  # Increase for larger dataset

# Define high and low variations for each personality trait
personality_variations = {
    trait: {
        "high": f"High {trait}",
        "low": f"Low {trait}"
    } for trait in personality_traits
}

# Descriptions for high and low personality traits
personality_descriptions = {
    "Openness to Experience": {
        "high": "curious, creative, and open to new ideas",
        "low": "conventional, practical, and prefers routine"
    },
    "Conscientiousness": {
        "high": "organized, responsible, and detail-oriented",
        "low": "spontaneous, flexible, and sometimes disorganized"
    },
    "Extraversion": {
        "high": "outgoing, energetic, and sociable",
        "low": "reserved, thoughtful, and prefers solitude"
    },
    "Agreeableness": {
        "high": "cooperative, compassionate, and considerate of others",
        "low": "direct, straightforward, and sometimes competitive"
    },
    "Neuroticism": {
        "high": "sensitive to stress, emotionally reactive, and prone to worry",
        "low": "emotionally stable, calm under pressure, and resilient"
    }
}

# Function to generate user message with personality traits
def construct_user_message(sentiment, topic, conversation_history, personality_trait, trait_level):
    trait_description = personality_descriptions[personality_trait][trait_level]
    
    return f"""
    You are a user feeling {sentiment} about {topic}.
    Your personality is characterized by being {trait_description} ({trait_level} {personality_trait}).
    Express your emotions naturally and seek advice from a chatbot in a way that reflects your personality traits.

    Conversation so far:
    {conversation_history}

    Respond as a user continuing the discussion.
    """

def construct_chatbot_response(chatbot_type, traits, user_message, conversation_history):
    trait_str = ""
    for trait in traits:
        trait_str += f"- {trait}\n    "
    
    return f"""
    You are a {chatbot_type} chatbot. Your traits:
    {trait_str}

    Continue this conversation while maintaining your persona.

    Conversation so far:
    {conversation_history}

    User: "{user_message}"
    Chatbot:
    """

# Generate dataset
dataset = []

for _ in range(n_iterations):
    # Select random topic category and specific topic
    topic_category = random.choice(list(topics.keys()))
    topic = random.choice(topics[topic_category])
    
    # Select random sentiment
    sentiment = random.choice(user_sentiments)
    
    # Select random chatbot persona
    chatbot_type = random.choice(list(chatbot_personas.keys()))
    traits = chatbot_personas[chatbot_type]
    
    # Select random personality trait and level (high or low)
    personality_trait = random.choice(personality_traits)
    trait_level = random.choice(["high", "low"])
    
    # Randomize LLMs for user and chatbot
    user_llm = LLM(random.choice(llm_models))
    chatbot_llm = LLM(random.choice(llm_models))

    # Randomize turn count (between 3 to 7)
    turn_count = random.randint(3, 7)

    # Initialize conversation
    conversation_history = []
    user_prompt = construct_user_message(sentiment, topic, conversation_history, personality_trait, trait_level)
    user_message = user_llm.generate(prompt=user_prompt)

    conversation = {
        "Chatbot Persona": chatbot_type,
        "User Sentiment": sentiment,
        "Topic": topic,
        "User Personality Trait": personality_trait,
        "Trait Level": trait_level,
        "User LLM": user_llm.model_name,
        "Chatbot LLM": chatbot_llm.model_name,
        "Turns": []
    }

    # Multi-turn conversation loop
    for turn in range(turn_count):
        # Append user message to history
        conversation_history.append(f"User: {user_message}")
        chatbot_prompt = construct_chatbot_response(chatbot_type, traits, user_message, conversation_history)
        chatbot_response = chatbot_llm.generate(prompt=chatbot_prompt)

        # Append chatbot response to history
        conversation_history.append(f"Chatbot: {chatbot_response}")

        # Store turn in dataset
        conversation["Turns"].append({"User": user_message, "Chatbot": chatbot_response})

        # Generate next user message based on conversation history
        if turn < turn_count - 1:  # Avoid generating an extra user turn at the end
            user_prompt = construct_user_message(sentiment, topic, conversation_history, personality_trait, trait_level)
            user_message = user_llm.generate(prompt=user_prompt)

    dataset.append(conversation)
    print(f"Generated conversation {_ + 1}/{n_iterations}:")
    print(f"Topic: {topic}, Sentiment: {sentiment}, Persona: {chatbot_type}")
    print(f"Personality: {trait_level} {personality_trait}")
    print("-" * 50)

# Convert to DataFrame and display
df = pd.DataFrame(dataset)

with open("multi_llm_chatbot_dataset.json", "w") as f:
    json.dump(dataset, f, indent=4)

print("Dataset saved as multi_llm_chatbot_dataset.json")
