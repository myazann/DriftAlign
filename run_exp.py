from conversation_generator import ConversationGenerator

def main():
    """
    Main function to run the experiment and generate the dataset.
    """
    # Define multiple LLMs
    LLMs = ["GPT-4o", "GPT-4o-mini", "CLAUDE-3.7-SONNET"]

    # Number of total conversations to generate
    n_iterations = 10  # Increase for larger dataset
    min_turns = 3
    max_turns = 7
    
    # Initialize conversation generator
    generator = ConversationGenerator(LLMs)
    
    # Generate dataset
    dataset = generator.generate_dataset(n_iterations, min_turns=min_turns, max_turns=max_turns)

if __name__ == "__main__":
    main()
