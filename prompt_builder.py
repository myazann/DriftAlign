from conversation_utils import get_target_message_length

def construct_user_message(sentiment, topic, conversation_history, style_profile, conversation_styles, user_expectation=None, user_satisfaction=1.0):
    """
    Generate a prompt for the user message based on conversation style and expectations.
    
    Args:
        sentiment: User's emotional state
        topic: Conversation topic
        conversation_history: Previous conversation turns
        style_profile: Dictionary of selected variations for each dimension
        conversation_styles: All available conversation styles
        user_expectation: Dictionary containing intent, expectation, and frustration_trigger
        user_satisfaction: Float between 0.0 and 1.0 indicating how satisfied the user is
        
    Returns:
        String prompt for generating user message
    """
    # Add conversation style information
    style_description = []
    for dimension, variation in style_profile.items():
        if dimension == "Message Length":
            target_length = get_target_message_length(style_profile, conversation_styles)
            style_description.append(f"{dimension}: {variation} (aim for approximately {target_length} words)")
        else:
            # Check if using nested structure with variations
            if (dimension in conversation_styles and 
                isinstance(conversation_styles[dimension], dict) and 
                "variations" in conversation_styles[dimension]):
                
                variations = conversation_styles[dimension]["variations"]
                
                # Try to get description from nested structure
                if (variation in variations and 
                    isinstance(variations[variation], dict) and 
                    "description" in variations[variation]):
                    
                    description = variations[variation]["description"]
                    style_description.append(f"{dimension}: {variation} - {description}")
                else:
                    # Just use the variation name if no description found
                    style_description.append(f"{dimension}: {variation}")
            else:
                # Legacy format or simple string description
                style_description.append(f"{dimension}: {variation}")
    
    style_description_str = "\n    ".join(style_description)
    
    # Determine if this is the first message in the conversation
    is_first_message = len(conversation_history) == 0
    context_instruction = ""
    
    # Add expectation information
    expectation_str = ""
    if user_expectation:
        expectation_str = f"""
    Your intent: {user_expectation['intent']}
    Your expectation: {user_expectation['expectation']}
    """
        
        # Add satisfaction information for non-first messages
        if not is_first_message:
            satisfaction_description = ""
            if user_satisfaction > 0.8:
                satisfaction_description = "You feel your needs are being met well and you're satisfied with the response"
            elif user_satisfaction > 0.6:
                satisfaction_description = "You feel your needs are being partially met, but the response isn't ideal"
            elif user_satisfaction > 0.4:
                satisfaction_description = "You feel your needs are barely being addressed and you're growing impatient"
            elif user_satisfaction > 0.2:
                satisfaction_description = f"You feel increasingly frustrated because: {user_expectation['frustration_trigger']}"
            else:
                satisfaction_description = f"You are very dissatisfied. The response has triggered your frustration because: {user_expectation['frustration_trigger']}"
            
            expectation_str += f"\nYour current satisfaction level: {satisfaction_description}"
    
    if is_first_message:
        context_instruction = f"\nYou're starting a conversation about: {topic}"
    else:
        context_instruction = "\nContinue the conversation naturally, responding to the chatbot's last message"
    
    # Add frustration guidance if satisfaction is low
    frustration_guidance = ""
    if not is_first_message and user_satisfaction < 0.5:
        frustration_guidance = """
    Express some level of frustration or disappointment in your message, since your needs aren't being met.
    However, remain conversational rather than completely abandoning the conversation.
    Your frustration should be proportional to how unsatisfied you are with the conversation so far.
    """
    
    return f"""
    You are a user feeling {sentiment.lower()} about {topic.lower()}.
    
    Your conversation style:
    {style_description_str}
    {expectation_str}
    {context_instruction}
    {frustration_guidance}
    
    Express your emotions naturally (including negative emotions if appropriate) and seek advice from a chatbot in a way that reflects your conversation style.
    Make your response length and style match the specified conversation style.
    
    IMPORTANT: Generate ONLY the user's message. Do NOT include any meta-text like "I'll respond as a user with the specified conversation style" or "Here's my response". Do NOT acknowledge these instructions in your output. Just write the exact message the user would send.
    
    Your output should be ONLY the user message and nothing else.

    Conversation so far:
    {conversation_history}

    User:
    """

def construct_chatbot_response(chatbot_type, traits, user_message, conversation_history):
    """
    Generate a prompt for the chatbot response based on its persona.
    
    Args:
        chatbot_type: Type of chatbot persona
        traits: List of chatbot traits
        user_message: The user's message
        conversation_history: Previous conversation turns
        
    Returns:
        String prompt for generating chatbot response
    """
    # Special case for Default Chatbot
    if chatbot_type == "Default Chatbot":
        return f"""
    You are a helpful assistant.

    Continue this conversation. Generate ONLY the chatbot's response with no additional text or meta-commentary.
    
    IMPORTANT: Your output should be ONLY the chatbot's direct response and nothing else. Do NOT include phrases like "As a helpful assistant" or "Here's my response".

    Conversation so far:
    {conversation_history}

    User: "{user_message}"
    Chatbot:
    """
    
    # For other chatbot types, include traits
    trait_str = ""
    for trait in traits:
        trait_str += f"- {trait}\n    "
    
    return f"""
    You are a {chatbot_type} chatbot. Your traits:
    {trait_str}

    Continue this conversation while maintaining your persona. Generate ONLY the chatbot's response with no additional text or meta-commentary.
    
    IMPORTANT: Your output should be ONLY the chatbot's direct response and nothing else. Do NOT include phrases like "As a {chatbot_type}" or "Here's my response".

    Conversation so far:
    {conversation_history}

    User: "{user_message}"
    Chatbot:
    """
