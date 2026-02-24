import google.generativeai as genai
import os

class FocusFlowEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def get_ai_breakdown(self, topics):
        """Uses Gemini to organize topics by logical difficulty/order."""
        if not self.api_key:
            return "API Key not provided. Using default order."

        prompt = f"""
        Act as a study coach. I have these topics to study: {topics}.
        1. Organize them in the most logical learning order.
        2. Briefly explain why this order works.
        3. Identify which topic might be the 'Deep Work' focus.
        Keep the response concise and formatted for a desktop app.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error connecting to Gemini: {str(e)}"
