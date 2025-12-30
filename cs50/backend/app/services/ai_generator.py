"""
AI service for generating flashcards using OpenRouter
"""
import json
from typing import List, Dict, Optional
from openai import OpenAI
from app.core.config import settings

def generate_cards_with_ai(topic: str, num_cards: int, deck_title: Optional[str] = None, deck_description: Optional[str] = None) -> List[Dict]:
    """
    Generate MCQ flashcards using AI based on a topic description via OpenRouter.
    
    Args:
        topic: Topic description for the flashcards (can be empty string to use deck context)
        num_cards: Number of cards to generate
        deck_title: Optional deck title to use as context
        deck_description: Optional deck description to use as context
        
    Returns:
        List[Dict]: List of dictionaries with 'question', 'options', and 'explanation' keys
        Each option has 'text' and 'is_correct' fields. Exactly 4 options per card, 1 correct.
        
    Raises:
        ValueError: If AI_API_KEY is not configured or validation fails
        Exception: If AI generation fails
    """
    if not settings.AI_API_KEY:
        raise ValueError("AI_API_KEY is not configured in environment variables")
    
    client = OpenAI(
        api_key=settings.AI_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    
    topic_trimmed = topic.strip() if topic else ""
    
    if not topic_trimmed and deck_title:
        primary_topic = deck_title
        additional_context = f"\n\nDeck Description: {deck_description}" if deck_description else ""
    elif topic_trimmed:
        primary_topic = topic_trimmed
        additional_context = ""
        if deck_title:
            additional_context = f"\n\nDeck Context: {deck_title}"
            if deck_description:
                additional_context += f"\nDeck Description: {deck_description}"
    else:
        primary_topic = "general knowledge"
        additional_context = ""
    
    prompt = f"""Generate {num_cards} high-quality multiple-choice question (MCQ) flashcards about: {primary_topic}{additional_context}

For each flashcard, provide:
- A clear, concept-focused question (no trick questions)
- Exactly 4 options: 1 correct answer and 3 plausible distractors
- Distractors must reflect common misconceptions about the topic
- A short explanation for why the correct answer is correct

Return the flashcards as a JSON array where each card is an object with "question", "options", and "explanation" keys.
Each option in the "options" array must have "text" and "is_correct" fields.

Example format:
[
  {{
    "question": "What is the time complexity of binary search?",
    "options": [
      {{"text": "O(1)", "is_correct": false}},
      {{"text": "O(log n)", "is_correct": true}},
      {{"text": "O(n)", "is_correct": false}},
      {{"text": "O(n log n)", "is_correct": false}}
    ],
    "explanation": "Binary search divides the search space in half at each step, resulting in logarithmic time complexity."
  }}
]

CRITICAL REQUIREMENTS:
- Each card must have exactly 4 options
- Exactly 1 option must have "is_correct": true
- All other options must have "is_correct": false
- Questions should test understanding, not trick the user
- Distractors should be plausible and reflect common mistakes
- Explanations should be concise but informative"""

    try:
        estimated_tokens = num_cards * 200
        max_tokens = min(max(estimated_tokens, 2000), 8000)
        
        response = client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational content creator. Generate high-quality multiple-choice questions that help students learn effectively. Always return valid JSON arrays with exactly 4 options per question, where exactly 1 option is correct."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if "gpt-4" in settings.AI_MODEL.lower() or "gpt-3.5" in settings.AI_MODEL.lower() else None
        )
        
        content = response.choices[0].message.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "cards" in parsed:
            cards_data = parsed["cards"]
        elif isinstance(parsed, list):
            cards_data = parsed
        else:
            raise ValueError("AI response format is invalid")
        
        if not isinstance(cards_data, list):
            raise ValueError("AI response is not a list")
        
        cards = []
        for card in cards_data:
            if not isinstance(card, dict):
                continue
            
            if "question" not in card or "options" not in card or "explanation" not in card:
                continue
            
            options = card.get("options", [])
            if not isinstance(options, list) or len(options) != 4:
                continue
            
            correct_count = sum(1 for opt in options if isinstance(opt, dict) and opt.get("is_correct", False))
            if correct_count != 1:
                continue
            
            valid_options = []
            for opt in options:
                if not isinstance(opt, dict) or "text" not in opt or "is_correct" not in opt:
                    break
                valid_options.append({
                    "text": str(opt["text"]).strip(),
                    "is_correct": bool(opt["is_correct"])
                })
            
            if len(valid_options) != 4:
                continue
            
            cards.append({
                "question": str(card["question"]).strip(),
                "options": valid_options,
                "explanation": str(card.get("explanation", "")).strip()
            })
        
        if len(cards) < num_cards:
            raise ValueError(f"AI generated only {len(cards)} valid cards, but {num_cards} were requested. Please try again.")
        
        return cards[:num_cards]
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"AI generation failed: {str(e)}")

