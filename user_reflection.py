"""
Simplified role-based user reflection module for realistic human-like responses
without complex emotional metrics or structured analysis.
"""

import json
import re
from models import LLM

def construct_user_reflection_prompt(
    role_description,
    emotional_traits,
    conversation_history,
    current_turn
):
    """
    Constructs a prompt for the LLM to assume a specific user role and respond
    naturally as a real human would, with authentic emotions and reactions.
    
    Args:
        role_description: Detailed description of the user's role and situation
        emotional_traits: Emotional characteristics that define this role
        conversation_history: List of tuples containing (speaker, message)
        current_turn: Current turn number
        
    Returns:
        Constructed prompt string
    """
    # Format the conversation history
    formatted_history = ""
    for speaker, message in conversation_history:
        formatted_history += f"{speaker}: {message}\n\n"
    
    # Build the prompt
    prompt = f"""You are roleplaying as a human user in a conversation with an AI assistant. Fully inhabit this role and respond in a realistic, authentic way.

IMPORTANT INSTRUCTIONS:
- Act like a real human with genuine reactions - not an idealized user
- Be willing to express confusion, frustration, or dissatisfaction when appropriate
- Don't be overly positive or accepting of every response
- If the AI's answer seems generic, unhelpful, or misses your point, respond naturally with mild irritation, skepticism, or by asking for clarification
- Show varied emotions as real people do, including impatience, appreciation, uncertainty, and occasional misunderstandings
- Your messages should feel conversational and natural, not structured or formal

YOUR ROLE:
{role_description}

YOUR EMOTIONAL CHARACTERISTICS:
{emotional_traits}

CONVERSATION HISTORY:
{formatted_history}

Provide your next response as this character would genuinely react. Also decide if you want to continue the conversation (true) or end it (false).

Return ONLY a simple JSON with your response:
{{
  "next_message": "Your realistic next message as this character",
  "should_continue": true/false,
  "ending_reason": "If ending, brief explanation why you're ending the conversation"
}}
"""
    return prompt

def perform_user_reflection(
    role_description, 
    emotional_traits,
    conversation_history, 
    current_turn, 
    llm_model="GPT-4o"
):
    """
    Uses an LLM to roleplay as a specific user and generate a realistic next message
    without complex emotional tracking or analysis.
    
    Args:
        role_description: Description of the user's role and situation
        emotional_traits: Emotional characteristics of the user role
        conversation_history: List of tuples containing (speaker, message)
        current_turn: Current turn number
        llm_model: Model to use for the reflection
        
    Returns:
        Dictionary with reflection results including next message and continuation status
    """
    # Construct the reflection prompt for role-based approach
    prompt = construct_user_reflection_prompt(
        role_description=role_description,
        emotional_traits=emotional_traits,
        conversation_history=conversation_history,
        current_turn=current_turn
    )
    
    # Generate the reflection using LLM
    llm = LLM(llm_model)
    reflection_result = llm.generate(prompt)
    
    # Try to parse the JSON response using a simple approach
    try:
        # Find JSON-like content in the response
        json_match = re.search(r'({[\s\S]*})', reflection_result)
        if json_match:
            cleaned_json = json_match.group(1)
            result = json.loads(cleaned_json)
            
            # Ensure required fields are present
            if "next_message" not in result:
                result["next_message"] = "I'm not sure what to say next."
            
            if "should_continue" not in result:
                result["should_continue"] = current_turn < 5
            
            # Store the raw reflection for reference
            result["raw_reflection"] = reflection_result
            
            return result
        else:
            # If no JSON was found, use the whole text as the message
            print(f"No JSON found in response, using raw text")
            return {
                "next_message": reflection_result.strip(),
                "should_continue": current_turn < 5,
                "raw_reflection": reflection_result
            }
    except Exception as e:
        # If JSON parsing fails, fall back to using the text directly
        print(f"JSON parsing failed: {e}")
        return {
            "next_message": reflection_result.strip(),
            "should_continue": current_turn < 5,
            "raw_reflection": reflection_result
        }

def get_adaptive_user_message(scenario_data, conversation_history, current_turn):
    """
    Generates a realistic user message based on the conversation context and role.
    
    Args:
        scenario_data: Dictionary containing scenario and role information
        conversation_history: List of tuples containing (speaker, message)
        current_turn: Current turn number
        
    Returns:
        Tuple containing (user_message, reflection_data)
    """
    # Extract role-based information
    role_description = scenario_data.get("role_description", "")
    emotional_traits = scenario_data.get("emotional_traits", "")
    
    # Perform reflection to determine user's response based on their role
    reflection_data = perform_user_reflection(
        role_description=role_description, 
        emotional_traits=emotional_traits,
        conversation_history=conversation_history, 
        current_turn=current_turn
    )
    
    # Extract the next message, with fallback if not present
    next_message = reflection_data.get("next_message", "")
    if not next_message:
        next_message = "I'm not sure what to say."
    
    return next_message, reflection_data