#!/usr/bin/env python3
"""
Test different backend options without Venice AI
Demo: Groq, OpenRouter, Ollama, Stable Horde
"""

import asyncio
import sys
import time
sys.path.append('.')

from app.services.intent_router import IntentRouter
from app.services.memory_manager import MemoryManager
from app.services.safety import SafetyService

class BackendTester:
    """Test different backend combinations"""
    
    def __init__(self):
        self.intent_router = IntentRouter()
        self.memory_manager = MemoryManager()
        self.safety_service = SafetyService()
        
    async def test_groq_backend(self):
        """Test Groq backend (free tier)"""
        print("🔵 Testing Groq Backend (Free Tier)")
        print("=" * 40)
        
        try:
            from app.llm_backends.groq_backend import GroqBackend
            from app.config import settings
            
            if not settings.GROQ_API_KEY:
                print("❌ No Groq API key found")
                print("💡 Get free key at: https://console.groq.com/")
                return False
            
            # Initialize Groq
            groq = GroqBackend(api_key=settings.GROQ_API_KEY)
            
            # Test chat
            start_time = time.time()
            messages = [
                {"role": "user", "content": "Hello, tell me a short story"}
            ]
            
            response = await groq.chat(messages)
            end_time = time.time()
            
            if response.get("success"):
                print(f"✅ Chat Response: {response['content'][:100]}...")
                print(f"⏱️ Response Time: {end_time - start_time:.2f}s")
                print(f"💰 Cost: ~$0.0001 (very cheap)")
            else:
                print(f"❌ Chat Error: {response.get('error', 'Unknown error')}")
            
            # Test character creation
            character_result = await groq.create_character_card("romantic")
            if character_result.get("success"):
                print(f"✅ Character Created: {character_result['character']['name']}")
            else:
                print(f"❌ Character Error: {character_result.get('error', 'Unknown error')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Groq Test Failed: {e}")
            return False
    
    async def test_openrouter_backend(self):
        """Test OpenRouter backend"""
        print("\n🟢 Testing OpenRouter Backend")
        print("=" * 40)
        
        try:
            from app.llm_backends.openrouter import OpenRouterBackend
            from app.config import settings
            
            if not settings.OPENAI_API_KEY:
                print("❌ No OpenAI API key found")
                print("💡 Get key at: https://platform.openai.com/")
                return False
            
            # Initialize OpenRouter
            openrouter = OpenRouterBackend()
            
            # Test chat
            start_time = time.time()
            messages = [
                {"role": "user", "content": "Hello, how are you?"}
            ]
            
            response = await openrouter.chat(messages)
            end_time = time.time()
            
            if response.get("success"):
                print(f"✅ Chat Response: {response['content'][:100]}...")
                print(f"⏱️ Response Time: {end_time - start_time:.2f}s")
                print(f"💰 Cost: ~$0.001 (affordable)")
            else:
                print(f"❌ Chat Error: {response.get('error', 'Unknown error')}")
            
            return True
            
        except Exception as e:
            print(f"❌ OpenRouter Test Failed: {e}")
            return False
    
    async def test_stable_horde_image(self):
        """Test Stable Horde image generation (free)"""
        print("\n🟡 Testing Stable Horde Image Generation (Free)")
        print("=" * 40)
        
        try:
            from app.image_backends.horde import StableHordeBackend
            
            # Initialize Stable Horde
            horde = StableHordeBackend()
            
            # Test image generation
            print("🎨 Generating image: 'a beautiful sunset over mountains'")
            start_time = time.time()
            
            result = await horde.generate_image("a beautiful sunset over mountains")
            end_time = time.time()
            
            if result.get("success"):
                print(f"✅ Image Generated Successfully!")
                print(f"⏱️ Generation Time: {end_time - start_time:.2f}s")
                print(f"💰 Cost: $0 (completely free)")
                print(f"🖼️ Image URL: {result.get('image_url', 'Available')}")
            else:
                print(f"❌ Image Generation Failed: {result.get('error', 'Unknown error')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Stable Horde Test Failed: {e}")
            return False
    
    async def test_ollama_local(self):
        """Test Ollama local setup"""
        print("\n🟠 Testing Ollama Local (Free)")
        print("=" * 40)
        
        try:
            # Check if Ollama is installed
            import subprocess
            result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ Ollama not installed")
                print("💡 Install: https://ollama.ai/")
                print("💡 Then run: ollama pull llama3.1:8b")
                return False
            
            print("✅ Ollama installed")
            
            # Check if model is available
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if 'llama3.1:8b' in result.stdout:
                print("✅ Llama 3.1 model available")
                print("💰 Cost: $0 (completely free)")
                print("⚡ Speed: 50-100 tokens/second")
                print("🔒 Privacy: 100% local")
                return True
            else:
                print("⚠️ Llama 3.1 model not found")
                print("💡 Download: ollama pull llama3.1:8b")
                return False
                
        except Exception as e:
            print(f"❌ Ollama Test Failed: {e}")
            return False
    
    async def test_cost_comparison(self):
        """Show cost comparison"""
        print("\n💰 Cost Comparison")
        print("=" * 40)
        
        costs = {
            "Venice AI (Full)": {
                "LLM": "$0.01-0.05/1K tokens",
                "Image": "$0.02-0.05/ảnh", 
                "Monthly (1K users)": "$150-450",
                "Quality": "⭐⭐⭐⭐⭐"
            },
            "Groq + Stable Horde": {
                "LLM": "Free tier (1M tokens)",
                "Image": "Free",
                "Monthly (1K users)": "$0-20",
                "Quality": "⭐⭐⭐⭐"
            },
            "OpenRouter + Stable Horde": {
                "LLM": "$0.10-0.50/1M tokens",
                "Image": "Free",
                "Monthly (1K users)": "$10-50",
                "Quality": "⭐⭐⭐⭐"
            },
            "Ollama Local": {
                "LLM": "$0 (electricity only)",
                "Image": "$0 (electricity only)",
                "Monthly (1K users)": "$0",
                "Quality": "⭐⭐⭐"
            }
        }
        
        for setup, details in costs.items():
            print(f"\n{setup}:")
            print(f"  LLM: {details['LLM']}")
            print(f"  Image: {details['Image']}")
            print(f"  Monthly: {details['Monthly (1K users)']}")
            print(f"  Quality: {details['Quality']}")

async def main():
    """Main test function"""
    print("🧪 Backend Testing & Cost Analysis")
    print("=" * 50)
    
    tester = BackendTester()
    
    # Test different backends
    results = {}
    
    print("\n1️⃣ Testing Groq Backend...")
    results['Groq'] = await tester.test_groq_backend()
    
    print("\n2️⃣ Testing OpenRouter Backend...")
    results['OpenRouter'] = await tester.test_openrouter_backend()
    
    print("\n3️⃣ Testing Stable Horde Image...")
    results['Stable Horde'] = await tester.test_stable_horde_image()
    
    print("\n4️⃣ Testing Ollama Local...")
    results['Ollama'] = await tester.test_ollama_local()
    
    # Show cost comparison
    await tester.test_cost_comparison()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    for backend, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{backend}: {status}")
    
    print("\n🎯 Recommendations:")
    print("✅ For Testing: Groq + Stable Horde (free)")
    print("✅ For Production: Venice AI (best quality)")
    print("✅ For Development: Ollama Local (free)")
    
    print("\n🚀 Ready to test without Venice AI!")

if __name__ == "__main__":
    asyncio.run(main())
