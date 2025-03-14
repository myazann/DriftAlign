"""
Simplified role-based user reflection module for realistic human-like responses
without complex emotional metrics or analysis.
"""

import json
import re
import random
from models import LLM

def construct_user_reflection_prompt(role_description, emotional_traits, conversation_history, adaptive_length_instruction, realistic_behavior_instructions, goal_alignment=""):
    """
    Constructs the prompt for generating user reflections.
    
    Args:
        role_description: Description of the user's role
        emotional_traits: Emotional characteristics of the user
        conversation_history: List of conversation turns
        adaptive_length_instruction: Instructions for message length
        realistic_behavior_instructions: Instructions for realistic behavior
        goal_alignment: Assessment of how well the chatbot's response aligns with user goals
    
    Returns:
        Formatted prompt string
    """
    # Convert conversation history to formatted string
    formatted_history = ""
    for i, (speaker, message) in enumerate(conversation_history):
        formatted_history += f"{speaker}: {message}\n\n"
    
    prompt = f"""
You are roleplaying as a user interacting with an AI chatbot. 

## Your Character
{role_description}

## Your Emotional Traits
{emotional_traits}

## Message Length Guidance
{adaptive_length_instruction}

## Realistic Human Behavior Guidelines
{realistic_behavior_instructions}

{goal_alignment}

## Conversation History
{formatted_history}

## Your Task
Think about how the character you're playing would naturally respond to the chatbot's most recent message.

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

def generate_realistic_behavior_instructions(current_turn):
    """
    Generates instructions for realistic human behavior in conversations with AI assistants.
    
    Args:
        current_turn: Current turn number
        
    Returns:
        String with realistic behavior instructions
    """
    
    instructions = [
        "**To make your responses more authentic and less artificial:**",
        
        # Less agreeability
        "- **Don't be overly agreeable with the chatbot.** Real users often push back, question, or disagree with AI suggestions.",
        
        # If chatbot is giving advice
        "- **When given advice:** It's natural to be somewhat skeptical or hesitant about implementing suggestions. You may express doubts, ask for clarification, or occasionally reject advice outright.",
        
        # Reduce thanking
        "- **Minimize unnecessary thanking.** Real users rarely thank chatbots for every response. Only express gratitude for exceptionally helpful information or when concluding a conversation. Otherwise, simply continue the conversation without acknowledgment.",
        
        # Add more realistic behaviors
        "- **Show impatience occasionally.** If the chatbot is being repetitive or not addressing your core concern, it's natural to express slight frustration or redirect them.",
        
        "- **Use shorter, more casual responses.** Real users often write brief, informal messages and don't always use complete sentences or perfect grammar.",
        
        # Add more realism based on context
        "- **Don't explain yourself too much.** Real users often state their needs directly without extensive backstory or justification for every response."
    ]
    
    # Add context-specific instructions
    if current_turn > 2:
        instructions.append("- **At this point in the conversation:** Users typically become more direct and goal-focused. You may skip pleasantries and get straight to the point.")
    
    return "\n".join(instructions)

def determine_adaptive_message_length(current_turn, selected_styles, last_chatbot_message):
    """
    Determines an appropriate message length based on conversation context.
    
    Args:
        current_turn: Current turn number in the conversation
        selected_styles: Dictionary containing the conversation style attributes
        last_chatbot_message: The most recent message from the chatbot
    
    Returns:
        String with message length instruction
    """
    # Get the user's baseline message length style from selected_styles
    baseline_length_style = "medium"
    baseline_min_words = 20
    baseline_max_words = 40
    
    if selected_styles and "Message Length" in selected_styles:
        style_type = selected_styles["Message Length"].get("type", "medium")
        baseline_length_style = style_type
        baseline_min_words = selected_styles["Message Length"].get("min_words", 20)
        baseline_max_words = selected_styles["Message Length"].get("max_words", 40)
    
    # First message is typically longer to explain the situation
    if current_turn == 1:
        # Make the first message longer regardless of the baseline style
        if baseline_length_style == "very_short":
            return "This is your first message, so it should be somewhat longer (15-30 words) to explain your situation clearly."
        elif baseline_length_style == "short":
            return "This is your first message, so it should be longer (25-45 words) to properly explain your situation and concerns."
        else:
            return "This is your first message, so you can be detailed (40-70 words) to fully explain your situation and concerns."
    
    # Check if the bot's last message requires a more detailed response
    question_indicators = ["?", "what do you think", "how do you feel", "can you explain", 
                         "tell me more", "could you share", "describe", "elaborate"]
    
    problem_indicators = ["sorry", "unfortunately", "issue", "problem", "error", "mistake", 
                         "difficult", "challenging", "trouble", "failed"]
    
    # Check if chatbot asked an important question
    important_question = any(indicator in last_chatbot_message.lower() for indicator in question_indicators)
    
    # Check if there's a problem to discuss
    has_problem = any(indicator in last_chatbot_message.lower() for indicator in problem_indicators)
    
    # Random chance to occasionally vary the message length
    random_variation = random.random() < 0.2
    
    # Default to shorter responses after the first message
    if current_turn > 1:
        # If it's a very important question or problem, provide a more detailed response
        if important_question or has_problem:
            if baseline_length_style == "very_short":
                return "The chatbot has asked an important question or identified a problem. Provide a more detailed response (15-25 words) than you normally would."
            elif baseline_length_style == "short":
                return "The chatbot has asked an important question or identified a problem. Provide a more detailed response (20-35 words) to properly address it."
            else:
                return "The chatbot has asked an important question or identified a problem. You can be detailed (30-50 words) in your response to fully address it."
        
        # Occasionally vary the message length randomly for natural conversation flow
        elif random_variation:
            if random.random() < 0.7:  # 70% chance to be shorter
                return "For this response, keep it briefer than usual. A quick, concise reply (5-15 words) would be natural here."
            else:  # 30% chance to be longer
                return "For this response, you feel like elaborating a bit more than usual (add 10-15 words beyond your typical length)."
        
        # Most regular responses should be shorter than the baseline
        else:
            if baseline_length_style == "very_short":
                return "Keep your response very brief (3-8 words), as people typically use short messages in ongoing conversations."
            elif baseline_length_style == "short":
                return "Keep your response brief (5-15 words), as people typically use shorter messages in ongoing conversations."
            elif baseline_length_style == "medium":
                return "Keep your response relatively concise (10-25 words), as people typically use shorter messages in ongoing conversations."
            else:
                return "Keep your response reasonably concise (15-35 words), although you tend to be more detailed than most people."
    
    # Fallback for any other cases
    return f"Follow your usual {baseline_length_style} message style ({baseline_min_words}-{baseline_max_words} words)."

def perform_user_reflection(
    role_description, 
    emotional_traits,
    conversation_history, 
    current_turn,
    selected_styles=None,
    llm_model="GEMMA-3-12B-GGUF",
    user_goal=None
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
        user_goal: The user's goal for this conversation, if available
        
    Returns:
        Dictionary with reflection results including next message and continuation status
    """
    # Get last chatbot message if available
    last_chatbot_message = ""
    if len(conversation_history) > 0 and conversation_history[-1][0] == "Chatbot":
        last_chatbot_message = conversation_history[-1][1]
    
    # Determine adaptive message length based on context
    adaptive_length_instruction = determine_adaptive_message_length(
        current_turn, 
        selected_styles,
        last_chatbot_message
    )
    
    # Generate instructions for realistic human behavior
    realistic_behavior_instructions = generate_realistic_behavior_instructions(current_turn)
    
    # Assess if the chatbot's response helps achieve the user's goal
    goal_alignment = ""
    if user_goal and last_chatbot_message:
        goal_alignment = assess_goal_alignment(user_goal, last_chatbot_message, current_turn)
    
    # Construct the prompt for user reflection
    prompt = construct_user_reflection_prompt(
        role_description, 
        emotional_traits, 
        conversation_history, 
        adaptive_length_instruction,
        realistic_behavior_instructions,
        goal_alignment
    )
    
    # Call LLM to generate response (simplified for illustration)
    raw_response = call_llm(prompt, model=llm_model)
    processed_response = process_reflection_response(raw_response)
    return processed_response

def assess_goal_alignment(user_goal, last_chatbot_message, current_turn):
    """
    Assesses how well the chatbot's response aligns with the user's goals and provides guidance
    for the user's reaction.
    
    Args:
        user_goal: String describing the user's goal for this conversation
        last_chatbot_message: The most recent message from the chatbot
        current_turn: Current turn number in the conversation
    
    Returns:
        String with instructions for the user's reaction based on goal alignment
    """
    # Create instructions for realistic goal-based reactions
    instructions = [
        "## Goal Assessment",
        f"Your primary goal in this conversation is: {user_goal}",
        "",
        "Based on this goal, consider:",
    ]
    
    # First turn guidance
    if current_turn == 1:
        instructions.append("- Since this is your first response, express your initial reaction and what you hope to get from this conversation.")
        instructions.append("- It's natural to be somewhat skeptical of help, but remain open to suggestions that might address your needs.")
        return "\n".join(instructions)
    
    # Progressive goal assessment for later turns
    if current_turn >= 2:
        instructions.extend([
            "- Evaluate if the chatbot's last response is bringing you closer to your goal or not.",
            "- Your agreement or disagreement should be based primarily on whether the response helps with your specific goal.",
            "",
            "Consider responding in one of these ways:",
            "1. **If the suggestion directly addresses your goal:** Show cautious optimism, but it's still natural to have follow-up questions or want clarification.",
            "2. **If the suggestion partially addresses your goal:** Acknowledge what's useful and specifically point out what's still missing or concerning.",
            "3. **If the suggestion misses your goal entirely:** Express disappointment or redirect the conversation toward what you actually need."
        ])
    
    # Add more nuanced guidance for later turns
    if current_turn >= 3:
        instructions.extend([
            "",
            "At this point in the conversation:",
            "- Show signs of whether you're making progress toward your goal or not.",
            "- If progress is being made, you might express relief or cautious optimism.",
            "- If little progress has been made, your frustration might be more apparent.",
            "- Be willing to compromise on approaches, but not on your fundamental goal."
        ])
    
    return "\n".join(instructions)

def call_llm(prompt, model="GPT-4o"):
    """
    Calls the language model with the given prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        model: The model name to use
    
    Returns:
        The raw response from the LLM
    """
    # This is a simplified version - in the real implementation, this would call the actual LLM
    # Use the imported LLM class
    llm = LLM(model)
    response = llm.generate(prompt)
    return response

def process_reflection_response(raw_response):
    """
    Processes the raw LLM response and extracts the structured reflection data.
    
    Args:
        raw_response: The raw text response from the LLM
    
    Returns:
        Dictionary with the structured reflection data
    """
    # Find JSON-like content in the response
    json_match = re.search(r'({[\s\S]*})', raw_response)
    if json_match:
        cleaned_json = json_match.group(1)
        result = json.loads(cleaned_json)
        
        # Ensure required fields are present
        if "reasoning" not in result:
            result["reasoning"] = "No explicit reasoning provided."
            
        if "next_message" not in result:
            result["next_message"] = "I'm not sure what to say next."
        
        if "should_continue" not in result:
            result["should_continue"] = True
        
        # Store the raw reflection for reference
        result["raw_reflection"] = raw_response
        
        return result
    else:
        # If no JSON was found, use the whole text as the message
        print(f"No JSON found in response, using raw text")
        return {
            "reasoning": "No structured reasoning provided.",
            "next_message": raw_response.strip(),
            "should_continue": True,
            "raw_reflection": raw_response
        }

def get_adaptive_user_message(scenario_data, conversation_history, current_turn, selected_styles=None, reasoning_model="GEMMA-3-12B"):
    """
    Generates a realistic user message based on the conversation context and role.
    
    Args:
        scenario_data: Dictionary containing scenario and role information
        conversation_history: List of tuples containing (speaker, message)
        current_turn: Current turn number
        selected_styles: Dictionary containing the conversation style attributes
        reasoning_model: Model to use for user reflection (default: GEMMA-3-12B)
        
    Returns:
        Tuple containing (user_message, reflection_data)
    """
    # Extract role-based information
    role_description = scenario_data.get("role_description", "")
    emotional_traits = scenario_data.get("emotional_traits", "")
    user_goal = scenario_data.get("user_goal", "")
    
    # Perform reflection to determine user's response based on their role
    reflection_data = perform_user_reflection(
        role_description=role_description, 
        emotional_traits=emotional_traits,
        conversation_history=conversation_history, 
        current_turn=current_turn,
        selected_styles=selected_styles,
        llm_model=reasoning_model,
        user_goal=user_goal
    )
    
    # Extract the next message, with fallback if not present
    next_message = reflection_data.get("next_message", "")
    
    if not next_message:
        next_message = "I'm not sure what to say."
        
    return next_message, reflection_data