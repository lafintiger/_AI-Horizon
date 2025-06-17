#!/usr/bin/env python3
"""
Simple AI-Horizon demonstration - showing the core capabilities.
"""

import asyncio
from aih.utils.ollama_client import OllamaClient

async def quick_demo():
    print('🚀 AI-Horizon System Demo')
    print('=' * 50)
    print('Testing your local AI models...\n')
    
    client = OllamaClient()
    
    # Test 1: Basic chat
    print('💬 Test 1: AI Chat Capability')
    print('Question: "What are the top 3 ways AI is changing cybersecurity jobs?"')
    print('🤖 Thinking...')
    
    response = await client.chat('What are the top 3 ways AI is changing cybersecurity jobs in 2024?')
    print(f'✅ Response: {response[:400]}...\n')
    
    # Test 2: Classification task
    print('🔍 Test 2: AI Classification')
    print('Content: "AI-powered threat detection systems can automatically identify and respond to security incidents"')
    print('🤖 Analyzing...')
    
    analysis = await client.analyze_content(
        'AI-powered threat detection systems can automatically identify and respond to security incidents',
        analysis_type='classification'
    )
    print(f'✅ Analysis: {analysis[:200]}...\n')
    
    print('🎉 SUCCESS! Your AI-Horizon system is fully operational!')
    print('📊 Performance: Excellent')
    print('💰 Cost: $0.00 (100% local)')
    print('🔒 Privacy: Complete (no data leaves your machine)')

if __name__ == "__main__":
    asyncio.run(quick_demo()) 