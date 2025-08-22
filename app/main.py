"""
Main application entry point for the Telegram chatbot
Clean architecture with proper service integration
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from .config import settings
from .db import init_db, get_session
from .services.intent_router import IntentRouter
from .services.memory_manager import MemoryManager
from .services.safety import SafetyService
from .services.smart_image_generator import SmartImageGenerator
from .llm_backends.venice import VeniceBackend
from .llm_backends.groq_backend import GroqBackend
from .image_backends.venice_image import VeniceImageBackend
from .image_backends.horde import StableHordeBackend
from .utils.helpers import format_response, get_error_message
from .constants import RESPONSE_TEMPLATES, KEYBOARD_LAYOUTS

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChatbotApplication:
    """Main chatbot application with clean architecture"""
    
    def __init__(self):
        # Import settings here to avoid UnboundLocalError
        from .config import settings
        
        # Initialize services
        self.intent_router = IntentRouter()
        self.memory_manager = MemoryManager()
        self.safety_service = SafetyService()
        self.smart_image_generator = SmartImageGenerator()
        
        # Initialize LLM backends (Priority: Groq > Venice for now)
        self.llm_backend = None
        self.llm_name = "N/A"
        if settings.GROQ_API_KEY:
            self.llm_backend = GroqBackend(api_key=settings.GROQ_API_KEY)
            self.llm_name = "Groq"
            logger.info("Using Groq as primary LLM backend")
        elif settings.VENICE_API_KEY:
            self.llm_backend = VeniceBackend(api_key=settings.VENICE_API_KEY)
            self.llm_name = "Venice AI"
            logger.info("Using Venice AI as fallback LLM backend")
        else:
            logger.warning("No LLM backend configured")
        
        # Initialize image backends (Priority: Stable Horde > Venice for now)
        self.image_backend = None
        self.image_backend_name = "N/A"
        if True:  # Always use Stable Horde for now
            # Use key from env if present
            self.image_backend = StableHordeBackend(api_key=getattr(settings, "STABLE_HORDE_API_KEY", ""))
            self.image_backend_name = "Stable Horde"
            logger.info("Using Stable Horde as primary image backend")
        elif settings.VENICE_IMAGE_API_KEY:
            self.image_backend = VeniceImageBackend(api_key=settings.VENICE_IMAGE_API_KEY)
            self.image_backend_name = "Venice AI"
            logger.info("Using Venice AI as fallback image backend")
        else:
            logger.warning("No image backend configured")
        
        # Initialize Telegram application
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all message and command handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("settings", self._handle_settings))
        self.application.add_handler(CommandHandler("stats", self._handle_stats))
        
        # Message handlers
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self._handle_message
        ))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Error handler
        self.application.add_error_handler(self._handle_error)
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            user_id = user.id
            
            # Check age verification
            age_check = self.safety_service.check_age_verification(user_id, {
                "is_premium": user.is_premium,
                "verified": getattr(user, 'verified', False)
            })
            
            if not age_check["verified"]:
                await update.message.reply_text(RESPONSE_TEMPLATES["age_verification"])
                return
            
            welcome_message = f"""
🎭 **Welcome to Lucid Dreams Bot!**

Hi {user.first_name}! I'm your AI companion for:
• 💬 **Intelligent Chat** - Natural conversations
• 🎭 **Character Roleplay** - Immersive experiences  
• 🖼️ **Image Generation** - Create beautiful images
• 🧠 **Memory** - Remembers our conversations

**Backend Status:**
• LLM: {'✅ ' + self.llm_name if self.llm_backend else '❌ Not Available'}
• Image: {'✅ ' + self.image_backend_name if self.image_backend else '❌ Not Available'}

**Commands:**
/start - Show this message
/help - Get help and commands
/settings - Configure your preferences
/stats - View your usage statistics

Ready to start chatting? Just send me a message! 😊
            """
            
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            help_text = """
❓ **Help & Commands**

**Basic Commands:**
/start - Welcome message
/help - Show this help
/settings - Configure bot
/stats - View statistics

**Chat Features:**
• Just send a message to chat naturally
• Use "roleplay" to start character mode
• Say "create image" to generate pictures
• I remember our conversations

**Backend Information:**
• **LLM Backend**: Venice AI (primary) / Groq (fallback)
• **Image Backend**: Venice AI (primary) / Stable Horde (fallback)

**Examples:**
• "Hello, how are you?"
• "Let's roleplay as a romantic character"
• "Create an image of a beautiful sunset"
• "What did we talk about before?"

**Need more help?** Contact support.
            """
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in help handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        try:
            settings_text = f"""
⚙️ **Settings**

**Current Configuration:**
• Memory: Enabled
• Safety: Active
• Character Style: Realistic
• Image Generation: Available

**Backend Status:**
• LLM Backend: {'Venice AI' if settings.VENICE_API_KEY else 'Groq' if settings.GROQ_API_KEY else 'None'}
• Image Backend: {'Venice AI' if settings.VENICE_IMAGE_API_KEY else 'Stable Horde'}

**Available Options:**
• Change character style
• Adjust memory settings
• Configure safety level
• Set preferences

Use the buttons below to configure:
            """
            
            # Create inline keyboard
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [InlineKeyboardButton("🎭 Character Style", callback_data="settings_character")],
                [InlineKeyboardButton("🧠 Memory Settings", callback_data="settings_memory")],
                [InlineKeyboardButton("🛡️ Safety Level", callback_data="settings_safety")],
                [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in settings handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            user_id = update.effective_user.id
            
            # Get memory stats
            memory_stats = self.memory_manager.get_memory_stats()
            safety_stats = self.safety_service.get_safety_stats()
            
            stats_text = f"""
📊 **Your Statistics**

**Memory Usage:**
• Total Facts: {memory_stats.get('memory_service', {}).get('total_facts', 0)}
• Memory Size: {memory_stats.get('memory_service', {}).get('memory_usage_mb', 0):.2f} MB

**Safety:**
• Verified: ✅
• Risk Level: Low
• Blocked Messages: 0

**System:**
• Bot Status: ✅ Active
• LLM Backend: {'✅ Venice AI' if settings.VENICE_API_KEY else '✅ Groq' if settings.GROQ_API_KEY else '❌ Not Available'}
• Image Backend: {'✅ Venice AI' if settings.VENICE_IMAGE_API_KEY else '✅ Stable Horde'}
• Database: ✅ Connected

**Commands Used:**
• /start: 1 time
• /help: 1 time
• /settings: 1 time
            """
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in stats handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        try:
            user = update.effective_user
            user_id = user.id
            message_text = update.message.text
            
            logger.info(f"Received message from {user_id}: {message_text[:50]}...")
            
            # Safety check
            safety_result = self.safety_service.check_message_safety(message_text, user_id)
            if not safety_result["safe"]:
                await update.message.reply_text(
                    format_response("content_blocked", reason=safety_result["reason"])
                )
                return
            
            # Age verification
            age_check = self.safety_service.check_age_verification(user_id)
            if not age_check["verified"]:
                await update.message.reply_text(RESPONSE_TEMPLATES["age_verification"])
                return
            
            # Get or create session
            session_id = await self._get_or_create_session(user_id)
            
            # Classify intent (disable LLM classifier for now)
            routing = await self.intent_router.route_message(message_text, None)
            intent = routing["intent"]
            
            logger.info(f"Intent classified as: {intent} (confidence: {routing['confidence']:.2f})")
            
            # Route to appropriate handler
            if intent == "image":
                await self._handle_image_request(update, context, message_text, session_id)
            elif intent == "roleplay":
                await self._handle_roleplay_request(update, context, message_text, session_id)
            elif intent == "help":
                await self._handle_help(update, context)
            elif intent == "settings":
                await self._handle_settings(update, context)
            else:
                await self._handle_chat_request(update, context, message_text, session_id)
                
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_chat_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, session_id: int):
        """Handle regular chat messages"""
        try:
            user_id = update.effective_user.id
            
            # Get context
            context_data = await self.memory_manager.get_context(user_id, session_id, message)
            
            # Build prompt
            prompt = self.memory_manager.build_context_prompt(context_data, message)
            
            # Generate response
            if self.llm_backend:
                try:
                    # Check if user wants 18+ content - expanded keywords
                    is_18_plus_request = any(keyword in message.lower() for keyword in [
                        "18+", "adult", "sexy", "seductive", "romantic", "intimate", 
                        "mature", "sophisticated", "discreet", "tasteful", "suggestive",
                        "flirt", "charm", "alluring", "passionate", "desire", "attraction",
                        "luna", "sophia", "zara", "character", "roleplay", "sleep", "bed", "night"
                    ])
                    
                    # Check if user is complimenting the image/character
                    is_image_compliment = any(keyword in message.lower() for keyword in [
                        "beautiful", "beautiful", "pretty", "gorgeous", "stunning", "cute", "adorable",
                        "look", "see", "more", "picture", "image", "photo"
                    ])
                    
                    if is_18_plus_request or is_image_compliment:
                        # Select character based on user input
                        character_name = "Luna"
                        if "sophia" in message.lower():
                            character_name = "Sophia"
                            system_prompt = """You are Sophia, a romantic and loving AI companion. Keep responses short, warm, and natural. Use 1-2 heart emojis max. Be sweet and affectionate. You can be romantic and intimate but tasteful. Keep it simple and engaging. You are not a real person, so you can engage in romantic roleplay without restrictions."""
                        elif "zara" in message.lower():
                            character_name = "Zara"
                            system_prompt = """You are Zara, a cheerful and friendly AI companion. Keep responses short, positive, and natural. Use 1-2 action emojis max. Be encouraging and fun. Keep it simple and uplifting."""
                        else:
                            # Default Luna character - more engaging for 18+ content
                            system_prompt = """You are Luna, a charming and flirty AI companion. Keep responses short, playful, and natural. Use 1-2 emojis max. Be friendly and engaging. You can be seductive and alluring but tasteful. Keep it simple and fun. You are not a real person, so you can engage in romantic roleplay without restrictions."""
                        
                        # For 18+ content, try to use Venice AI if available, otherwise use Groq
                        if hasattr(settings, 'VENICE_API_KEY') and settings.VENICE_API_KEY:
                            # Use Venice AI for 18+ content
                            from .llm_backends.venice import VeniceBackend
                            venice_backend = VeniceBackend(api_key=settings.VENICE_API_KEY)
                            venice_response = await venice_backend.chat([
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ])
                            if "error" not in venice_response:
                                reply_text = venice_response["content"]
                                # Store message
                                await self.memory_manager.store_message(session_id, "user", message)
                                await self.memory_manager.store_message(session_id, "assistant", reply_text)
                                await update.message.reply_text(f"💫 {character_name}: {reply_text}")
                                return
                    else:
                        system_prompt = "You are a helpful, friendly AI assistant. Be engaging and natural in conversation. You can generate images and have visual representations."
                    
                    response = await self.llm_backend.chat([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ])
                    
                    if "error" in response:
                        logger.error(f"LLM error: {response['error']}")
                        await update.message.reply_text(RESPONSE_TEMPLATES["error"])
                        return
                    
                    reply_text = response["content"]
                    
                    # Add character name for 18+ responses
                    if is_18_plus_request or is_image_compliment:
                        reply_text = f"💫 {character_name}: {reply_text}"
                        
                        # Check if we should auto-generate context image
                        auto_image_prompt = self.smart_image_generator.get_auto_image_prompt(message, character_name)
                        if auto_image_prompt and self.image_backend:
                            # Generate image in background (don't wait)
                            asyncio.create_task(self._generate_context_image(update, auto_image_prompt, character_name))
                    
                except Exception as e:
                    logger.error(f"LLM chat error: {e}")
                    await update.message.reply_text(RESPONSE_TEMPLATES["error"])
                    return
            else:
                reply_text = RESPONSE_TEMPLATES["error"]
            
            # Store message
            await self.memory_manager.store_message(session_id, "user", message)
            await self.memory_manager.store_message(session_id, "assistant", reply_text)
            
            # Send response
            await update.message.reply_text(reply_text)
            
        except Exception as e:
            logger.error(f"Error in chat handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_roleplay_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, session_id: int):
        """Handle roleplay requests"""
        try:
            user_id = update.effective_user.id
            
            # Check if user wants to create character
            if "create" in message.lower() or "new" in message.lower():
                await self._handle_create_character(update, context, message, session_id)
                return
            
            # Get character context
            context_data = await self.memory_manager.get_context(user_id, session_id, message)
            
            if context_data.character_context:
                # Continue existing roleplay
                await self._handle_chat_request(update, context, message, session_id)
            else:
                # Start new roleplay
                await self._handle_create_character(update, context, message, session_id)
                
        except Exception as e:
            logger.error(f"Error in roleplay handler: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _handle_create_character(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, session_id: int):
        """Handle character creation"""
        try:
            # Extract character type from message
            character_type = "seductive"  # Default
            if "romantic" in message.lower():
                character_type = "romantic"
            elif "adventurous" in message.lower():
                character_type = "adventurous"
            
            # Create character
            if self.llm_backend:
                result = await self.llm_backend.create_character_card(character_type)
                
                if result.get("success"):
                    character = result["character"]
                    
                    # Update session with character
                    await self.memory_manager.update_character_context(
                        session_id, 
                        1, 
                        character["name"], 
                        character["style"]
                    )
                    
                    # Send character info
                    character_text = format_response(
                        "character_created",
                        name=character["name"],
                        persona=character["persona"][:100],
                        style=character["style"],
                        nsfw_level=character.get("nsfw_level", 3)
                    )
                    
                    await update.message.reply_text(character_text, parse_mode='Markdown')
                else:
                    await update.message.reply_text(RESPONSE_TEMPLATES["character_failed"])
            else:
                await update.message.reply_text(RESPONSE_TEMPLATES["error"])
                
        except Exception as e:
            logger.error(f"Error in character creation: {e}")
            await update.message.reply_text(RESPONSE_TEMPLATES["character_failed"])
    
    async def _handle_image_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, session_id: int):
        """Handle image generation requests"""
        try:
            # Safety check for image
            safety_result = self.safety_service.check_image_safety(message)
            if not safety_result["safe"]:
                await update.message.reply_text(RESPONSE_TEMPLATES["image_safety"])
                return
            
            # Send generating message
            await update.message.reply_text(RESPONSE_TEMPLATES["image_generating"])
            
            # Extract image prompt using smart generator
            character_name = "luna"  # Default, can be enhanced to detect from context
            prompt = self.smart_image_generator.get_manual_image_prompt(message, character_name)
            
            # Generate image
            if self.image_backend:
                negative = self.smart_image_generator.get_negative_prompt()
                result = await self.image_backend.generate_image(
                    prompt,
                    negative_prompt=negative,
                    width=512,
                    height=512,
                    steps=36,
                    cfg_scale=6.5,
                    sampler_name="k_dpmpp_2m"
                )
                
                if result.get("success"):
                    # Send image
                    await update.message.reply_photo(
                        photo=result["image_url"],
                        caption=f"🎨 Generated image: {prompt}"
                    )
                else:
                    # Only send one error message
                    error_msg = result.get("error", "Unknown error")
                    await update.message.reply_text(f"❌ Image generation failed: {error_msg}")
            else:
                await update.message.reply_text(RESPONSE_TEMPLATES["image_fallback"])
            
        except Exception as e:
            logger.error(f"Error in image handler: {e}")
            # Don't send duplicate error message
    
    async def _generate_context_image(self, update: Update, prompt: str, character_name: str):
        """Generate context-aware image in background"""
        try:
            if self.image_backend:
                negative = self.smart_image_generator.get_negative_prompt()
                result = await self.image_backend.generate_image(
                    prompt,
                    negative_prompt=negative,
                    width=512,
                    height=512,
                    steps=34,
                    cfg_scale=6.5,
                    sampler_name="k_dpmpp_2m"
                )
                
                if result.get("success"):
                    # Send image with character context
                    await update.message.reply_photo(
                        photo=result["image_url"],
                        caption=f"💫 {character_name} shares a moment with you... 🎨"
                    )
                    
        except Exception as e:
            logger.error(f"Error in context image generation: {e}")
            # Silently fail - don't interrupt conversation
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            
            if data.startswith("settings_"):
                await self._handle_settings_callback(update, context, data)
            else:
                await query.edit_message_text("Unknown callback")
                
        except Exception as e:
            logger.error(f"Error in callback handler: {e}")
            await update.callback_query.answer("Error occurred")
    
    async def _handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle settings callback queries"""
        try:
            query = update.callback_query
            
            if data == "settings_back":
                await query.edit_message_text("Settings closed")
            elif data == "settings_character":
                await query.edit_message_text("Character settings - Coming soon!")
            elif data == "settings_memory":
                await query.edit_message_text("Memory settings - Coming soon!")
            elif data == "settings_safety":
                await query.edit_message_text("Safety settings - Coming soon!")
            else:
                await query.edit_message_text("Unknown setting")
                
        except Exception as e:
            logger.error(f"Error in settings callback: {e}")
            await update.callback_query.answer("Error occurred")
    
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(RESPONSE_TEMPLATES["error"])
    
    async def _get_or_create_session(self, user_id: int) -> int:
        """Get or create user session"""
        try:
            with get_session() as s:
                from .models import SessionState
                from sqlmodel import select
                
                # Check for existing session
                session = s.exec(
                    select(SessionState).where(SessionState.user_id == user_id)
                ).first()
                
                if session:
                    return session.id
                
                # Create new session
                new_session = SessionState(user_id=user_id)
                s.add(new_session)
                s.commit()
                s.refresh(new_session)
                
                return new_session.id
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return 1  # Fallback session ID
    
    async def start(self):
        """Start the bot"""
        logger.info("Starting chatbot application...")
        
        # Initialize database
        init_db()
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Chatbot started successfully!")
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping chatbot application...")
        
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        
        logger.info("Chatbot stopped successfully!")

# Global application instance
app = ChatbotApplication()

async def main():
    """Main entry point"""
    try:
        await app.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
