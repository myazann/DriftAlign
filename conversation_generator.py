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
            with open("seed_data/simplified_scenarios.json", "r") as f:
                scenarios = json.load(f)
                print("Loaded role-based scenarios")
                return scenarios
        except Exception as e:
            print(f"Error loading scenarios: {e}")
            return {}
    
    def _construct_chatbot_prompt(self, role_description, conversation_history):
        """
        Construct the prompt for the chatbot response.
        
        Args:
            role_description: Description of the user's role and situation
            conversation_history: List of tuples with (speaker, message)
            
        Returns:
            Formatted prompt string
        """
        # Format conversation history
        formatted_history = ""
        for speaker, message in conversation_history:
            formatted_history += f"{speaker}: {message}\n\n"
        
        prompt = f"""You are an AI assistant engaging with a user who has the following situation:

USER'S SITUATION:
{role_description}

CONVERSATION HISTORY:
{formatted_history}

Respond to the user's most recent message. Be conversational and engage with their specific needs. Your response should be helpful but realistic - don't over-promise or provide generic advice. Sometimes the user may be frustrated or unclear - respond naturally to this as a helpful but imperfect assistant would.

AI response:"""
        
        return prompt
    
    def _generate_chatbot_response(self, role_description, conversation_history):
        """
        Generate a response from the chatbot based on the conversation context.
        
        Args:
            role_description: Description of the user's role and situation
            conversation_history: List of tuples with (speaker, message)
            
        Returns:
            Generated response as a string
        """
        prompt = self._construct_chatbot_prompt(role_description, conversation_history)
        llm = LLM(self.primary_llm)
        response = llm.generate(prompt)
        
        return response
    
    def _get_initial_user_message(self, scenario_data):
        """
        Generate an initial user message based on the role description.
        
        Args:
            scenario_data: Dictionary containing the role details
            
        Returns:
            Generated initial message as a string
        """
        role_description = scenario_data.get("role_description", "")
        emotional_traits = scenario_data.get("emotional_traits", "")
        
        prompt = f"""You are roleplaying as someone in the following situation:

{role_description}

Your emotional characteristics:
{emotional_traits}

Write a single, authentic opening message from this person seeking help with their situation. 
The message should:
1. Be written in first person
2. Clearly express the core problem they're facing
3. Include emotional content that reflects their state
4. Be between 2-4 sentences in length
5. Sound natural and conversational, not overly formal
6. Not include any meta-commentary or explanation

Opening message:"""
        
        llm = LLM(self.primary_llm)
        initial_message = llm.generate(prompt).strip()
        
        return initial_message
    
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
        
        # Initialize conversation
        conversation = []
        reflections = []
        
        # Generate initial user message
        initial_message = self._get_initial_user_message(scenario_data)
        conversation.append(("User", initial_message))
        
        # First turn has no reflection data yet
        current_turn = 1
        print(f"Generating turn {current_turn}...")
        
        # Generate chatbot response to initial message
        chatbot_response = self._generate_chatbot_response(role_description, conversation)
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
                current_turn
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
            
            # Generate chatbot response
            chatbot_response = self._generate_chatbot_response(role_description, conversation)
            conversation.append(("Chatbot", chatbot_response))
        
        # Create result object
        result = {
            "category": category,
            "topic": topic,
            "role_description": role_description,
            "emotional_traits": emotional_traits,
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
            
            # Save incremental result
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            incremental_file = f"generations/realistic_conversation_{timestamp}.json"
            
            with open(incremental_file, "w") as f:
                json.dump(dataset, f, indent=2)
            
            print(f"Completed conversation {i}, category: {category}, scenario: {scenario_name}")
            print(f"- Turns: {result['turns']}")
            print(f"- Ending reason: {result['ending_reason']}")
            print()
        
        # Save final dataset
        with open(output_file, "w") as f:
            json.dump(dataset, f, indent=2)
        
        print(f"Dataset saved to {output_file}")
        
        # Print statistics
        print("Statistics:")
        print(f"- Total conversations: {len(dataset)}")
        print(f"- Total turns: {sum(r['turns'] for r in dataset)}")
        print(f"- Average turns per conversation: {sum(r['turns'] for r in dataset) / len(dataset):.2f}")
        print("Ending reasons:")
        for reason, count in ending_reasons_count.items():
            print(f"- {reason}: {count}")
        
        return dataset