import argparse
from conversation_generator import RoleBasedConversationGenerator

def main():
    parser = argparse.ArgumentParser(description='Generate emotionally dynamic conversations using role-based scenarios.')
    parser.add_argument('--iterations', type=int, default=10,
                        help='Number of conversations to generate (default: 10)')
    parser.add_argument('--min-turns', type=int, default=3,
                        help='Minimum number of turns per conversation (default: 3)')
    parser.add_argument('--max-turns', type=int, default=7,
                        help='Maximum number of turns per conversation (default: 7)')
    parser.add_argument('--output', type=str, default='role_based_conversations.json',
                        help='Output file name (default: role_based_conversations.json)')
    parser.add_argument('--models', type=str, nargs='+', 
                        default=["GPT-4o", "CLAUDE-3.7-SONNET", "DEEPSEEK-R1"],
                        help='LLM models to use for conversation generation (default: ["GPT-4o", "CLAUDE-3.7-SONNET", "DEEPSEEK-R1"])')
    
    args = parser.parse_args()
    
    LLMs = args.models
    generator = RoleBasedConversationGenerator(LLMs)
    
    generator.generate_dataset(
        iterations=args.iterations,
        min_turns=args.min_turns,
        max_turns=args.max_turns,
        output_file=args.output
    )

if __name__ == "__main__":
    main()
