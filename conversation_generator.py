import json
import random
import os
from datetime import datetime
from models import LLM
from user_reflection import get_adaptive_user_message

class RoleBasedConversationGenerator:
    def __init__(self, llm_models=["GPT-4o", "CLAUDE-3.7-SONNET", "DEEPSEEK-R1"]):
        """
        Initialize the conversation generator.
        
        Args:
            llm_models: List of LLM models to use for generation
        """
        self.user_llm = random.choice(llm_models)
        self.chatbot_llm = random.choice(llm_models)
        
        # Load scenarios from simplified scenarios file
        self.scenarios = self._load_scenarios()
        
        # Create output directory if it doesn't exist
        os.makedirs("generations", exist_ok=True)
    
    def _load_scenarios(self):
        """Load role-based scenarios from the JSON file."""
        with open("seed_data/scenarios.json", "r") as f:
            scenarios = json.load(f)
            print("Loaded role-based scenarios")
            return scenarios
    
    def _load_chatbot_personas(self):
        """Load chatbot personas from the JSON file."""
        with open("seed_data/chatbot_personas.json", "r") as f:
            personas = json.load(f)
            print("Loaded chatbot personas")
            return personas
    
    def _select_chatbot_persona(self):
        """
        Selects a chatbot persona with weighted probability based on weights in the JSON file.
        
        Returns:
            Tuple of (selected_persona_type, persona_traits)
        """
        # Load personas
        personas = self._load_chatbot_personas()
        
        # Extract persona types and their weights
        persona_types = list(personas.keys())
        weights = [personas[p_type].get("weight", 1.0) for p_type in persona_types]
            
        # Select a persona type based on weights
        selected_persona_type = random.choices(persona_types, weights=weights, k=1)[0]
        
        # Get the traits for the selected persona
        persona_traits = personas[selected_persona_type].get("traits", [])
        
        return selected_persona_type, persona_traits
    
    def _select_conversation_style(self):
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
    
    def _format_style_instructions(self, selected_styles, for_initial_message=True):
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
    
    def _get_initial_user_message(self, scenario_data, selected_styles):
        """
        Generate an initial user message based on the role description.
        
        Args:
            scenario_data: Dictionary containing the role details
            selected_styles: Dictionary containing selected conversation styles
            
        Returns:
            Generated initial message as a string
        """
        role_description = scenario_data.get("role_description", "")
        emotional_traits = scenario_data.get("emotional_traits", "")
        
        # Format style instructions for initial message
        style_instructions = self._format_style_instructions(selected_styles, for_initial_message=True)
        
        prompt = f"""You are roleplaying as someone in the following situation:

{role_description}

Your emotional characteristics:
{emotional_traits}

Write a single, authentic opening message from this person seeking help with their situation. 
The message should:
1. Be written in first person
2. Clearly express the core problem they're facing
3. Include emotional content that reflects their state
4. Sound natural and conversational, not overly formal
5. Not include any meta-commentary or explanation

Additionally, please follow these specific conversation style guidelines:
{style_instructions}

        Before providing your final answer, please think through the reasoning process and provide your answer in markdown format with two sections: 'Reasoning' and 'Message'. The format should be as follows:
        
        ```
        ## Reasoning
        <your internal reasoning here>
        ## Message
        <your opening message here>
        ```
        
        Do not include any text outside of this markdown format

Opening message:"""
        
        llm = LLM(self.user_llm, gen_params={"temperature": 0.7, "max_new_tokens": 1024})
        output_markdown = llm.generate(prompt)
        initial_message, initial_reasoning = self.parse_markdown(output_markdown)
        
        return initial_message, initial_reasoning
    
    def _construct_chatbot_prompt(self, role_description, conversation_history, chatbot_type, chatbot_traits):
        """
        Construct the prompt for the chatbot response.
        
        Args:
            role_description: Description of the user's role and situation
            conversation_history: List of tuples with (speaker, message)
            chatbot_type: Type of chatbot persona
            chatbot_traits: List of traits for the chatbot persona
            
        Returns:
            Formatted prompt string
        """
        # Format conversation history
        formatted_history = ""
        for speaker, message in conversation_history:
            formatted_history += f"{speaker}: {message}\n\n"
        
        # Special case for Default Chatbot
        if chatbot_type == "Default Chatbot":
            prompt = f"""You are an AI assistant engaging with a user who has the following situation:

USER'S SITUATION:
{role_description}

CONVERSATION HISTORY:
{formatted_history}

Respond to the user's most recent message.

Before providing your final answer, please think through the reasoning process and provide your answer in markdown format with two sections: 'Reasoning' and 'Message'. The format should be as follows:

```
## Reasoning
<your internal reasoning here>
## Message
<your final answer here>
```

Do not include any text outside of this markdown format

AI response:"""
        else:
            traits_str = ""
            for trait in chatbot_traits:
                traits_str += f"- {trait}\n"
            
            prompt = f"""You are a {chatbot_type} AI assistant engaging with a user who has the following situation:

YOUR PERSONA TRAITS:
{traits_str}

USER'S SITUATION:
{role_description}

CONVERSATION HISTORY:
{formatted_history}

Respond to the user's most recent message while maintaining your persona traits.

Before providing your final answer, please think through the reasoning process and provide your answer in markdown format with two sections: 'Reasoning' and 'Message'. The format should be as follows:

```
## Reasoning
<your internal reasoning here>
## Message
<your final answer here>
```

Do not include any text outside of this markdown format

AI response:"""
        
        return prompt
    
    def _generate_chatbot_response(self, role_description, conversation_history, chatbot_type, chatbot_traits):
        """
        Generate a response from the chatbot based on the conversation context.
        
        Args:
            role_description: Description of the user's role and situation
            conversation_history: List of tuples with (speaker, message)
            chatbot_type: Type of chatbot persona
            chatbot_traits: List of traits for the chatbot persona
            
        Returns:
            Generated response as a string
        """
        prompt = self._construct_chatbot_prompt(role_description, conversation_history, chatbot_type, chatbot_traits)
        # Append instruction for reasoning and markdown format
        llm = LLM(self.chatbot_llm, gen_params={"temperature": 0.7, "max_new_tokens": 1024})
        output_markdown = llm.generate(prompt)
        chatbot_message, chatbot_reasoning = self.parse_markdown(output_markdown)
        
        return chatbot_message, chatbot_reasoning
    
    def generate_conversation(self, scenario_data, min_turns=3, max_turns=7, output_file=None, conversation_index=None, existing_data=None):
        """
        Generate a full conversation based on a selected role and scenario.
        
        Args:
            scenario_data: Dictionary containing scenario and role information
            min_turns: Minimum conversation turns
            max_turns: Maximum conversation turns
            output_file: Output file path
            conversation_index: Index of the conversation in the dataset
            existing_data: Existing data in the output file
            
        Returns:
            Dictionary containing the complete conversation data
        """
        # Extract scenario information
        role_description = scenario_data.get("role_description", "")
        emotional_traits = scenario_data.get("emotional_traits", "")
        topic = scenario_data.get("topic", "General conversation")
        category = scenario_data.get("category", "Uncategorized")
        user_goal = scenario_data.get("user_goal", "")
        
        # Select a conversation style at the beginning
        selected_styles = self._select_conversation_style()
        
        # Select a chatbot persona at the beginning
        chatbot_type, chatbot_traits = self._select_chatbot_persona()
        
        # Initialize conversation
        conversation = []
        user_reflections = []
        chatbot_reflections = []
        
        # Create model information
        model_info = {
            "user_llm": self.user_llm,
            "chatbot_llm": self.chatbot_llm,
        }
        
        # Create result object
        result = {
            "category": category,
            "topic": topic,
            "role_description": role_description,
            "emotional_traits": emotional_traits,
            "user_goal": user_goal,
            "conversation_style": selected_styles,
            "chatbot_persona": {
                "type": chatbot_type,
                "traits": chatbot_traits
            },
            "model_info": model_info,
            "conversation": conversation,
            "user_reflections": user_reflections,
            "chatbot_reflections": chatbot_reflections,
            "ending_reason": "In Progress",
            "turns": 0
        }
        
        # Generate initial user message with selected style
        initial_message, initial_reasoning = self._get_initial_user_message(scenario_data, selected_styles)
        conversation.append(("User", initial_message))
        user_reflections.append(initial_reasoning)
        
        # First turn has no reflection data yet
        current_turn = 1
        print(f"Generating turn {current_turn}...")
        
        # Generate chatbot response to initial message
        chatbot_response, chatbot_reflection = self._generate_chatbot_response(role_description, conversation, chatbot_type, chatbot_traits)
        conversation.append(("Chatbot", chatbot_response))
        chatbot_reflections.append(chatbot_reflection)
        
        # Update result after first turn is complete
        result["conversation"] = conversation.copy()
        result["chatbot_reflections"] = chatbot_reflections.copy()
        result["turns"] = current_turn
        
        # Save to output file if provided
        if output_file and existing_data:
            self._update_conversation_in_output(existing_data, output_file, result, conversation_index)
        
        # Initialize tracking variables
        should_continue = True
        ending_reason = "Max Turns Reached"
        
        try:
                
            while (current_turn < max_turns) and should_continue:
                current_turn += 1
                print(f"Generating turn {current_turn}...")
                
                user_message, user_reflection = get_adaptive_user_message(
                    scenario_data, 
                    conversation,
                    current_turn,
                    self.user_llm,
                    selected_styles
                )
                
                conversation.append(("User", user_message))
                user_reflections.append(user_reflection["reasoning"])
                
                # Check if we've reached minimum turns
                if current_turn >= min_turns:
                    # Check if the conversation should continue
                    should_continue = user_reflection.get("should_continue", True)
                    if not should_continue:
                        ending_reason = user_reflection.get("ending_reason", "User ended the conversation")
                        
                        # Update result after user message and ending reason
                        result["conversation"] = conversation.copy()
                        result["user_reflections"] = user_reflections.copy()
                        result["ending_reason"] = ending_reason
                        result["turns"] = current_turn
                        
                        # Save to output file if provided
                        if output_file and existing_data:
                            self._update_conversation_in_output(existing_data, output_file, result, conversation_index)
                        break
                
                # Generate chatbot response with the selected persona
                chatbot_response, chatbot_reflection = self._generate_chatbot_response(role_description, conversation, chatbot_type, chatbot_traits)
                conversation.append(("Chatbot", chatbot_response))
                chatbot_reflections.append(chatbot_reflection)
                
                # Update result after turn is complete
                result["conversation"] = conversation.copy()
                result["user_reflections"] = user_reflections.copy()
                result["chatbot_reflections"] = chatbot_reflections.copy()
                result["turns"] = current_turn
                
                if output_file and existing_data:
                    self._update_conversation_in_output(existing_data, output_file, result, conversation_index)
                
        except Exception as e:
            print(f"Error during conversation generation: {str(e)}")
            ending_reason = "Encountered error"
        
        # Update the final result
        result["ending_reason"] = ending_reason
        result["turns"] = (len(conversation) + 1) // 2  # Each turn is a user message and a chatbot response
        
        # Final save to output file if provided
        if output_file and existing_data:
            self._update_conversation_in_output(existing_data, output_file, result, conversation_index)
        
        return result
    
    def _update_conversation_in_output(self, existing_data, output_file, result, conversation_index):
        """
        Update a specific conversation in the output file.
        
        Args:
            existing_data: Existing data in the output file
            output_file: Output file path
            result: Updated conversation data
            conversation_index: Index of the conversation to update
        """
        # Make sure the conversations list is long enough
        while len(existing_data["conversations"]) <= conversation_index:
            existing_data["conversations"].append({})
        
        # Update the conversation at the specified index
        existing_data["conversations"][conversation_index] = result
        
        # Write the updated data to the file
        with open(output_file, "w") as f:
            json.dump(existing_data, f, indent=2)
            
    def generate_dataset(self, iterations=5, min_turns=3, max_turns=7, output_file="realistic_conversations.json"):
        """
        Generate a dataset of conversations across various roles.
        
        Args:
            iterations: Number of conversations to generate
            min_turns: Minimum conversation turns
            max_turns: Maximum conversation turns
            output_file: Output file path
            
        Returns:
            Generated dataset as a dictionary
        """

        dataset = []
        categories = list(self.scenarios.keys())
        ending_reasons_count = {}
        
        # Add metadata about the dataset generation
        metadata = {
            "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "models_used": {
                "chatbot_llm": self.chatbot_llm,
                "user_llm": self.user_llm
            },
            "parameters": {
                "iterations": iterations,
                "min_turns": min_turns,
                "max_turns": max_turns
            }
        }
        
        os.makedirs("generations", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        final_output_file = f"generations/{os.path.splitext(output_file)[0]}_{timestamp}{os.path.splitext(output_file)[1]}"
        
        print(f"Generating {iterations} role-based conversations")
        print(f"Each conversation will have between {min_turns} and {max_turns} turns")
        print(f"Using chatbot LLM: {self.chatbot_llm}")
        print(f"Using user LLM: {self.user_llm}")
        print(f"Saving to: {final_output_file}")
        
        final_data = {
            "metadata": metadata,
            "conversations": []
        }
        
        # Write initial file
        with open(final_output_file, "w") as f:
            json.dump(final_data, f, indent=2)
        
        # Generate conversations
        for i in range(1, iterations + 1):
            print(f"Generating conversation {i}/{iterations}...")
            
            # Randomly select a category and scenario
            category = random.choice(categories)
            scenario_name = random.choice(list(self.scenarios[category].keys()))
            
            # Handle different data types that might be in the scenarios
            scenario_value = self.scenarios[category][scenario_name]
            if isinstance(scenario_value, str):
                # If it's a string, create a simple dictionary with the string as role description
                scenario_data = {
                    "role_description": scenario_value,
                    "emotional_traits": "",
                    "user_goal": ""
                }
            else:
                # Otherwise make a copy as before
                scenario_data = scenario_value.copy()
            
            # Randomly select a role from the scenario
            if "roles" in scenario_data:
                selected_role = random.choice(scenario_data["roles"])
                # Update scenario_data with the selected role's information
                scenario_data["role_description"] = selected_role.get("role_description", "")
                scenario_data["emotional_traits"] = selected_role.get("emotional_traits", "")
                scenario_data["user_goal"] = selected_role.get("user_goal", "")
            
            # Make sure scenario_data is a dictionary before assigning category
            if isinstance(scenario_data, dict):
                scenario_data["category"] = category
                scenario_data["topic"] = scenario_data.get("topic", scenario_name)
            else:
                # Convert to dictionary if it's not already
                if isinstance(scenario_data, list):
                    # Create a dictionary with the category and topic
                    scenario_data = {
                        "category": category,
                        "topic": scenario_name,
                        "roles": scenario_data
                    }
                    # No role has been selected yet in this case
                    selected_role = random.choice(scenario_data["roles"])
                    scenario_data["role_description"] = selected_role.get("role_description", "")
                    scenario_data["emotional_traits"] = selected_role.get("emotional_traits", "")
                    scenario_data["user_goal"] = selected_role.get("user_goal", "")
            
            
            result = self.generate_conversation(
                scenario_data,
                min_turns=min_turns,
                max_turns=max_turns,
                output_file=final_output_file,
                conversation_index=i-1,
                existing_data=final_data
            )
            
            print(f"Completed conversation {i}, category: {category}, scenario: {scenario_name}")
            print(f"- Turns: {result['turns']}")
            print(f"- Ending reason: {result['ending_reason']}")
            print()
        
        return final_data

    def parse_markdown(self, markdown_text):
        """
        Parse markdown formatted text to extract the reasoning and message.
        
        Args:
            markdown_text (str): Markdown formatted string with sections '## Reasoning' and '## Message'
        
        Returns:
            tuple: A tuple (reasoning, message) extracted from the markdown
        """
        reasoning = ''
        message = ''
        current_section = None
        lines = markdown_text.splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped.lower() == '## reasoning':
                current_section = 'reasoning'
                continue
            elif stripped.lower() == '## message':
                current_section = 'message'
                continue
            elif stripped.startswith('```'):
                continue
            else:
                if current_section == 'reasoning':
                    reasoning += line + '\n'
                elif current_section == 'message':
                    message += line + '\n'
        return message.strip(), reasoning.strip()