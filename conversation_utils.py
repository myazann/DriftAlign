import random
import json
import os
import time
from pathlib import Path
from datetime import datetime
import re

from prompts import construct_satisfaction_evaluation_prompt
from models import LLM

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
                            weights.append(0.5)  # 50% chance
                        elif variant == "short":
                            weights.append(0.35)  # 35% chance
                        elif variant == "medium":
                            weights.append(0.1)  # 15% chance
                        elif variant == "long":
                            weights.append(0.05)  # 10% chance
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

def evaluate_satisfaction_with_llm(conversation_history, user_expectation, turn_index, llm_model="GPT-4o"):
    """
    Evaluate user satisfaction using an LLM to analyze how well the chatbot response
    meets the user's expectations.
    
    Args:
        conversation_history: List of tuples of (speaker, message)
        user_expectation: Dictionary containing intent and expectation
        turn_index: The current turn index in the conversation
        llm_model: The LLM model to use for evaluation
        
    Returns:
        Tuple of (satisfaction_score, explanation)
    """
    if len(conversation_history) < 2:
        return 1.0, "Initial satisfaction is perfect"
    
    # Get the most recent user message and chatbot response
    last_user_index = -2  # Second-to-last message (user)
    last_chatbot_index = -1  # Last message (chatbot)
    
    if conversation_history[last_user_index][0] != "User" or conversation_history[last_chatbot_index][0] != "Chatbot":
        # Something is wrong with the conversation history format
        return 0.7, "Unable to properly evaluate conversation"
    
    user_message = conversation_history[last_user_index][1]
    chatbot_response = conversation_history[last_chatbot_index][1]
    
    # Create evaluation prompt
    evaluation_prompt = construct_satisfaction_evaluation_prompt(
        user_message=user_message,
        chatbot_response=chatbot_response,
        user_expectation=user_expectation,
        turn_index=turn_index
    )
    
    # Use LLM to evaluate
    llm = LLM(llm_model)
    evaluation_result = llm.generate(evaluation_prompt)
    
    try:
        # Clean up the response to ensure it's valid JSON
        # First, find the start and end of JSON content
        json_start = evaluation_result.find('{')
        json_end = evaluation_result.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            # Extract just the JSON part
            json_content = evaluation_result[json_start:json_end]
            
            # Parse the JSON result
            result = json.loads(json_content)
            satisfaction_score = float(result.get("satisfaction_score", 0.7))
            explanation = result.get("explanation", "No explanation provided")
            
            # Ensure satisfaction is within bounds
            satisfaction_score = max(0.05, min(0.95, satisfaction_score))
            
            # Store the explanation in the conversation history
            conversation_history[-1] = (conversation_history[-1][0], conversation_history[-1][1], explanation)
            
            return satisfaction_score, explanation
        else:
            raise ValueError("Could not find valid JSON content in the response")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error parsing LLM evaluation: {e}")
        print(f"Raw response: {evaluation_result}")
        
        # Fallback to a default satisfaction score
        return 0.7, "Error in satisfaction evaluation, using default score"

def calculate_user_satisfaction(conversation_history, user_expectation, turn_index):
    """
    Calculate user satisfaction level based on how well the chatbot is meeting expectations.
    
    Args:
        conversation_history: List of tuples of (speaker, message)
        user_expectation: Dictionary containing intent and expectation
        turn_index: Current turn index
        
    Returns:
        Tuple of (satisfaction_score, explanation)
    """
    # Use LLM-based satisfaction evaluation
    satisfaction, explanation = evaluate_satisfaction_with_llm(
        conversation_history, 
        user_expectation, 
        turn_index
    )
    
    return satisfaction, explanation

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
        'conversation_styles': load_json_file(base_dir / "conversation_styles.json"),
        'chatbot_personas': load_json_file(base_dir / "chatbot_personas.json")
    }

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
    Save the generated dataset to a JSON file with timestamp in the generations folder.
    
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
    
    # Ensure generations directory exists
    generations_dir = "generations"
    os.makedirs(generations_dir, exist_ok=True)
    
    # Create path in generations directory
    output_file = os.path.join(generations_dir, f"{base_name}_{timestamp}{ext}")
    
    # Save the dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Dataset saved to {output_file}")
