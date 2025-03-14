"""
Simplified role-based conversation generator that focuses on realistic human-like
interactions without complex emotional metrics or analysis.
"""

import json
import random
import os
from datetime import datetime
from models import LLM
from user_reflection import get_adaptive_user_message

class RoleBasedConversationGenerator:
    def __init__(self, llm_models=["GPT-4o", "CLAUDE-3.7-SONNET"]):
        """
        Initialize the conversation generator.
        
        Args:
            llm_models: List of LLM models to use for generation
        """
        self.llm_models = llm_models
        self.primary_llm = llm_models[0] if llm_models else "GPT-4o"
        
        # Load scenarios from simplified scenarios file
        self.scenarios = self._load_scenarios()
        
        # Create output directory if it doesn't exist
        os.makedirs("generations", exist_ok=True)
    
    def _load_scenarios(self):
        """Load role-based scenarios from the JSON file."""
        try:
            with open("seed_data/scenarios.json", "r") as f:
                scenarios = json.load(f)
                print("Loaded role-based scenarios")
                return scenarios
        except Exception as e:
            print(f"Error loading scenarios: {e}")
            return {}
    
    def _load_chatbot_personas(self):
        """Load chatbot personas from the JSON file."""
        try:
            with open("seed_data/chatbot_personas.json", "r") as f:
                personas = json.load(f)
                print("Loaded chatbot personas")
                return personas
        except Exception as e:
            print(f"Error loading chatbot personas: {e}")
            return {}
    
    def _select_chatbot_persona(self):
        """
        Selects a chatbot persona with weighted probability based on weights in the JSON file.
        
        Returns:
            Tuple of (selected_persona_type, persona_traits)
        """
        try:
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
            
        except Exception as e:
            print(f"Error selecting chatbot persona: {e}")
            return "Default Chatbot", []
    
    def _select_conversation_style(self):
        """
        Selects a conversation style randomly based on weights in the conversation_styles.json.
        
        Returns:
            Dictionary containing the selected style attributes
        """
        try:
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
                
        except Exception as e:
            print(f"Error loading conversation styles: {e}")
            return {}
    
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

Opening message:"""
        
        llm = LLM(self.primary_llm)
        initial_message = llm.generate(prompt).strip()
        
        return initial_message
    
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

AI response:"""
        else:
            # For other chatbot types, include traits
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
        llm = LLM(self.primary_llm)
        response = llm.generate(prompt)
        
        return response
    
    def generate_conversation(self, scenario_data, min_turns=3, max_turns=10):
        """
        Generate a complete conversation based on the given role.
        
        Args:
            scenario_data: Dictionary containing the role details
            min_turns: Minimum conversation turns
            max_turns: Maximum conversation turns
            
        Returns:
            Dictionary containing the complete conversation data
        """
        # Extract scenario information
        role_description = scenario_data.get("role_description", "")
        emotional_traits = scenario_data.get("emotional_traits", "")
        topic = scenario_data.get("topic", "General conversation")
        category = scenario_data.get("category", "Uncategorized")
        
        # Select a conversation style at the beginning
        selected_styles = self._select_conversation_style()
        
        # Select a chatbot persona at the beginning
        chatbot_type, chatbot_traits = self._select_chatbot_persona()
        
        # Initialize conversation
        conversation = []
        reflections = []
        
        # Generate initial user message with selected style
        initial_message = self._get_initial_user_message(scenario_data, selected_styles)
        conversation.append(("User", initial_message))
        
        # First turn has no reflection data yet
        current_turn = 1
        print(f"Generating turn {current_turn}...")
        
        # Generate chatbot response to initial message
        chatbot_response = self._generate_chatbot_response(role_description, conversation, chatbot_type, chatbot_traits)
        conversation.append(("Chatbot", chatbot_response))
        
        # Initialize tracking variables
        should_continue = True
        ending_reason = "Max Turns Reached"
        
        # Continue conversation for a minimum number of turns and up to max
        while (current_turn < max_turns) and should_continue:
            current_turn += 1
            print(f"Generating turn {current_turn}...")
            
            # Get adaptive user response with reflection
            user_message, reflection = get_adaptive_user_message(
                scenario_data, 
                conversation,
                current_turn,
                selected_styles
            )
            
            conversation.append(("User", user_message))
            reflections.append(reflection)
            
            # Check if we've reached minimum turns
            if current_turn >= min_turns:
                # Check if the conversation should continue
                should_continue = reflection.get("should_continue", True)
                if not should_continue:
                    ending_reason = reflection.get("ending_reason", "User ended the conversation")
                    break
            
            # Generate chatbot response with the selected persona
            chatbot_response = self._generate_chatbot_response(role_description, conversation, chatbot_type, chatbot_traits)
            conversation.append(("Chatbot", chatbot_response))
        
        # Create result object
        result = {
            "category": category,
            "topic": topic,
            "role_description": role_description,
            "emotional_traits": emotional_traits,
            "conversation_style": selected_styles,
            "chatbot_persona": {
                "type": chatbot_type,
                "traits": chatbot_traits
            },
            "conversation": conversation,
            "reflections": reflections,
            "ending_reason": ending_reason,
            "turns": (len(conversation) + 1) // 2  # Each turn is a user message and a chatbot response
        }
        
        return result
    
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
        
        print(f"Generating {iterations} role-based conversations")
        print(f"Each conversation will have between {min_turns} and {max_turns} turns")
        
        # Generate conversations
        for i in range(1, iterations + 1):
            print(f"Generating conversation {i}/{iterations}...")
            
            # Randomly select a category and scenario
            category = random.choice(categories)
            scenario_name = random.choice(list(self.scenarios[category].keys()))
            scenario_data = self.scenarios[category][scenario_name]
            scenario_data["category"] = category
            
            # Generate conversation
            result = self.generate_conversation(
                scenario_data,
                min_turns=min_turns,
                max_turns=max_turns
            )
            
            # Add to dataset
            dataset.append(result)
            
            # Update statistics
            ending_reason = result["ending_reason"]
            ending_reasons_count[ending_reason] = ending_reasons_count.get(ending_reason, 0) + 1
            
            print(f"Completed conversation {i}, category: {category}, scenario: {scenario_name}")
            print(f"- Turns: {result['turns']}")
            print(f"- Ending reason: {result['ending_reason']}")
            print()
        
        # Create generations directory if it doesn't exist
        os.makedirs("generations", exist_ok=True)
        
        # Save final dataset with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        final_output_file = f"generations/{os.path.splitext(output_file)[0]}_{timestamp}{os.path.splitext(output_file)[1]}"
        
        with open(final_output_file, "w") as f:
            json.dump(dataset, f, indent=2)
        
        print(f"Dataset saved to {final_output_file}")
        
        # Print statistics
        print("Statistics:")
        print(f"- Total conversations: {len(dataset)}")
        print(f"- Total turns: {sum(r['turns'] for r in dataset)}")
        print(f"- Average turns per conversation: {sum(r['turns'] for r in dataset) / len(dataset):.2f}")
        print("Ending reasons:")
        for reason, count in ending_reasons_count.items():
            print(f"- {reason}: {count}")
        
        return dataset