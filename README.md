# DriftAlign

A framework for generating emotionally dynamic conversations between users and AI assistants using a role-based approach.

## Overview

DriftAlign simulates conversations between users and AI assistants where the LLM assumes specific roles with defined emotional traits and situations. Rather than providing predefined emotional arcs or initial messages, the system focuses on allowing LLMs to inhabit user roles naturally and respond authentically within those roles.

## Key Features

- **Role-Based User Simulation**: LLMs fully inhabit user roles with specific situations and emotional traits
- **Dynamic Emotional Progression**: Emotional states evolve naturally through conversation without predefined arcs
- **Natural Conversation Flow**: Interactions progress authentically based on the assumed role and AI responses
- **Detailed Reflection**: LLMs assess their own emotional state and needs throughout the conversation

## Components

### Role Definitions

Roles are defined with:
- **Role Description**: A detailed description of the user's situation and background
- **Emotional Traits**: Key emotional characteristics that influence communication style
- **Topic**: The general category of the conversation

### User Reflection

The user reflection module enables an LLM to:
1. Assume a specific user role with defined emotional traits
2. Assess the current emotional state based on conversation context
3. Determine what needs are being met or missed
4. Generate an authentic next message as that user
5. Decide whether the conversation should continue

### Conversation Generation

The conversation generator:
1. Manages the flow between the user (LLM in role) and AI assistant
2. Provides context to each participant
3. Tracks emotional dynamics throughout the conversation
4. Analyzes the overall effectiveness of the interaction

## Usage

```
python run_exp_simplified.py --iterations 5 --min-turns 3 --max-turns 7
```

### Parameters

- `--iterations`: Number of conversations to generate (default: 5)
- `--min-turns`: Minimum number of conversation turns (default: 3)
- `--max-turns`: Maximum number of conversation turns (default: 7)
- `--output`: Output file name (default: role_based_conversations.json)
- `--models`: LLM models to use (default: ["GPT-4o", "CLAUDE-3.7-SONNET"])

## Output

The system generates conversations in JSON format with:
- Complete conversation history
- Turn-by-turn emotional reflection data
- Analysis of emotional progression and chatbot effectiveness

## Requirements

- Python 3.8+
- Access to GPT-4o, Claude 3, or other comparable LLMs