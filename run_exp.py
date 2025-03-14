"""
Role-based conversation generation script that focuses on LLMs assuming specific roles
and responding naturally within those roles.
"""

import argparse
from conversation_generator import RoleBasedConversationGenerator

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Generate emotionally dynamic conversations using role-based scenarios.')
    parser.add_argument('--iterations', type=int, default=10,
                        help='Number of conversations to generate (default: 5)')
    parser.add_argument('--min-turns', type=int, default=5,
                        help='Minimum number of turns per conversation (default: 3)')
    parser.add_argument('--max-turns', type=int, default=7,
                        help='Maximum number of turns per conversation (default: 7)')
    parser.add_argument('--output', type=str, default='role_based_conversations.json',
                        help='Output file name (default: role_based_conversations.json)')
    parser.add_argument('--models', type=str, nargs='+', 
                        default=["GPT-4o", "CLAUDE-3.7-SONNET"],
                        help='LLM models to use for conversation generation (default: ["GPT-4o", "CLAUDE-3.7-SONNET"])')
    parser.add_argument('--reasoning-model', type=str, default="DEEPSEEK-R1",
                        help='Model to use for user reflection')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize the role-based conversation generator
    LLMs = args.models
    reasoning_model = args.reasoning_model
    generator = RoleBasedConversationGenerator(LLMs, reasoning_model=reasoning_model)
    
    # Generate the dataset
    generator.generate_dataset(
        iterations=args.iterations,
        min_turns=args.min_turns,
        max_turns=args.max_turns,
        output_file=args.output
    )

if __name__ == "__main__":
    main()
