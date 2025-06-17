#!/usr/bin/env python3
"""
Interactive chat interface to test AI-Horizon's local models.
Perfect for testing the chat and RAG capabilities.
"""

import asyncio
from aih.utils.ollama_client import OllamaClient
from aih.utils.database import Database

async def interactive_chat():
    """Interactive chat session with AI-Horizon."""
    print("🚀 AI-Horizon Interactive Chat")
    print("=" * 50)
    print("This is your local AI cybersecurity workforce expert!")
    print("Type 'quit' to exit, 'rag' to enable RAG mode")
    print()
    
    client = OllamaClient()
    db = Database()
    
    # Get some context from your database
    artifacts = db.get_artifacts(limit=3)
    context = "\n\n".join([artifact[2][:1000] for artifact in artifacts])
    
    rag_mode = False
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'rag':
                rag_mode = not rag_mode
                print(f"🔍 RAG mode {'enabled' if rag_mode else 'disabled'}")
                continue
            
            if not user_input:
                continue
            
            print("🤖 Thinking...")
            
            if rag_mode:
                response = await client.chat_with_context(
                    query=user_input,
                    context=context
                )
                print(f"AI (with context): {response}")
            else:
                response = await client.chat(user_input)
                print(f"AI: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_chat()) 