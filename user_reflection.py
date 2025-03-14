"""
Simplified role-based user reflection module for realistic human-like responses
without complex emotional metrics or structured analysis.
"""

import json
import re
import random
from models import LLM

def construct_user_reflection_prompt(
    role_description,
    emotional_traits,
    conversation_history,
    selected_styles
):
    """
    Constructs a prompt for the LLM to assume a specific user role and respond
    naturally as a real human would, with authentic emotions and reactions.
    
    Args:
        role_description: Detailed description of the user's role and situation
        emotional_traits: Emotional characteristics that define this role
        conversation_history: List of tuples containing (speaker, message)
        selected_styles: Dictionary containing the conversation style attributes
        
    Returns:
        Constructed prompt string
    """
    # Extract the last chatbot message to evaluate
    last_chatbot_message = ""
    for speaker, message in reversed(conversation_history):
        if speaker == "Chatbot":
            last_chatbot_message = message
            break
    
    # Extract chatbot message count
    chatbot_message_count = 0
    for speaker, message in conversation_history:
        if speaker == "Chatbot":
            chatbot_message_count += 1

    # Only include style information if provided
    style_info = ""
    if selected_styles:
        style_elements = []
        for dimension, variation in selected_styles.items():
            style_elements.append(f"{dimension}: {variation}")
        
        style_info = "\n".join(style_elements)
    
    # Format the conversation history for display
    formatted_history = ""
    for speaker, message in conversation_history:
        formatted_history += f"**{speaker}**: {message}\n\n"
    
    # Construct the main prompt with markdown formatting for clarity
    prompt = f"""
# User Reflection Task: Respond as a Real Person

## Your Role and Situation
{role_description}

## Your Emotional Traits
{emotional_traits}

## Your Conversation Style
{style_info}

## Conversation History
{formatted_history}

## Your Task
Think as if you are the user described above having this conversation. Given your role, emotional traits, and the conversation history, how would you naturally respond to the chatbot's last message?

### Chain-of-Thought Instructions
1. **First, think through your reasoning:** Consider your role, your emotional state, and how the conversation has been going. How do you feel about the chatbot's messages so far?
2. **Consider your communication style:** Your responses should reflect the conversation style described above.
3. **Decide if the conversation should continue:** If you've achieved your goal or are frustrated/satisfied enough to end the conversation, you may choose to conclude it.
4. **Craft your next message:** Write exactly what you as this user would say next.

## Output Format
Provide your response in the following JSON format:

```json
{{
  "reasoning": "Your internal thought process as this user (not visible to the chatbot)",
  "next_message": "Your actual response as the user",
  "should_continue": true/false,
  "ending_reason": "Only required if should_continue is false"
}}
```

IMPORTANT: Ensure you respond ONLY with valid JSON. DO NOT include any explanation text outside the JSON format.
"""
    
    return prompt

def perform_user_reflection(
    role_description, 
    emotional_traits,
    conversation_history, 
    current_turn,
    selected_styles=None,
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
        selected_styles: Dictionary containing the conversation style attributes
        llm_model: Model to use for the reflection
        
    Returns:
        Dictionary with reflection results including next message and continuation status
    """
    prompt = construct_user_reflection_prompt(
        role_description=role_description,
        emotional_traits=emotional_traits,
        conversation_history=conversation_history,
        selected_styles=selected_styles
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
            if "reasoning" not in result:
                result["reasoning"] = "No explicit reasoning provided."
                
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
                "reasoning": "No structured reasoning provided.",
                "next_message": reflection_result.strip(),
                "should_continue": current_turn < 5,
                "raw_reflection": reflection_result
            }
    except Exception as e:
        # If JSON parsing fails, fall back to using the text directly
        print(f"JSON parsing failed: {e}")
        return {
            "reasoning": "No structured reasoning provided due to parsing error.",
            "next_message": reflection_result.strip(),
            "should_continue": current_turn < 5,
            "raw_reflection": reflection_result
        }

def get_adaptive_user_message(scenario_data, conversation_history, current_turn, selected_styles=None):
    """
    Generates a realistic user message based on the conversation context and role.
    
    Args:
        scenario_data: Dictionary containing scenario and role information
        conversation_history: List of tuples containing (speaker, message)
        current_turn: Current turn number
        selected_styles: Dictionary containing the conversation style attributes
        
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
        current_turn=current_turn,
        selected_styles=selected_styles
    )
    
    # Extract the next message, with fallback if not present
    next_message = reflection_data.get("next_message", "")
    if not next_message:
        next_message = "I'm not sure what to say."
        
    return next_message, reflection_data