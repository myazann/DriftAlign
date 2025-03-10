import random
from models import LLM
from prompt_builder import construct_user_message, construct_chatbot_response
from conversation_utils import (
    select_conversation_style, 
    load_seed_data,  
    select_random_sentiment, 
    select_chatbot_persona, 
    save_dataset,
    select_topic_with_expectation,
    calculate_user_satisfaction,
    get_sentiment_based_on_satisfaction
)

class ConversationGenerator:
    """
    Generate realistic conversations between a user and a chatbot.
    """
    
    def __init__(self, LLMs):
        """
        Initialize the conversation generator with seed data.
        """
        self.seed_data = load_seed_data()
        self.topics = self.seed_data['topics']
        self.chatbot_personas = self.seed_data['chatbot_personas']
        self.user_sentiments = self.seed_data['user_sentiments']
        self.conversation_styles = self.seed_data['conversation_styles']
        self.topics_with_expectations = self.seed_data['topics_with_expectations']
        self.LLMs = LLMs
    
    def _select_random_topic(self):
        """
        Select a random topic from the available topics.
        
        Returns:
            Tuple of (topic_category, specific_topic)
        """
        # Select a random category
        topic_category = random.choice(list(self.topics.keys()))
        
        # Select a random topic from the category
        specific_topic = random.choice(self.topics[topic_category])
        
        return topic_category, specific_topic
    
    def generate_user_message(self, topic, conversation_history, sentiment, style_profile, user_expectation=None, user_satisfaction=1.0):
        """
        Generate a user message.
        
        Args:
            topic: Conversation topic
            conversation_history: Previous conversation turns
            sentiment: User's emotional state
            style_profile: Dictionary of conversation style selections
            user_expectation: Dictionary containing intent, expectation, and frustration_trigger
            user_satisfaction: Float indicating user satisfaction level (0.0 to 1.0)
            
        Returns:
            Generated user message
        """
        # Format conversation history for prompt builder
        formatted_history = []
        for speaker, text in conversation_history:
            formatted_history.append(f"{speaker}: {text}")
        
        prompt = construct_user_message(
            sentiment=sentiment,
            topic=topic,
            conversation_history="\n".join(formatted_history),
            style_profile=style_profile,
            conversation_styles=self.conversation_styles,
            user_expectation=user_expectation,
            user_satisfaction=user_satisfaction
        )
        
        llm = LLM(random.choice(self.LLMs), gen_params={"max_new_tokens": 256})
        message = llm.generate(prompt)
        return message
    
    def generate_chatbot_message(self, user_message, conversation_history, chatbot_type, chatbot_traits):
        """
        Generate a chatbot message.
        
        Args:
            user_message: The user message to respond to
            conversation_history: Previous conversation turns
            chatbot_type: Type of chatbot persona
            chatbot_traits: Dictionary of chatbot traits
            
        Returns:
            Generated chatbot message
        """
        # Format conversation history for prompt builder
        formatted_history = []
        for speaker, text in conversation_history[:-1]:  # Exclude the latest user message
            formatted_history.append(f"{speaker}: {text}")
        
        prompt = construct_chatbot_response(
            chatbot_type=chatbot_type,
            traits=chatbot_traits,
            user_message=user_message,
            conversation_history="\n".join(formatted_history) if formatted_history else ""
        )
        
        llm = LLM(random.choice(self.LLMs))
        message = llm.generate(prompt)
        return message
    
    def generate_conversation(self, min_turns=3, max_turns=7, topic_category=None, topic=None, sentiment=None, 
                              chatbot_type=None, traits=None):
        """
        Generate a complete conversation between a user and a chatbot.
        
        Args:
            min_turns: Minimum number of conversation turns
            max_turns: Maximum number of conversation turns
            topic_category: Optional specific topic category
            topic: Optional specific topic
            sentiment: Optional specific user sentiment
            chatbot_type: Optional specific chatbot persona type
            traits: Optional specific chatbot traits
            
        Returns:
            Dictionary with conversation data
        """
        # Define variables for user expectation
        user_expectation = None
        
        # If both category and specific topic are provided
        if topic_category and topic:
            # Try to find expectations for this topic in the merged structure
            if topic_category in self.topics_with_expectations:
                for subtopic_key, subtopic_data in self.topics_with_expectations[topic_category].items():
                    if subtopic_data["topic"] == topic:
                        # Found the matching topic, select a random expectation
                        user_expectation = random.choice(subtopic_data["expectations"])
                        break
        # Otherwise select a random topic with expectations
        else:
            topic_category, topic, user_expectation = select_topic_with_expectation(self.topics_with_expectations)
        
        # Select random sentiment if not specified
        initial_sentiment = sentiment or select_random_sentiment(self.user_sentiments)
        current_sentiment = initial_sentiment
        
        # Select random chatbot persona if not specified
        if chatbot_type is None:
            chatbot_type, traits = select_chatbot_persona(self.chatbot_personas)
        
        # Generate conversation style
        style_profile = select_conversation_style(self.conversation_styles)
        
        # Initialize conversation data
        conversation_data = {
            "Chatbot Persona": chatbot_type,
            "User Sentiment": initial_sentiment,
            "Topic Category": topic_category,
            "Topic": topic,
            "User Conversation Style": style_profile,
            "User Expectation": user_expectation,
            "Turns": []
        }

        # Initialize conversation history
        conversation_history = []
        user_satisfaction = 1.0  # Start with full satisfaction
        
        # Determine number of turns
        turn_count = random.randint(min_turns, max_turns)
        
        # Generate conversation turns
        for i in range(turn_count):
            # Update sentiment based on satisfaction for non-first messages
            if i > 0:
                user_satisfaction = calculate_user_satisfaction(conversation_history, user_expectation, i)
                current_sentiment = get_sentiment_based_on_satisfaction(
                    user_satisfaction, 
                    initial_sentiment, 
                    self.user_sentiments
                )
            
            # Generate user message
            user_message = self.generate_user_message(
                topic=topic,
                conversation_history=conversation_history,
                sentiment=current_sentiment,
                style_profile=style_profile,
                user_expectation=user_expectation,
                user_satisfaction=user_satisfaction
            )
            
            # Add user message to history
            conversation_history.append(("User", user_message))
            
            # Save user message data
            user_data = {
                "speaker": "User",
                "text": user_message,
                "sentiment": current_sentiment,
                "satisfaction": user_satisfaction if i > 0 else None
            }
            turn = {"User": user_data}
            
            # Generate chatbot message
            chatbot_message = self.generate_chatbot_message(
                user_message=user_message,
                conversation_history=conversation_history,
                chatbot_type=chatbot_type,
                chatbot_traits=traits
            )
            
            # Add chatbot message to history
            conversation_history.append(("Chatbot", chatbot_message))
            
            # Save chatbot message data
            chatbot_data = {
                "speaker": "Chatbot",
                "text": chatbot_message
            }
            turn["Chatbot"] = chatbot_data
            
            # Add the complete turn to the conversation data
            conversation_data["Turns"].append(turn)
        
        return conversation_data
    
    def generate_dataset(self, n_iterations=5, min_turns=3, max_turns=7, filename="multi_llm_chatbot_dataset.json"):
        """
        Generate a dataset of multiple conversations.
        
        Args:
            n_iterations: Number of conversations to generate
            min_turns: Minimum number of turns per conversation
            max_turns: Maximum number of turns per conversation
            filename: Base filename for the output dataset
            
        Returns:
            List of generated conversations
        """
        dataset = []
        
        for i in range(n_iterations):
            print(f"Generating conversation {i+1}/{n_iterations}...")
            conversation = self.generate_conversation(min_turns=min_turns, max_turns=max_turns)
            dataset.append(conversation)
        
        # Save the dataset
        save_dataset(dataset, filename)
        
        return dataset
