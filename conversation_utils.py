import random
import json

def load_scenarios():
    """Load role-based scenarios from the JSON file."""
    with open("seed_data/scenarios.json", "r") as f:
        scenarios = json.load(f)
        return scenarios

def load_chatbot_personas():
    """Load chatbot personas from the JSON file."""
    with open("seed_data/chatbot_personas.json", "r") as f:
        personas = json.load(f)
        return personas

def select_chatbot_persona():
    """
    Selects a chatbot persona with weighted probability based on weights in the JSON file.
    
    Returns:
        Tuple of (selected_persona_type, persona_traits)
    """
    # Load personas
    personas = load_chatbot_personas()
    
    # Extract persona types and their weights
    persona_types = list(personas.keys())
    weights = [personas[p_type].get("weight", 1.0) for p_type in persona_types]
        
    # Select a persona type based on weights
    selected_persona_type = random.choices(persona_types, weights=weights, k=1)[0]
    
    # Get the traits for the selected persona
    persona_traits = personas[selected_persona_type].get("traits", [])
    
    return selected_persona_type, persona_traits

def select_conversation_style():
    """
    Selects a conversation style randomly based on weights in the conversation_styles.json.
    
    Returns:
        Dictionary containing the selected style attributes
    """
    with open("seed_data/conversation_styles.json", "r") as f:
        conversation_styles = json.load(f)
        
    # Randomly select style attributes
    selected_styles = {}
    for style_category, style_data in conversation_styles.items():
        variations = style_data.get("variations", {})
        # Select a variation based on weights
        weights = [v.get("weight", 1.0) for k, v in variations.items()]
        variation_keys = list(variations.keys())
        selected_variation = random.choices(variation_keys, weights=weights, k=1)[0]
        selected_styles[style_category] = {
            "type": selected_variation,
            "description": variations[selected_variation].get("description", "")
        }
        
        # Add min/max words if it's message length
        if style_category == "Message Length":
            selected_styles[style_category]["min_words"] = variations[selected_variation].get("min_words", 0)
            selected_styles[style_category]["max_words"] = variations[selected_variation].get("max_words", 100)
    
    return selected_styles

def format_style_instructions(selected_styles, for_initial_message=True):
    """
    Formats the style instructions based on selected styles.
    
    Args:
        selected_styles: Dictionary with selected style attributes
        for_initial_message: Whether formatting is for initial message or reflection
        
    Returns:
        Formatted style instruction string
    """
    style_instructions = ""
    for category, style in selected_styles.items():
        style_type = style.get("type", "")
        description = style.get("description", "")
        
        if category == "Message Length" and not for_initial_message:
            # For reflection, provide more flexibility with message length
            style_instructions += f"- {category}: Try to generally follow the {style_type} style ({description}), but feel free to use more words if needed to express yourself naturally, especially if expressing frustration or strong emotions\n"
        elif category == "Message Length":
            min_words = style.get("min_words", 0)
            max_words = style.get("max_words", 100)
            style_instructions += f"- {category}: {style_type} ({min_words}-{max_words} words) - {description}\n"
        else:
            style_instructions += f"- {category}: {style_type} - {description}\n"
            
    return style_instructions