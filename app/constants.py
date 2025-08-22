"""
Constants and configuration values for the chatbot
Centralized to avoid hard coding and make maintenance easier
"""

# Memory Configuration
MEMORY_CONFIG = {
    "MAX_RECENT_MESSAGES": 5,
    "MAX_SUMMARY_LENGTH": 100,
    "SUMMARY_THRESHOLD": 10,
    "MAX_FACTS_PER_USER": 50,
    "CLEANUP_DAYS": 7
}

# Intent Classification
INTENT_PATTERNS = {
    "image": [
        r"tạo\s+ảnh|generate\s+image|vẽ\s+ảnh|draw\s+picture",
        r"ảnh\s+của|picture\s+of|photo\s+of",
        r"show\s+me|cho\s+tôi\s+xem",
        r"create\s+.*\s+image|create\s+.*\s+picture",
        r"🎨|🖼️|📸|📷"
    ],
    "roleplay": [
        r"roleplay|nhập\s+vai|đóng\s+vai",
        r"character|nhân\s+vật|persona",
        r"be\s+my|act\s+as|pretend\s+to\s+be",
        r"create\s+character|tạo\s+nhân\s+vật",
        r"🎭|👤|🎪"
    ],
    "help": [
        r"help|giúp|hướng\s+dẫn|tutorial",
        r"how\s+to|làm\s+sao|cách\s+dùng",
        r"commands|lệnh|menu",
        r"❓|❔|💡|📖"
    ],
    "settings": [
        r"settings|cài\s+đặt|config|tùy\s+chọn",
        r"preferences|ưu\s+tiên|option",
        r"change|thay\s+đổi|modify",
        r"⚙️|🔧|🎛️"
    ],
    "chat": [
        r"hello|hi|chào|xin\s+chào",
        r"how\s+are\s+you|bạn\s+khỏe\s+không",
        r"bye|tạm\s+biệt|goodbye",
        r"💬|🗨️|💭"
    ]
}

INTENT_KEYWORDS = {
    "image": ["ảnh", "image", "picture", "photo", "draw", "vẽ", "tạo", "generate", "create"],
    "roleplay": ["roleplay", "character", "nhân vật", "đóng vai", "persona", "act"],
    "help": ["help", "giúp", "hướng dẫn", "tutorial", "commands", "lệnh"],
    "settings": ["settings", "cài đặt", "config", "tùy chọn", "preferences"],
    "chat": ["hello", "hi", "chào", "bye", "tạm biệt", "how are you"]
}

# Safety Configuration
SAFETY_CONFIG = {
    "UNSAFE_KEYWORDS": [
        "child", "minor", "teen", "underage", "pedo",
        "violence", "gore", "blood", "weapon"
    ],
    "AGE_VERIFICATION_REQUIRED": True,
    "MIN_AGE": 18,
    "MAX_RISK_LEVEL": 3
}

# LLM Configuration
LLM_CONFIG = {
    "DEFAULT_TEMPERATURE": 0.9,
    "MAX_TOKENS": 1000,
    "TIMEOUT_SECONDS": 30,
    "RETRY_ATTEMPTS": 3,
    "RETRY_MIN_WAIT": 1,
    "RETRY_MAX_WAIT": 8
}

# Groq Models
GROQ_MODELS = {
    "llama3.1-8b": "llama-3.1-8b-instant",
    "llama3.1-70b": "llama-3.1-70b-versatile", 
    "deepseek": "deepseek-llm-67b-chat",
    "mixtral": "mixtral-8x7b-32768"
}

# Image Generation
IMAGE_CONFIG = {
    "DEFAULT_SIZE": "768x768",
    "DEFAULT_STYLE": "realistic",
    "TIMEOUT_SECONDS": 120,
    "POLLING_INTERVAL": 5,
    "MAX_POLLING_ATTEMPTS": 36
}

# Character Templates
CHARACTER_TEMPLATES = {
    "seductive": {
        "name": "Luna",
        "persona": "A mysterious and alluring woman with a playful personality. She enjoys deep conversations and has a seductive charm.",
        "boundaries": "Respectful and consensual interactions only. No explicit content.",
        "scenario": "Meeting in a cozy café for an intimate conversation.",
        "greeting": "Hello there, handsome. I've been waiting for someone interesting to talk to.",
        "image_prompt": "Beautiful woman with long dark hair, seductive smile, elegant dress",
        "tags": ["seductive", "mysterious", "charming"]
    },
    "romantic": {
        "name": "Sophia",
        "persona": "A romantic and caring woman who believes in true love and meaningful connections.",
        "boundaries": "Romantic but respectful. Focus on emotional connection.",
        "scenario": "A romantic dinner date under the stars.",
        "greeting": "Hi there! I'm so glad we could spend this evening together.",
        "image_prompt": "Romantic woman with soft features, warm smile, elegant evening wear",
        "tags": ["romantic", "caring", "elegant"]
    },
    "adventurous": {
        "name": "Zara",
        "persona": "An adventurous and energetic woman who loves excitement and new experiences.",
        "boundaries": "Fun and flirty but appropriate. No explicit content.",
        "scenario": "Meeting at an exciting outdoor adventure location.",
        "greeting": "Hey! Ready for some excitement? I love meeting adventurous people!",
        "image_prompt": "Athletic woman with confident pose, adventurous spirit, outdoor setting",
        "tags": ["adventurous", "energetic", "confident"]
    }
}

# Response Templates
RESPONSE_TEMPLATES = {
    "greeting": "Hi there! How can I help you today?",
    "farewell": "Goodbye! Have a great day!",
    "help": "I'm here to chat with you. What would you like to talk about?",
    "image_fallback": "I'd love to generate an image for you, but I'm currently using a free model that doesn't support image generation.",
    "roleplay": "I can engage in roleplay conversations with you. What character would you like me to be?",
    "error": "❌ Sorry, something went wrong. Please try again.\nIf the problem persists, contact support.",
    "age_verification": "⚠️ This bot is for adults only (18+).\n\nPlease verify your age in Telegram settings and try again.\nYou must be 18 or older to use this bot.",
    "content_blocked": "⚠️ Message blocked: {reason}\n\nPlease review our content guidelines and try again.",
    "image_generating": "🎨 Generating image... Please wait.",
    "image_safety": "⚠️ Image generation blocked due to safety concerns.",
    "character_created": "🎭 Created {name} for you!\n\n**Persona:** {persona}...\n**Style:** {style}\n**NSFW Level:** {nsfw_level}/5\n\nStart chatting with {name}!",
    "character_failed": "❌ Failed to create character. Please try again.",
    "image_failed": "❌ Failed to generate image. Please try again."
}

# Keyboard Layouts
KEYBOARD_LAYOUTS = {
    "main": [
        ["🎭 Create Character", "🖼️ Generate Image"],
        ["⚙️ Settings", "❓ Help"]
    ],
    "settings": [
        ["🔙 Back", "💎 Shop"],
        ["📊 Stats", "🛡️ Safety"]
    ],
    "back": [
        ["🔙 Back to Main"]
    ]
}

# Database Configuration
DB_CONFIG = {
    "MAX_MESSAGE_LENGTH": 4096,
    "MAX_META_DATA_SIZE": 1024,
    "SESSION_TIMEOUT_HOURS": 24
}

# Logging Configuration
LOG_CONFIG = {
    "DEFAULT_LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "MAX_LOG_SIZE": 10 * 1024 * 1024,  # 10MB
    "BACKUP_COUNT": 5
}

# API Endpoints
API_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1",
    "stable_horde": "https://stablehorde.net/api/v2",
    "replicate": "https://api.replicate.com/v1",
    "huggingface": "https://api-inference.huggingface.co/models/",
    "ollama": "http://localhost:11434"
}

# Error Messages
ERROR_MESSAGES = {
    "api_timeout": "API request timed out. Please try again.",
    "api_rate_limit": "Rate limit exceeded. Please wait a moment.",
    "api_unauthorized": "API key is invalid or expired.",
    "database_connection": "Database connection failed.",
    "memory_full": "Memory storage is full. Cleaning up...",
    "invalid_input": "Invalid input provided.",
    "service_unavailable": "Service temporarily unavailable."
}

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    "MAX_RESPONSE_TIME_MS": 5000,
    "MAX_MEMORY_USAGE_MB": 500,
    "MAX_DB_QUERY_TIME_MS": 1000,
    "MAX_CONTEXT_LENGTH": 2000
}
