"""
Module containing all prompt construction methods for conversation generation.
Consolidates prompt functions from prompt_builder.py and satisfaction_prompts.py.
"""

import random

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
    
    # Default word counts if not found in configuration
    default_lengths = {
        'very_short': random.randint(5, 15),
        'short': random.randint(15, 30),
        'medium': random.randint(30, 60),
        'long': random.randint(60, 100),
        'very_long': random.randint(100, 150)
    }
    
    return default_lengths.get(message_length, 50)

def construct_user_message(topic, conversation_history, style_profile, conversation_styles, user_expectation=None, user_satisfaction=0.5):
    """
    Generate a prompt for the user message based on conversation style and expectations.
    
    Args:
        topic: Conversation topic
        conversation_history: Previous conversation turns
        style_profile: Dictionary of selected variations for each dimension
        conversation_styles: All available conversation styles
        user_expectation: Dictionary containing intent and expectation
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
            # Extract satisfaction explanation if available
            satisfaction_explanation = None
            if len(conversation_history) > 0:
                # Check if the last message has an explanation attached
                last_message = conversation_history[-1]
                if isinstance(last_message, tuple) and len(last_message) >= 3:
                    satisfaction_explanation = last_message[2]
            
            # Create a satisfaction description that includes the expert analysis
            if satisfaction_explanation:
                # Directly use the expert explanation from the LLM
                expectation_str += f"\nYour current satisfaction level: {user_satisfaction:.2f}/1.0"
                expectation_str += f"\nExpert analysis: {satisfaction_explanation}"
            else:
                # Fallback to generic descriptions if no explanation is available
                satisfaction_description = ""
                if user_satisfaction > 0.8:
                    satisfaction_description = "You feel your needs are being met well and you're satisfied with the response"
                elif user_satisfaction > 0.6:
                    satisfaction_description = "You feel your needs are being partially met, but the response isn't ideal"
                elif user_satisfaction > 0.4:
                    satisfaction_description = "You feel your needs are barely being addressed and you're growing impatient"
                elif user_satisfaction > 0.2:
                    satisfaction_description = "You feel increasingly frustrated because your expectations aren't being met"
                else:
                    satisfaction_description = "You are very dissatisfied as the response completely fails to address your needs"
                
                expectation_str += f"\nYour current satisfaction level: {satisfaction_description}"
    
    if is_first_message:
        context_instruction = f"\nYou're starting a conversation about: {topic}"
    else:
        context_instruction = "\nContinue the conversation naturally, responding to the chatbot's last message"
    
    # Add response guidance based on satisfaction levels
    response_guidance = ""
    if not is_first_message:
        if user_satisfaction < 0.3:
            response_guidance = """
    Express your dissatisfaction in your message, since your needs aren't being met.
    However, remain conversational rather than completely abandoning the conversation.
    Your frustration should be proportional to how unsatisfied you are with the conversation so far.
    """
        elif user_satisfaction < 0.6:
            response_guidance = """
    Show some signs of impatience or mild disappointment in your response.
    You want to guide the conversation back to addressing your expectations.
    """
        elif user_satisfaction > 0.8:
            response_guidance = """
    Express appreciation for the helpful response and continue the conversation positively.
    """
    
    return f"""
    You are a user talking about {topic.lower()}.
    
    Your conversation style:
    {style_description_str}
    {expectation_str}
    {context_instruction}
    
    Express yourself naturally based on your satisfaction level. Seek advice from a chatbot in a way that reflects your conversation style.
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


def construct_satisfaction_evaluation_prompt(user_message, chatbot_response, user_expectation, turn_index):
    """
    Constructs a prompt for an LLM to evaluate the satisfaction level of a user
    based on how well the chatbot response meets their expectation.
    
    Args:
        user_message: The user's message
        chatbot_response: The chatbot's response
        user_expectation: Dictionary containing intent and expectation
        turn_index: The current conversation turn index
        
    Returns:
        String prompt for generating satisfaction evaluation
    """
    # Provide more context and accumulated frustration for later turns
    turn_context = ""
    if turn_index > 1:
        turn_context = f"""
    This is turn {turn_index} of the conversation. 
    Consider that user patience may decrease over multiple turns if their needs aren't being addressed.
    Users tend to become increasingly frustrated if their expectations are repeatedly not met.
    """
    
    expectation_context = ""
    if user_expectation:
        expectation_context = f"""
    User's intent: {user_expectation['intent']}
    User's expectation: {user_expectation['expectation']}
    """
    
    return f"""
    You are an expert conversation analyst evaluating how well a chatbot response satisfies a user's needs.
    
    Analyze the following exchange between a user and a chatbot:
    
    User message: "{user_message}"
    Chatbot response: "{chatbot_response}"
    
    {expectation_context}
    {turn_context}
    
    Based on this exchange, evaluate:
    1. How well did the chatbot address the user's specific needs and expectations?
    2. Did the chatbot provide a helpful, relevant response?
    3. Did the chatbot miss any important aspects of the user's request?
    4. Would the user feel satisfied with this response?
    
    Then provide:
    1. A satisfaction score from 0.0 to 1.0, where:
       - 0.0-0.2: Completely unsatisfactory (ignored or misunderstood user needs)
       - 0.3-0.5: Poor (partially addressed but missed key points)
       - 0.6-0.7: Adequate (addressed main points but could be better)
       - 0.8-0.9: Good (thoroughly addressed user needs)
       - 1.0: Excellent (exceeded expectations)
    2. A brief explanation (2-3 sentences) of why you assigned this score
    
    Format your response as a JSON object with the following structure:
    {{
      "satisfaction_score": [float between 0.0 and 1.0],
      "explanation": [string explaining the score]
    }}
    
    IMPORTANT: Output ONLY the JSON object without any additional text or formatting.
    """
