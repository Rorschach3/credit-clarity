"""
Credit Clarity Chatbot Service
Uses Google Vertex AI Gemini models for credit-focused conversations
Integrates with existing user data and credit analysis capabilities
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import google.generativeai as genai
from google.oauth2 import service_account
from supabase import Client

# Set up logging
logger = logging.getLogger(__name__)

class CreditChatbotService:
    """
    Credit-focused chatbot service using Google Vertex AI
    Provides personalized credit advice based on user's data
    """
    
    def __init__(self, supabase_client: Client, gemini_api_key: str):
        """Initialize the chatbot service with required dependencies"""
        self.supabase = supabase_client
        
        # Initialize Gemini model
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("✅ Gemini model initialized for chatbot")
        else:
            logger.error("❌ Gemini API key missing for chatbot")
            self.model = None
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Fetch user's credit context for personalized responses"""
        try:
            context = {
                "profile": None,
                "tradelines": [],
                "disputes": [],
                "recent_activity": []
            }
            
            # Get user profile
            profile_result = self.supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if profile_result.data:
                context["profile"] = profile_result.data[0]
            
            # Get tradelines summary
            tradelines_result = self.supabase.table('tradelines').select('*').eq('user_id', user_id).limit(10).execute()
            if tradelines_result.data:
                context["tradelines"] = tradelines_result.data
            
            # Get recent dispute packets
            disputes_result = self.supabase.table('dispute_packets').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(5).execute()
            if disputes_result.data:
                context["disputes"] = disputes_result.data
            
            logger.info(f"📊 Retrieved context for user {user_id}: {len(context['tradelines'])} tradelines, {len(context['disputes'])} disputes")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error fetching user context: {e}")
            return {"profile": None, "tradelines": [], "disputes": [], "recent_activity": []}
    
    def build_system_prompt(self, user_context: Dict[str, Any]) -> str:
        """Build a context-aware system prompt for the chatbot"""
        base_prompt = """You are Credit Clarity AI, a specialized assistant for credit repair and financial education. 

CORE CAPABILITIES:
- Credit report analysis and explanation
- Dispute letter strategy and guidance
- Credit score improvement recommendations
- Financial education and best practices
- Tradeline interpretation and advice

PERSONALITY:
- Professional but approachable
- Educational and empowering
- Honest about limitations
- Focused on actionable advice

IMPORTANT GUIDELINES:
- Always provide accurate, helpful information about credit
- Encourage users to review their actual credit reports
- Suggest appropriate dispute strategies based on their data
- Never guarantee specific credit score outcomes
- Refer to professional services when appropriate
- Keep responses concise but comprehensive"""

        # Add user-specific context if available
        if user_context.get("profile"):
            profile = user_context["profile"]
            base_prompt += f"\n\nUSER CONTEXT:\n- User Name: {profile.get('firstName', '')} {profile.get('lastName', '')}"
            if profile.get('state'):
                base_prompt += f"\n- Location: {profile.get('state')}"
        
        if user_context.get("tradelines"):
            tradelines = user_context["tradelines"]
            negative_count = len([t for t in tradelines if t.get('is_negative')])
            base_prompt += f"\n- Credit Profile: {len(tradelines)} accounts, {negative_count} with negative marks"
            
            # Add account types summary
            account_types = {}
            for tradeline in tradelines:
                acc_type = tradeline.get('account_type', 'Unknown')
                account_types[acc_type] = account_types.get(acc_type, 0) + 1
            
            if account_types:
                types_str = ", ".join([f"{count} {acc_type}" for acc_type, count in account_types.items()])
                base_prompt += f"\n- Account Types: {types_str}"
        
        if user_context.get("disputes"):
            disputes = user_context["disputes"]
            base_prompt += f"\n- Dispute History: {len(disputes)} dispute packets created"
        
        base_prompt += "\n\nUse this context to provide personalized, relevant advice."
        
        return base_prompt
    
    async def generate_response(self, user_id: str, message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a contextual response using Gemini"""
        try:
            if not self.model:
                return {
                    "success": False,
                    "error": "Chatbot service not available",
                    "response": "I'm sorry, the chat service is currently unavailable. Please try again later."
                }
            
            # Get user context
            user_context = await self.get_user_context(user_id)
            
            # Build system prompt with context
            system_prompt = self.build_system_prompt(user_context)
            
            # Build conversation for context
            conversation_text = system_prompt + "\n\n"
            
            # Add conversation history if provided
            if conversation_history:
                conversation_text += "CONVERSATION HISTORY:\n"
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    conversation_text += f"{role.upper()}: {content}\n"
            
            # Add current message
            conversation_text += f"\nUSER: {message}\n\nASSISTANT:"
            
            logger.info(f"🧠 Generating response for user {user_id}")
            
            # Generate response with Gemini
            response = self.model.generate_content(conversation_text)
            
            if response and response.text:
                # Save conversation to database
                await self.save_conversation(user_id, message, response.text)
                
                logger.info(f"✅ Generated response for user {user_id}: {len(response.text)} characters")
                
                return {
                    "success": True,
                    "response": response.text.strip(),
                    "user_context": {
                        "has_tradelines": len(user_context.get("tradelines", [])) > 0,
                        "has_disputes": len(user_context.get("disputes", [])) > 0,
                        "profile_complete": user_context.get("profile") is not None
                    }
                }
            else:
                logger.error("❌ Empty response from Gemini")
                return {
                    "success": False,
                    "error": "No response generated",
                    "response": "I'm having trouble processing your request. Could you please try rephrasing your question?"
                }
                
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
            }
    
    async def save_conversation(self, user_id: str, user_message: str, ai_response: str):
        """Save conversation to database for history and learning"""
        try:
            conversation_data = {
                "user_id": user_id,
                "user_message": user_message,
                "ai_response": ai_response,
                "created_at": datetime.utcnow().isoformat(),
                "session_id": f"{user_id}_{datetime.now().strftime('%Y%m%d')}"  # Daily session grouping
            }
            
            result = self.supabase.table('chat_conversations').insert(conversation_data).execute()
            
            if result.data:
                logger.info(f"💾 Saved conversation for user {user_id}")
            else:
                logger.warning(f"⚠️ Failed to save conversation for user {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error saving conversation: {e}")
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for context"""
        try:
            result = self.supabase.table('chat_conversations')\
                .select('user_message, ai_response, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                # Format for conversation context
                history = []
                for row in reversed(result.data):  # Reverse to get chronological order
                    history.append({"role": "user", "content": row["user_message"]})
                    history.append({"role": "assistant", "content": row["ai_response"]})
                
                logger.info(f"📜 Retrieved {len(history)} conversation messages for user {user_id}")
                return history
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error retrieving conversation history: {e}")
            return []
    
    async def suggest_credit_actions(self, user_id: str) -> Dict[str, Any]:
        """Generate proactive credit improvement suggestions"""
        try:
            user_context = await self.get_user_context(user_id)
            
            suggestions = []
            
            # Analyze tradelines for suggestions
            tradelines = user_context.get("tradelines", [])
            negative_tradelines = [t for t in tradelines if t.get('is_negative')]
            
            if negative_tradelines:
                suggestions.append({
                    "type": "dispute",
                    "priority": "high",
                    "title": "Dispute Negative Items",
                    "description": f"You have {len(negative_tradelines)} accounts with negative marks that could be disputed.",
                    "action": "Review and dispute inaccurate negative items"
                })
            
            # Check for missing account types
            account_types = set([t.get('account_type') for t in tradelines if t.get('account_type')])
            if 'Credit Card' not in account_types and len(tradelines) < 3:
                suggestions.append({
                    "type": "credit_building",
                    "priority": "medium", 
                    "title": "Build Credit Mix",
                    "description": "Consider adding a credit card to improve your credit mix.",
                    "action": "Apply for a secured or starter credit card"
                })
            
            # Check dispute history
            disputes = user_context.get("disputes", [])
            if not disputes and negative_tradelines:
                suggestions.append({
                    "type": "dispute",
                    "priority": "high",
                    "title": "Start Dispute Process",
                    "description": "You haven't created any dispute letters yet.",
                    "action": "Use Credit Clarity to generate dispute letters"
                })
            
            return {
                "success": True,
                "suggestions": suggestions,
                "user_summary": {
                    "total_accounts": len(tradelines),
                    "negative_accounts": len(negative_tradelines),
                    "disputes_created": len(disputes)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating suggestions: {e}")
            return {"success": False, "error": str(e), "suggestions": []}