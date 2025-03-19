import requests
import json
import logging
import re
from config import RESPONSE_STYLES, GOOGLE_API_KEY, GOOGLE_API_BASE_URL, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class AIHandler:
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.api_key = GOOGLE_API_KEY
        self.base_url = GOOGLE_API_BASE_URL
        self.default_style = "romantic"
    
    def is_amharic(self, text):
        """Check if text contains Amharic characters."""
        # Amharic Unicode range: \u1200-\u137F
        amharic_pattern = re.compile(r'[\u1200-\u137F]')
        return bool(amharic_pattern.search(text))

    def is_transliterated_amharic(self, text):
        """Check if text might be Amharic written in Latin alphabet."""
        # Common Amharic transliteration patterns
        amharic_markers = [
            r'\b(ene|ante|anchi|esu|esua|egna|enanet|enante)\b',  # pronouns
            r'\b(selam|tena yistilign|dehna|betam|ameseginalehu)\b',  # common phrases
            r'\b(new|nesh|nat|nachew|nen)\b',  # forms of "to be"
            r'\b(yihe|yih|ya|yehe|esu)\b',  # demonstratives
            r'\b(min|man|yet|meche|sint)\b',  # question words
            r'\b(alegn|alesh|ale|alat|alen|alachihu|alachew)\b',  # have forms
            r'\b(ewedihalehu|ewedishalehu|ewedihalew|ewediyatalew)\b',  # love forms
        ]
        
        # Check for multiple Amharic markers
        matches = 0
        for pattern in amharic_markers:
            if re.search(pattern, text.lower()):
                matches += 1
                if matches >= 1:  # If at least one marker is found
                    return True
        
        return False
    
    def generate_response(self, girlfriend_message, user_data):
        try:
            # Get user preferences
            style = user_data.get("style", self.default_style)
            girlfriend_name = user_data.get("girlfriend_name", "your girlfriend")
            personal_details = user_data.get("personal_details", {})
            history = user_data.get("history", [])
            
            # Detect language format
            is_amharic_message = self.is_amharic(girlfriend_message)
            is_transliterated = self.is_transliterated_amharic(girlfriend_message)
            
            # Create system prompt based on style
            style_description = RESPONSE_STYLES.get(style, RESPONSE_STYLES[self.default_style])
            
            # Build context from personal details
            context = ""
            if personal_details:
                context = "Important personal details to remember:\n"
                for key, value in personal_details.items():
                    context += f"- {key}: {value}\n"
            
            # Format conversation history
            history_text = ""
            if history:
                history_text = "Recent conversation:\n"
                for i, (gf_msg, bf_resp) in enumerate(history[-3:]):  # Only use last 3 exchanges
                    history_text += f"Girlfriend: {gf_msg}\n"
                    history_text += f"Boyfriend: {bf_resp}\n\n"
            
            # Determine language instruction based on detection
            language_instruction = "Respond in English."
            if is_amharic_message:
                language_instruction = "Respond in Amharic using Amharic script (Fidel)."
            elif is_transliterated:
                language_instruction = "Respond in Amharic but write it using Latin alphabet (transliterated Amharic). Do not use Amharic script."
            
            combined_prompt = (
                f"You are helping a boyfriend respond to his girlfriend named {girlfriend_name}. "
                f"Generate a {style_description} response to her message.\n\n"
                f"{context}\n"
                f"{history_text}\n"
                f"IMPORTANT INSTRUCTIONS:\n"
                f"1. Keep your response short and direct (1-3 sentences only)\n"
                f"2. Don't use markdown formatting, asterisks, or bullet points\n"
                f"3. Don't provide multiple options - just give ONE perfect response\n"
                f"4. Write as if you ARE the boyfriend (first person)\n"
                f"5. Don't include explanations or notes\n"
                f"6. Don't use phrases like 'you could say' or 'here's a response'\n"
                f"7. Use appropriate emojis naturally (1-2 emojis max) if it fits the tone\n"
                f"8. Make the response sound natural, like a real text from a boyfriend\n"
                f"9. Never start with 'As your boyfriend' or similar phrases\n"
                f"10. {language_instruction}\n\n"
                f"Her message: \"{girlfriend_message}\"\n\n"
                f"My response:"
            )
            
            # Call Gemini API
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [
                    {"parts": [{"text": combined_prompt}]}
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 150
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info(f"Sending request to Gemini API")
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response_json = response.json()
            
            logger.info(f"Received response from Gemini API: {response_json}")
            
            # Extract the response text from the Gemini API response
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                if "content" in response_json["candidates"][0] and "parts" in response_json["candidates"][0]["content"]:
                    ai_response = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # Clean up the response to remove any remaining formatting or options
                    ai_response = ai_response.replace("**", "").replace("Option 1:", "").replace("Option 2:", "")
                    ai_response = ai_response.replace("Option 3:", "").replace("*", "")
                    
                    # Remove any lines that start with numbers followed by a period (like "1. ")
                    ai_response = "\n".join([line for line in ai_response.split("\n") 
                                            if not (line.strip().startswith(("1.", "2.", "3.")) and len(line.strip()) > 3)])
                    
                    # Remove any "My response:" or similar prefixes
                    prefixes_to_remove = ["My response:", "Response:", "Boyfriend:", "Me:"]
                    for prefix in prefixes_to_remove:
                        if ai_response.startswith(prefix):
                            ai_response = ai_response[len(prefix):].strip()
                    
                    return ai_response
            
            # If we couldn't extract the response properly
            return "I couldn't generate a good response. Please try again."
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I couldn't generate a good response. Please try again."
    
    def generate_voice_message(self, text):
        """Generate a voice message from text (placeholder for future implementation)"""
        # This would integrate with a text-to-speech API
        # For now, we'll return None to indicate this feature isn't implemented
        return None