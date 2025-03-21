"""
Azure OpenAI Client
Provides integration with Azure OpenAI for text generation and analysis.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional, Union
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor

from utils.config import get_config
from utils.logging_utils import get_logger

logger = get_logger("services.azure_openai")


class AzureOpenAIClient:
    """
    Client for Azure OpenAI service.
    Provides methods for generating completions, chat completions, and embeddings.
    """
    
    def __init__(self):
        self.logger = get_logger("azure_openai")
        self._initialize_client()
        self.thread_executor = ThreadPoolExecutor(max_workers=5)
    
    def _initialize_client(self) -> None:
        """Initialize the Azure OpenAI client."""
        config = get_config()
        
        # Get Azure OpenAI credentials
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT") or \
                  config.get("openai", {}).get("endpoint")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY") or \
                 config.get("openai", {}).get("api_key")
        api_version = config.get("openai", {}).get("api_version", "2023-07-01-preview")
        
        if not endpoint or not api_key:
            self.logger.warning("Azure OpenAI credentials not found")
            self.endpoint = None
            self.api_key = None
            return
        
        # Initialize client properties
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.chat_deployment = config.get("openai", {}).get("chat_deployment", "gpt-4-turbo")
        self.embedding_deployment = config.get("openai", {}).get("embedding_deployment", "text-embedding-ada-002")
        
        self.logger.info("Azure OpenAI client initialized successfully")
    
    async def generate_completion(self, prompt: str, max_tokens: int = 1000, 
                                 temperature: float = 0.7) -> str:
        """
        Generate text completion using Azure OpenAI.
        
        Args:
            prompt: Input text to generate completion from
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            Generated text completion
        """
        if not self.endpoint or not self.api_key:
            self.logger.error("Azure OpenAI credentials not available")
            return "Azure OpenAI client not properly configured"
        
        try:
            # Prepare request
            url = f"{self.endpoint}/openai/deployments/{self.chat_deployment}/completions?api-version={self.api_version}"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            data = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "n": 1,
                "stop": None
            }
            
            # Send request using thread executor for async compatibility
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                self.thread_executor,
                lambda: requests.post(url, headers=headers, json=data)
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                completion_text = result["choices"][0]["text"]
                return completion_text
            else:
                self.logger.error(f"Error generating completion: {response.status_code} - {response.text}")
                return f"Error: {response.status_code} - {response.text}"
            
        except Exception as e:
            self.logger.error(f"Error generating completion: {str(e)}")
            return f"Error generating completion: {str(e)}"
    
    async def generate_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000,
                                      temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate chat completion using Azure OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            Dict containing generated chat completion
        """
        if not self.endpoint or not self.api_key:
            self.logger.error("Azure OpenAI credentials not available")
            return {"error": "Azure OpenAI client not properly configured"}
        
        try:
            # Prepare request
            url = f"{self.endpoint}/openai/deployments/{self.chat_deployment}/chat/completions?api-version={self.api_version}"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            data = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "n": 1,
                "stop": None
            }
            
            # Send request using thread executor for async compatibility
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                self.thread_executor,
                lambda: requests.post(url, headers=headers, json=data)
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                return {
                    "role": result["choices"][0]["message"]["role"],
                    "content": result["choices"][0]["message"]["content"],
                    "finish_reason": result["choices"][0]["finish_reason"],
                    "usage": result.get("usage", {})
                }
            else:
                self.logger.error(f"Error generating chat completion: {response.status_code} - {response.text}")
                return {"error": f"Error: {response.status_code} - {response.text}"}
            
        except Exception as e:
            self.logger.error(f"Error generating chat completion: {str(e)}")
            return {"error": f"Error generating chat completion: {str(e)}"}
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate text embeddings using Azure OpenAI.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        if not self.endpoint or not self.api_key:
            self.logger.error("Azure OpenAI credentials not available")
            return []
        
        try:
            # Prepare request
            url = f"{self.endpoint}/openai/deployments/{self.embedding_deployment}/embeddings?api-version={self.api_version}"
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            data = {
                "input": texts
            }
            
            # Send request using thread executor for async compatibility
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                self.thread_executor,
                lambda: requests.post(url, headers=headers, json=data)
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                # Extract embedding vectors
                embeddings = [item["embedding"] for item in result["data"]]
                return embeddings
            else:
                self.logger.error(f"Error generating embeddings: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            return []
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using Azure OpenAI.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict containing sentiment analysis
        """
        if not self.endpoint or not self.api_key:
            self.logger.error("Azure OpenAI credentials not available")
            return {"error": "Azure OpenAI client not properly configured"}
        
        try:
            # Create system message for sentiment analysis
            system_message = "You are an AI assistant that analyzes the sentiment of text. Classify the sentiment as POSITIVE, NEGATIVE, or NEUTRAL. Also provide a confidence score from 0.0 to 1.0 and a brief explanation of your analysis. Format your response as a JSON object with 'sentiment', 'confidence', and 'explanation' fields."
            
            # Create messages
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ]
            
            # Generate completion
            response = await self.generate_chat_completion(messages, 
                                                         max_tokens=500, 
                                                         temperature=0.3)
            
            # Parse JSON from response
            if "error" in response:
                return response
            
            content = response.get("content", "")
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the content
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    sentiment_data = json.loads(json_str)
                    return sentiment_data
                else:
                    # If no JSON found, return a structured version of the response
                    return {
                        "sentiment": "UNKNOWN",
                        "confidence": 0.0,
                        "explanation": content,
                        "error": "Could not parse JSON from response"
                    }
                    
            except json.JSONDecodeError:
                return {
                    "sentiment": "UNKNOWN",
                    "confidence": 0.0,
                    "explanation": content,
                    "error": "Could not parse JSON from response"
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"error": f"Error analyzing sentiment: {str(e)}"}
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract named entities from text using Azure OpenAI.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dict containing extracted entities
        """
        if not self.endpoint or not self.api_key:
            self.logger.error("Azure OpenAI credentials not available")
            return {"error": "Azure OpenAI client not properly configured"}
        
        try:
            # Create system message for entity extraction
            system_message = """
            You are an AI assistant that extracts named entities from text. 
            Extract entities such as:
            - PERSON: Names of people
            - ORGANIZATION: Names of companies, agencies, institutions
            - LOCATION: Names of cities, countries, geographic features
            - DATE: Dates and times
            - MONEY: Monetary values
            - PERCENT: Percentage values
            
            Format your response as a JSON object with an 'entities' array, where each entity has 'text', 'type', and 'start_index' fields.
            """
            
            # Create messages
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ]
            
            # Generate completion
            response = await self.generate_chat_completion(messages, 
                                                         max_tokens=1000, 
                                                         temperature=0.3)
            
            # Parse JSON from response
            if "error" in response:
                return response
            
            content = response.get("content", "")
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the content
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    entities_data = json.loads(json_str)
                    return entities_data
                else:
                    # If no JSON found, return a structured version of the response
                    return {
                        "entities": [],
                        "raw_response": content,
                        "error": "Could not parse JSON from response"
                    }
                    
            except json.JSONDecodeError:
                return {
                    "entities": [],
                    "raw_response": content,
                    "error": "Could not parse JSON from response"
                }
                
        except Exception as e:
            self.logger.error(f"Error extracting entities: {str(e)}")
            return {"error": f"Error extracting entities: {str(e)}"}
    
    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Generate a summary of text using Azure OpenAI.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in tokens
            
        Returns:
            Summarized text
        """
        if not self.endpoint or not self.api_key:
            self.logger.error("Azure OpenAI credentials not available")
            return "Azure OpenAI client not properly configured"
        
        try:
            # Create system message for summarization
            system_message = f"You are an AI assistant that summarizes text. Create a concise summary of the following text in {max_length} tokens or less, preserving the most important information."
            
            # Create messages
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ]
            
            # Generate completion
            response = await self.generate_chat_completion(messages, 
                                                         max_tokens=max_length, 
                                                         temperature=0.5)
            
            # Return summary
            if "error" in response:
                return f"Error: {response['error']}"
            
            return response.get("content", "")
                
        except Exception as e:
            self.logger.error(f"Error summarizing text: {str(e)}")
            return f"Error summarizing text: {str(e)}"