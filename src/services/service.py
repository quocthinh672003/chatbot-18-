import uuid
import requests
from typing import Optional, List, Dict, Any, Iterator
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.language_models import BaseLanguageModel
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult, Generation
from langchain_core.prompts import BasePromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from src.config.settings import (
    REDIS_URL,
    VENICE_BASE_URL,
    VENICE_API_KEY,
    VENICE_MODEL,
    MAX_TOKEN_LIMIT,
    TEMPERATURE,
    MEMORY_K,
)


class VeniceLLM(BaseLanguageModel):
    """Venice AI API wrapper - compatible with LangChain BaseLanguageModel"""

    def __init__(
        self, base_url: str, api_key: str, model: str, temperature: float = 0.5
    ):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

        # Validate required fields
        if not api_key:
            raise ValueError("VENICE_API_KEY is required")
        if not base_url:
            raise ValueError("VENICE_BASE_URL is required")

    @property
    def _llm_type(self) -> str:
        return "venice"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """For summarization - LangChain requirement"""
        return self.chat([{"role": "user", "content": prompt}])

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Required abstract method"""
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop, run_manager, **kwargs)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)

    def invoke(self, messages: List[BaseMessage]) -> str:
        """LangChain compatibility method"""
        # Convert BaseMessage to dict format
        dict_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                dict_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                dict_messages.append({"role": "assistant", "content": msg.content})
        return self.chat(dict_messages)

    def predict(self, text: str) -> str:
        """LangChain requirement - predict from text"""
        return self.chat([{"role": "user", "content": text}])

    def predict_messages(self, messages: List[BaseMessage]) -> str:
        """LangChain requirement - predict from messages"""
        return self.invoke(messages)

    def generate_prompt(self, prompt: BasePromptTemplate) -> str:
        """LangChain requirement - generate from prompt template"""
        return self.predict(prompt.to_string())

    def agenerate_prompt(self, prompt: BasePromptTemplate) -> str:
        """LangChain requirement - async version of generate_prompt"""
        return self.generate_prompt(prompt)

    def apredict(self, text: str) -> str:
        """LangChain requirement - async version of predict"""
        return self.predict(text)

    def apredict_messages(self, messages: List[BaseMessage]) -> str:
        """LangChain requirement - async version of predict_messages"""
        return self.predict_messages(messages)

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat request to Venice AI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1000,
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Venice AI API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Invalid response from Venice AI: {str(e)}")
        except Exception as e:
            raise Exception(f"Venice AI API error: {str(e)}")


class ChatService:
    """Chat service using LangChain components - ConversationSummaryBufferMemory"""

    def __init__(self):
        try:
            self.llm = VeniceLLM(
                VENICE_BASE_URL, VENICE_API_KEY, VENICE_MODEL, TEMPERATURE
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Venice LLM: {str(e)}")

    def process_chat(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat request using LangChain components as requested:

        1. RedisChatMessageHistory → store history per session (original)
        2. ConversationSummaryBufferMemory → auto summarize + keep recent window
        3. LLM Venice → call with context managed by memory
        """

        # Validate input
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        # Create session if needed
        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            # RedisChatMessageHistory → store raw messages (not lost when restart app)
            history = RedisChatMessageHistory(
                session_id=session_id, url=REDIS_URL, ttl=86400
            )

            # ConversationSummaryBufferMemory → automatically decide: keep k recent messages + old summary
            # This is the core of the original requirement!
            memory = ConversationSummaryBufferMemory(
                llm=self.llm,  # Use Venice LLM for summarization
                chat_memory=history,
                max_token_limit=MAX_TOKEN_LIMIT,  # Auto-summarize when exceed this limit
                return_messages=True,
                k=MEMORY_K,  # Keep k recent messages, older ones get summarized
            )

            # Add user message to memory
            memory.chat_memory.add_user_message(message)

            # Get context managed by memory
            # If >k messages → prompt sent includes summary of all old + k recent messages
            past_messages = memory.chat_memory.messages

            # Call LLM with context
            # Venice understands all previous context (via summary),
            # while having recent details (via k recent messages)
            messages = past_messages + [{"role": "user", "content": message}]
            response = self.llm.chat(messages)

            # Save AI response
            memory.chat_memory.add_ai_message(response)

            return {
                "session_id": session_id,
                "answer": response,
                "summary": getattr(memory, "moving_summary_buffer", None),
            }
        except Exception as e:
            raise Exception(f"Chat processing failed: {str(e)}")
