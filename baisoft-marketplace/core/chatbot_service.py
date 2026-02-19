import os
import json
from decimal import Decimal
from core.models import Product


class ChatbotService:
    """Service to handle chatbot AI interactions and product queries."""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('GROK_API_KEY')
        self.api_type = 'openai' if os.environ.get('OPENAI_API_KEY') else 'grok'
    
    def get_approved_products(self):
        """Fetch all approved products from database."""
        products = Product.objects.filter(status='approved', is_deleted=False).select_related('business')
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'business': p.business.name if p.business else 'Unknown'
        } for p in products]
    
    def filter_products_by_price(self, max_price):
        """Get products under a specific price."""
        products = Product.objects.filter(
            status='approved', 
            is_deleted=False,
            price__lte=Decimal(str(max_price))
        ).select_related('business')
        
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'business': p.business.name if p.business else 'Unknown'
        } for p in products]
    
    def search_product_by_name(self, name):
        """Search for products by name."""
        products = Product.objects.filter(
            status='approved',
            is_deleted=False,
            name__icontains=name
        ).select_related('business')
        
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'business': p.business.name if p.business else 'Unknown'
        } for p in products]
    
    def build_context(self, user_message):
        """Build context with product data for AI."""
        context = {
            'user_question': user_message,
            'available_products': []
        }
        
        # Check if user is asking about price
        if 'under' in user_message.lower() or '$' in user_message or 'price' in user_message.lower():
            # Try to extract price from message
            import re
            price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', user_message)
            if price_match:
                max_price = float(price_match.group(1))
                context['available_products'] = self.filter_products_by_price(max_price)
                context['filter_applied'] = f'under ${max_price}'
            else:
                context['available_products'] = self.get_approved_products()
        
        # Check if user is asking about specific product
        elif 'about' in user_message.lower() or 'tell me' in user_message.lower():
            # Extract potential product name
            words = user_message.lower().replace('about', '').replace('tell me', '').strip().split()
            if words:
                search_term = ' '.join(words[-3:])  # Take last few words as product name
                context['available_products'] = self.search_product_by_name(search_term)
                context['search_term'] = search_term
        
        # Default: show all products
        else:
            context['available_products'] = self.get_approved_products()
        
        return context
    
    def generate_response(self, user_message):
        """Generate AI response based on user message and product data."""
        context = self.build_context(user_message)
        
        # If no API key, use fallback response
        if not self.api_key:
            return self._generate_fallback_response(context)
        
        # Call AI API
        try:
            if self.api_type == 'openai':
                return self._call_openai(context)
            else:
                return self._call_grok(context)
        except Exception as e:
            print(f"AI API error: {e}")
            return self._generate_fallback_response(context)
    
    def _generate_fallback_response(self, context):
        """Generate response without AI API."""
        products = context['available_products']
        user_question = context['user_question']
        
        if not products:
            return "I couldn't find any products matching your criteria. Please try a different search."
        
        # Build response based on context
        if 'filter_applied' in context:
            response = f"I found {len(products)} product(s) {context['filter_applied']}:\n\n"
        elif 'search_term' in context:
            response = f"Here's what I found about '{context['search_term']}':\n\n"
        else:
            response = f"We currently have {len(products)} approved product(s) available:\n\n"
        
        # List products
        for product in products[:5]:  # Limit to 5 products
            response += f"• {product['name']} - ${product['price']:.2f}\n"
            response += f"  {product['description'][:100]}{'...' if len(product['description']) > 100 else ''}\n"
            response += f"  Business: {product['business']}\n\n"
        
        if len(products) > 5:
            response += f"...and {len(products) - 5} more products."
        
        return response
    
    def _call_openai(self, context):
        """Call OpenAI API."""
        import requests
        
        products_text = json.dumps(context['available_products'], indent=2)
        
        prompt = f"""You are a helpful shopping assistant for a marketplace. 
        
User question: {context['user_question']}

Available products:
{products_text}

Please provide a helpful, friendly response about the products. Be concise and highlight key details like price and description."""
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful shopping assistant.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")
    
    def _call_grok(self, context):
        """Call Grok API."""
        import requests
        
        products_text = json.dumps(context['available_products'], indent=2)
        
        prompt = f"""You are a helpful shopping assistant for a marketplace.

User question: {context['user_question']}

Available products:
{products_text}

Please provide a helpful, friendly response about the products. Be concise and highlight key details like price and description."""
        
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'grok-beta',
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful shopping assistant.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"Grok API error: {response.status_code}")
