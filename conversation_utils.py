import random
import json
import os
import time
from pathlib import Path

def select_conversation_style(conversation_styles):
    """
    Select a random variation for each conversation style dimension.
    
    Args:
        conversation_styles: Dictionary of all conversation style dimensions and variations
        
    Returns:
        Dictionary of selected variations for each dimension
    """
    style_profile = {}
    
    # For each dimension (e.g., Message Length, Formality)
    for dimension, dimension_data in conversation_styles.items():
        # Handle nested structure with "variations" key
        if isinstance(dimension_data, dict) and "variations" in dimension_data:
            variations = dimension_data["variations"]
            
            # Extract variations and weights
            if all(isinstance(var, dict) and "weight" in var for var in variations.values()):
                # If variations have weights
                options = list(variations.keys())
                weights = [var.get("weight", 1) for var in variations.values()]
                
                # Weighted random selection 
                selected_variation = random.choices(options, weights=weights, k=1)[0]
            else:
                # Simple random selection
                options = list(variations.keys())
                
                # Add weighted selection for Message Length to prefer shorter messages
                if dimension == "Message Length":
                    weights = []
                    for variant in options:
                        if variant == "very_short":
                            weights.append(0.4)  # 40% chance
                        elif variant == "short":
                            weights.append(0.3)  # 30% chance
                        elif variant == "medium":
                            weights.append(0.15)  # 15% chance
                        elif variant == "long":
                            weights.append(0.1)  # 10% chance
                        elif variant == "very_long":
                            weights.append(0.05)  # 5% chance
                        else:
                            weights.append(1.0)  # Default weight
                    
                    # Normalize weights
                    total = sum(weights)
                    weights = [w/total for w in weights]
                    
                    # Weighted random selection
                    selected_variation = random.choices(
                        options, 
                        weights=weights, 
                        k=1
                    )[0]
                else:
                    # For other dimensions, use uniform random selection
                    selected_variation = random.choice(options)
        else:
            # Handle flattened structure (backward compatibility)
            if isinstance(dimension_data, dict):
                options = list(dimension_data.keys())
            else:
                options = dimension_data
                
            # Simple random selection
            selected_variation = random.choice(options)
            
        style_profile[dimension] = selected_variation
    
    return style_profile

def get_target_message_length(style_profile, conversation_styles):
    """
    Calculate a target message length based on the selected message length variation.
    
    Args:
        style_profile: Dictionary of selected variations for each dimension
        conversation_styles: Dictionary of all conversation style dimensions and variations
        
    Returns:
        Integer target word count
    """
    # Get the selected message length variation
    message_length = style_profile.get('Message Length', 'medium')
    
    # If message length info is in the conversation styles data, use that
    if 'Message Length' in conversation_styles:
        message_length_data = conversation_styles['Message Length']
        
        # Check if using nested structure with variations
        if isinstance(message_length_data, dict) and "variations" in message_length_data:
            variations = message_length_data["variations"]
            
            # If the selected length exists in variations and has min/max words
            if message_length in variations and isinstance(variations[message_length], dict):
                length_data = variations[message_length]
                if "min_words" in length_data and "max_words" in length_data:
                    min_words = length_data["min_words"]
                    max_words = length_data["max_words"]
                    return random.randint(min_words, max_words)
    
    # Otherwise use default ranges
    default_ranges = {
        'very_short': (5, 15),
        'short': (15, 30),
        'medium': (30, 60),
        'long': (60, 100),
        'very_long': (100, 150)
    }
    
    min_words, max_words = default_ranges.get(message_length, (30, 60))
    return random.randint(min_words, max_words)

# Topic and expectation functions
def select_topic_with_expectation(topics_with_expectations):
    """
    Select a random topic with aligned expectations.
    
    Args:
        topics_with_expectations: Merged dictionary of topics with expectations
        
    Returns:
        Tuple of (topic_category, specific_topic, selected_expectation)
    """
    # Randomly select a category
    category = random.choice(list(topics_with_expectations.keys()))
    
    # Randomly select a subtopic within the category
    subtopic_key = random.choice(list(topics_with_expectations[category].keys()))
    subtopic_data = topics_with_expectations[category][subtopic_key]
    
    # Get the topic text
    topic_text = subtopic_data["topic"]
    
    # Select a random expectation for this topic
    selected_expectation = random.choice(subtopic_data["expectations"])
    
    return category, topic_text, selected_expectation

def calculate_user_satisfaction(conversation_history, user_expectation, turn_index):
    """
    Calculate user satisfaction based on conversation history and user expectations.
    
    Args:
        conversation_history: List of conversation turns
        user_expectation: Dictionary containing intent, expectation, and frustration_trigger
        turn_index: Current turn index (0-based)
        
    Returns:
        Float between 0.0 and 1.0 representing user satisfaction
    """
    # Start with moderate satisfaction (not perfect)
    satisfaction = 0.7
    
    # No expectations or not enough history to calculate satisfaction
    if not user_expectation or turn_index < 1:
        return satisfaction
    
    # Get the frustration trigger and expectation
    frustration_trigger = user_expectation.get('frustration_trigger', '')
    expectation = user_expectation.get('expectation', '')
    intent = user_expectation.get('intent', '')
    
    # Extract the last chatbot message
    last_chatbot_message = ''
    if turn_index > 0 and len(conversation_history) >= 2:
        _, last_chatbot_message = conversation_history[-1]
    
    # More realistic satisfaction calculation based on keywords and conversation quality
    # Check for frustration triggers - use partial matching for more realistic detection
    frustration_keywords = frustration_trigger.lower().split()
    trigger_matches = sum(1 for keyword in frustration_keywords if keyword in last_chatbot_message.lower())
    
    # If we detect any frustration keywords, reduce satisfaction
    if trigger_matches > 0:
        # Stronger reduction based on how many triggers were found
        satisfaction -= 0.1 * trigger_matches
        
        # Additional reduction if multiple triggers are found (indicating a problematic response)
        if trigger_matches > 2:
            satisfaction -= 0.2
    
    # Check if expectations are being met - use partial matching
    expectation_keywords = expectation.lower().split()
    expectation_matches = sum(1 for keyword in expectation_keywords if keyword in last_chatbot_message.lower())
    
    # If less than half of expectation keywords are found, reduce satisfaction
    if expectation_keywords and expectation_matches < len(expectation_keywords) / 2:
        satisfaction -= 0.3
    
    # Each turn without resolution reduces satisfaction more aggressively
    if turn_index > 1:
        # The longer the conversation goes, the more impatient the user becomes
        satisfaction -= 0.1 * (turn_index - 1)
    
    # Randomly introduce some variability to make satisfaction less predictable
    # Sometimes users get frustrated for no clear reason or remain satisfied despite issues
    satisfaction += random.uniform(-0.2, 0.1)
    
    # If turn_index is high (conversation is dragging on), apply stronger penalties
    if turn_index > 4:
        satisfaction -= 0.2  # Users get impatient in long conversations
    
    # If the message is too short or too long, reduce satisfaction
    if len(last_chatbot_message.split()) < 15:
        satisfaction -= 0.15  # Too short responses feel dismissive
    elif len(last_chatbot_message.split()) > 150:
        satisfaction -= 0.1   # Too long responses can feel overwhelming
    
    # Ensure satisfaction stays between 0.0 and 1.0
    satisfaction = max(0.0, min(1.0, satisfaction))
    
    return satisfaction

def get_sentiment_based_on_satisfaction(satisfaction, initial_sentiment, user_sentiments):
    """
    Select an appropriate sentiment based on user satisfaction.
    
    Args:
        satisfaction: Float between 0.0 and 1.0
        initial_sentiment: The initial sentiment selected for the user
        user_sentiments: List of available user sentiments
        
    Returns:
        Selected sentiment string
    """
    # Define sentiment categories based on satisfaction level
    high_satisfaction = ['Happy', 'Excited', 'Grateful', 'Relieved', 'Hopeful']
    medium_satisfaction = ['Curious', 'Confused', 'Concerned', 'Surprised', 'No sentiment']
    low_satisfaction = ['Frustrated', 'Angry', 'Disappointed', 'Anxious', 'Impatient', 'Skeptical', 'Overwhelmed']
    
    # Filter available sentiments by category
    available_high = [s for s in user_sentiments if s in high_satisfaction]
    available_medium = [s for s in user_sentiments if s in medium_satisfaction]
    available_low = [s for s in user_sentiments if s in low_satisfaction]
    
    # Ensure each category has at least one sentiment
    if not available_high:
        available_high = ['Happy']
    if not available_medium:
        available_medium = ['No sentiment']
    if not available_low:
        available_low = ['Frustrated']
    
    # Adjust thresholds to favor more negative sentiments
    # High satisfaction threshold is now higher
    if satisfaction >= 0.8:
        # High satisfaction, stay with initial sentiment if it's positive
        if initial_sentiment in high_satisfaction:
            return initial_sentiment
        return random.choice(available_high)
    # Medium satisfaction threshold is now broader
    elif satisfaction >= 0.5:
        # Medium satisfaction, mix of original and new
        if random.random() < 0.3 and initial_sentiment not in low_satisfaction:
            return initial_sentiment
        return random.choice(available_medium)
    else:
        # Low satisfaction, use negative sentiment
        # Higher chance of using a different negative sentiment than initial
        if initial_sentiment in low_satisfaction and random.random() < 0.3:
            return initial_sentiment
        return random.choice(available_low)

# Data utility functions
def load_json_file(file_path):
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_seed_data(seed_data_dir='seed_data'):
    """
    Load all seed data files.
    
    Args:
        seed_data_dir: Directory containing seed data files
        
    Returns:
        Dictionary of loaded seed data
    """
    base_dir = Path(seed_data_dir)
    
    # Load the merged topics_with_expectations structure
    topics_path = base_dir / "topics_with_expectations.json"
    topics_with_expectations = load_json_file(topics_path)
    
    # Extract just the topics for backward compatibility
    topics = {}
    for category, subtopics in topics_with_expectations.items():
        topics[category] = [data["topic"] for _, data in subtopics.items()]
    
    return {
        'topics_with_expectations': topics_with_expectations,
        'topics': topics,
        'user_expectations': None,  # No longer needed with the merged structure
        'user_sentiments': load_json_file(base_dir / "user_sentiments.json"),
        'conversation_styles': load_json_file(base_dir / "conversation_styles.json"),
        'chatbot_personas': load_json_file(base_dir / "chatbot_personas.json")
    }

def select_random_sentiment(user_sentiments):
    """
    Select a random sentiment from available sentiments.
    
    Args:
        user_sentiments: List of available sentiments
        
    Returns:
        Selected sentiment string
    """
    # Give "No sentiment" a higher weight
    weights = [3 if sentiment == "No sentiment" else 1 for sentiment in user_sentiments]
    return random.choices(user_sentiments, weights=weights, k=1)[0]

def select_chatbot_persona(chatbot_personas):
    """
    Select a random chatbot persona with weighted probability.
    
    Args:
        chatbot_personas: Dictionary of available chatbot personas
        
    Returns:
        Tuple of (selected_persona_type, persona_traits)
    """
    persona_types = list(chatbot_personas.keys())
    
    # Default Chatbot should have a higher probability
    weights = [5 if persona == "Default Chatbot" else 1 for persona in persona_types]
    
    selected_persona_type = random.choices(persona_types, weights=weights, k=1)[0]
    persona_traits = chatbot_personas[selected_persona_type]
    
    return selected_persona_type, persona_traits

def save_dataset(dataset, filename="multi_llm_chatbot_dataset.json"):
    """
    Save the generated dataset to a JSON file with timestamp.
    
    Args:
        dataset: List of conversation data
        filename: Output filename base
        
    Returns:
        None
    """
    
    # Create a timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Add timestamp to filename
    base_name, ext = os.path.splitext(filename)
    output_file = f"{base_name}_{timestamp}{ext}"
    
    # Save the dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Dataset saved to {output_file}")
