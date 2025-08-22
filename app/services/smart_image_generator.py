"""
Smart context-aware image generation service
Automatically generates appropriate anime-style images based on conversation context
"""

import re
from typing import Dict, Any, Optional, List
from ..constants import CHARACTER_TEMPLATES

class SmartImageGenerator:
    """Generates context-aware anime images based on conversation"""
    
    def __init__(self):
        # Base anime style prompt - beautiful anime like schoolgirl
        self.base_anime_style = "masterpiece, best quality, ultra detailed, anime style, beautiful artwork, high quality, detailed, soft lighting, vibrant colors, professional illustration, perfect anatomy, attractive features, stunning beauty, safe for work, tasteful, appropriate, 8k uhd, high resolution, highly detailed, sharp focus, studio lighting, professional photography"
        
        # Clothing levels - beautiful anime outfits (safe)
        self.clothing_levels = {
            "casual": "casual anime outfit, cute t-shirt, stylish jeans, fashionable, fully clothed",
            "elegant": "elegant anime dress, beautiful formal wear, sophisticated style, fully clothed", 
            "cute": "kawaii anime outfit, adorable dress, cute accessories, sweet style, fully clothed",
            "sporty": "anime sportswear, athletic outfit, energetic style, fully clothed",
            "swimwear": "beautiful anime swimsuit, beach wear, summer style, modest swimwear",
            "lingerie": "elegant anime sleepwear, beautiful pajamas, tasteful nightgown, fully covered",
            "sleepwear": "cute anime pajamas, comfortable nightgown, cozy sleepwear, fully covered"
        }
        
        # Character styles - beautiful anime characters like schoolgirl
        self.character_styles = {
            "luna": "beautiful anime girl with long wavy dark hair, large expressive eyes, elegant pose, seductive smile, confident expression, perfect features, stunning beauty, gorgeous face, flawless skin, perfect proportions",
            "sophia": "lovely anime girl with soft pink hair, large dreamy eyes, warm smile, gentle expression, romantic aura, sweet personality, beautiful features, adorable charm, cute face, perfect skin, lovely proportions", 
            "zara": "energetic anime girl with athletic build, vibrant hair, large sparkling eyes, dynamic pose, cheerful expression, fun personality, attractive features, energetic beauty, pretty face, healthy skin, fit proportions"
        }
        
        # Context keywords for automatic image generation
        self.auto_trigger_keywords = [
            "morning", "evening", "night", "sleep", "wake up", "bed", "bedroom",
            "shower", "bath", "tired", "rest", "relaxing", "comfortable",
            "date", "dinner", "romantic", "kiss", "hug", "embrace",
            "beach", "swimming", "hot", "summer", "warm", "cooling down"
        ]
    
    def should_generate_image(self, message: str, character_name: str = None) -> bool:
        """Check if we should auto-generate an image based on context"""
        message_lower = message.lower()
        
        # Check for trigger keywords
        return any(keyword in message_lower for keyword in self.auto_trigger_keywords)
    
    def analyze_context(self, message: str, character_name: str = "luna") -> Dict[str, Any]:
        """Analyze message context for image generation"""
        message_lower = message.lower()
        context = {
            "character": character_name.lower(),
            "clothing_level": "casual",
            "setting": "indoor",
            "mood": "friendly",
            "time_of_day": "day"
        }
        
        # Analyze clothing level
        if any(word in message_lower for word in ["sleep", "bed", "night", "tired", "pajama"]):
            context["clothing_level"] = "sleepwear"
        elif any(word in message_lower for word in ["shower", "bath", "hot", "warm"]):
            context["clothing_level"] = "swimwear"
        elif any(word in message_lower for word in ["romantic", "intimate", "seductive", "love"]):
            context["clothing_level"] = "lingerie"
        elif any(word in message_lower for word in ["sport", "exercise", "gym", "active"]):
            context["clothing_level"] = "sporty"
        elif any(word in message_lower for word in ["date", "dinner", "elegant", "formal"]):
            context["clothing_level"] = "elegant"
        elif any(word in message_lower for word in ["cute", "kawaii", "adorable"]):
            context["clothing_level"] = "cute"
        
        # Analyze setting
        if any(word in message_lower for word in ["beach", "swimming", "ocean", "water"]):
            context["setting"] = "beach"
        elif any(word in message_lower for word in ["bedroom", "bed", "sleep"]):
            context["setting"] = "bedroom" 
        elif any(word in message_lower for word in ["bathroom", "shower", "bath"]):
            context["setting"] = "bathroom"
        elif any(word in message_lower for word in ["kitchen", "cooking", "food"]):
            context["setting"] = "kitchen"
        elif any(word in message_lower for word in ["outside", "park", "garden", "outdoor"]):
            context["setting"] = "outdoor"
        
        # Analyze mood
        if any(word in message_lower for word in ["happy", "excited", "fun", "joy"]):
            context["mood"] = "happy"
        elif any(word in message_lower for word in ["romantic", "love", "sweet"]):
            context["mood"] = "romantic"
        elif any(word in message_lower for word in ["seductive", "flirty", "playful"]):
            context["mood"] = "seductive"
        elif any(word in message_lower for word in ["tired", "sleepy", "exhausted"]):
            context["mood"] = "sleepy"
        
        # Analyze time
        if any(word in message_lower for word in ["morning", "wake up", "breakfast"]):
            context["time_of_day"] = "morning"
        elif any(word in message_lower for word in ["evening", "dinner", "sunset"]):
            context["time_of_day"] = "evening" 
        elif any(word in message_lower for word in ["night", "sleep", "bed", "late"]):
            context["time_of_day"] = "night"
        
        return context
    
    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate image prompt based on context"""
        character_name = context["character"]
        
        # Get character style
        character_style = self.character_styles.get(character_name, self.character_styles["luna"])
        
        # Get clothing
        clothing = self.clothing_levels[context["clothing_level"]]
        
        # Build setting - beautiful anime backgrounds
        setting_prompts = {
            "bedroom": "cozy anime bedroom, soft bed, warm lighting, beautiful interior, romantic atmosphere",
            "bathroom": "modern anime bathroom, clean tiles, soft lighting, elegant design",
            "kitchen": "modern anime kitchen, clean counter, natural lighting, homey atmosphere", 
            "beach": "beautiful anime beach, ocean waves, sunny day, tropical paradise, summer vibes",
            "outdoor": "beautiful anime outdoor setting, natural environment, scenic landscape, peaceful atmosphere",
            "indoor": "comfortable anime indoor setting, soft lighting, cozy atmosphere, beautiful interior"
        }
        setting = setting_prompts.get(context["setting"], setting_prompts["indoor"])
        
        # Build mood/pose - beautiful anime expressions
        mood_prompts = {
            "happy": "bright anime smile, cheerful expression, joyful pose, sparkling eyes, happy mood, beautiful face",
            "romantic": "soft anime smile, loving expression, gentle pose, dreamy eyes, romantic mood, beautiful features",
            "seductive": "alluring anime smile, confident expression, elegant pose, captivating eyes, seductive mood, stunning beauty", 
            "sleepy": "sleepy anime expression, relaxed pose, comfortable, peaceful eyes, calm mood, beautiful face",
            "friendly": "warm anime smile, welcoming expression, natural pose, kind eyes, friendly mood, attractive features"
        }
        mood = mood_prompts.get(context["mood"], mood_prompts["friendly"])
        
        # Build time lighting - beautiful anime lighting
        time_lighting = {
            "morning": "soft morning light, golden hour, warm glow, beautiful sunrise atmosphere",
            "evening": "warm evening light, sunset glow, romantic lighting, magical atmosphere",
            "night": "soft night lighting, cozy atmosphere, dreamy moonlight, peaceful night",
            "day": "natural daylight, bright and clear, beautiful sunshine, vibrant atmosphere"
        }
        lighting = time_lighting.get(context["time_of_day"], time_lighting["day"])
        
        # Combine everything - beautiful anime style
        prompt = f"{self.base_anime_style}, {character_style}, {clothing}, {setting}, {mood}, {lighting}, beautiful anime artwork, professional illustration, perfect anatomy, attractive features, stunning beauty, safe for work, tasteful, no nudity, no explicit content, fully clothed, modest, appropriate, masterpiece, best quality, ultra detailed"
        
        return prompt
    
    def get_auto_image_prompt(self, message: str, character_name: str = "luna") -> Optional[str]:
        """Get automatic image prompt if context warrants it"""
        if not self.should_generate_image(message, character_name):
            return None
        
        context = self.analyze_context(message, character_name)
        return self.generate_prompt(context)
    
    def get_manual_image_prompt(self, user_prompt: str, character_name: str = "luna") -> str:
        """Get manual image prompt when user specifically requests image"""
        # Clean user prompt
        clean_prompt = user_prompt.lower()
        
        # Remove trigger words
        trigger_words = ["create", "generate", "make", "draw", "show", "image", "picture", "photo"]
        for word in trigger_words:
            clean_prompt = re.sub(rf'\b{word}\b', '', clean_prompt)
        
        clean_prompt = clean_prompt.strip()
        
        # If user gave specific description, use it with safety
        if clean_prompt:
            character_style = self.character_styles.get(character_name.lower(), self.character_styles["luna"])
            return f"{self.base_anime_style}, {character_style}, {clean_prompt}, beautiful anime artwork, professional illustration, perfect anatomy, attractive features, stunning beauty, safe for work, tasteful, no nudity, no explicit content, fully clothed, modest, appropriate"
        
        # Otherwise use context analysis
        context = self.analyze_context(user_prompt, character_name)
        return self.generate_prompt(context)
    
    def get_negative_prompt(self) -> str:
        """Get negative prompt to avoid unwanted content"""
        return "nude, naked, explicit, pornographic, sexual, inappropriate, blur, censored, low quality, distorted, ugly, deformed, bad anatomy, extra limbs, missing limbs, floating limbs, mutated hands and feet, out of frame, extra limbs, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, mutated hands, fused fingers, too many fingers, long neck"
