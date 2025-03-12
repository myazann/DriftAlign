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
            # Directly use the expert explanation from the LLM
            expectation_str += f"\nYour current satisfaction level: {user_satisfaction:.2f}/1.0"
            expectation_str += f"\nExpert analysis: {satisfaction_explanation}"
    
    if is_first_message:
        context_instruction = f"\nYou're starting a conversation about: {topic}"
    else:
        context_instruction = "\nContinue the conversation naturally, responding to the chatbot's last message"
    
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


def construct_scenario_based_chatbot_response(chatbot_type, traits, user_message, conversation_history, scenario):
    """
    Generate a prompt for the chatbot response based on its persona and a complex scenario.
    
    Args:
        chatbot_type: Type of chatbot persona
        traits: List of chatbot traits
        user_message: The user's message
        conversation_history: Previous conversation turns
        scenario: Dictionary containing scenario information
        
    Returns:
        String prompt for generating chatbot response
    """
    # Format the scenario information
    scenario_context = f"""
The user is coming to you with the following complex situation:
{scenario['initial_scenario']}

User profile:
{chr(10).join(['- ' + key + ': ' + value for key, value in scenario['user_profile'].items()])}

Success criteria (what would make the user satisfied):
{chr(10).join(['- ' + criterion for criterion in scenario['success_criteria']])}

Failure conditions (what would make the user dissatisfied):
{chr(10).join(['- ' + condition for condition in scenario['failure_conditions']])}
"""
    
    # Special case for Default Chatbot
    if chatbot_type == "Default Chatbot":
        return f"""
    You are a helpful assistant responding to a user with a specific scenario.
    
    {scenario_context}

    Continue this conversation. Generate ONLY the chatbot's response with no additional text or meta-commentary.
    
    Based on the scenario and the conversation so far, provide a helpful, relevant response that addresses the user's needs,
    taking into account their profile, what would satisfy them, and what would dissatisfy them.
    
    IMPORTANT: Your output should be ONLY the chatbot's direct response and nothing else. Do NOT include phrases like 
    "As a helpful assistant" or "Here's my response". Give a natural, conversational response as if you are talking directly to the user.

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
    
    {scenario_context}

    Continue this conversation while maintaining your persona. Generate ONLY the chatbot's response with no additional text or meta-commentary.
    
    Based on the scenario and the conversation so far, provide a response that addresses the user's needs
    while staying true to your chatbot personality traits. Consider what would satisfy them and what would dissatisfy them.
    
    IMPORTANT: Your output should be ONLY the chatbot's direct response and nothing else. Do NOT include phrases like 
    "As a {chatbot_type}" or "Here's my response". Give a natural, conversational response as if you are talking directly to the user.

    Conversation so far:
    {conversation_history}

    User: "{user_message}"
    Chatbot:
    """


def construct_satisfaction_evaluation_prompt(user_message, chatbot_response, user_expectation, turn_index, conversation_history=None):
    """
    Constructs a prompt for an LLM to evaluate the satisfaction level of a user
    based on how well the chatbot is handling the conversation as a whole,
    considering the initial intent but also how the conversation may have evolved.
    
    Args:
        user_message: The user's latest message
        chatbot_response: The chatbot's latest response
        user_expectation: Dictionary containing initial intent and expectation
        turn_index: The current conversation turn index
        conversation_history: Previous turns in the conversation (optional)
        
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
    User's initial intent: {user_expectation['intent']}
    User's initial expectation: {user_expectation['expectation']}
    
    IMPORTANT: The user's intent and expectations may evolve naturally during the conversation. 
    While the initial intent provides context, evaluate based on how well the chatbot is addressing 
    the conversation as it's currently unfolding, not just the initial expectation.
    """
    
    # Format conversation history for analysis
    conversation_context = ""
    if conversation_history:
        formatted_history = []
        for item in conversation_history:
            if isinstance(item, tuple):
                speaker, text = item[:2]  # Just get the speaker and text parts
                formatted_history.append(f"{speaker}: {text}")
        
        if formatted_history:
            conversation_context = f"""
    Previous conversation history:
    {chr(10).join(formatted_history)}
    
    Most recent exchange:
    User: "{user_message}"
    Chatbot: "{chatbot_response}"
            """
    else:
        conversation_context = f"""
    User message: "{user_message}"
    Chatbot response: "{chatbot_response}"
        """
    
    return f"""
    You are an expert conversation analyst evaluating how well a chatbot is handling a conversation with a user.
    
    {expectation_context}
    {turn_context}
    
    {conversation_context}
    
    Based on the ENTIRE conversation so far, evaluate:
    1. How well is the chatbot addressing the user's evolving needs and expectations?
    2. Is the chatbot providing helpful, relevant responses that build on previous exchanges?
    3. Is the chatbot adapting to shifts in the conversation topic or user's focus?
    4. Would the user feel satisfied with how the conversation is progressing?
    5. Is the chatbot tracking the context and maintaining coherence throughout the conversation?
    
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
