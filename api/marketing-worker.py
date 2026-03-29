import os
import json
import logging
from http.server import BaseHTTPRequestHandler

# Configure basic logging
logging.basicConfig(level=logging.INFO)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        auth_header = self.headers.get('Authorization')
        cron_secret = os.environ.get('CRON_SECRET')
        
        # Security: Require CRON_SECRET authorization
        if not cron_secret or auth_header != f"Bearer {cron_secret}":
            logging.warning("Unauthorized access attempt to marketing loop.")
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode('utf-8'))
            return

        try:
            # We import here to keep the Vercel cold start as low as possible for other routes if needed, 
            # though Vercel caches warm environments.
            import google.generativeai as genai
            from supabase import create_client, Client
            
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
                
            genai.configure(api_key=gemini_key)
            
            # Step 1: Draft the LinkedIn Post
            model = genai.GenerativeModel('gemini-pro')
            prompt = "Act as an expert HVAC Compliance Marketer. Draft an engaging LinkedIn post about the EPA 15lb threshold rule for 2026 and how PermitFlow Pro helps automate the mandatory refrigerant logs. Use industry-specific terminology."
            
            logging.info("Generating marketing content with Google Gemini...")
            response = model.generate_content(prompt)
            post_content = response.text
            
            # Step 2: Save the draft to Supabase
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
            
            if supabase_url and supabase_key:
                logging.info("Saving draft to Supabase marketing_queue table...")
                supabase: Client = create_client(supabase_url, supabase_key)
                
                # Insert the draft into the table
                supabase.table("marketing_queue").insert({
                    "draft_content": post_content,
                    "status": "pending_review"
                }).execute()
            else:
                logging.warning("Supabase credentials not found. Returning draft without saving.")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            res = {
                "success": True, 
                "message": "Marketing loop executed successfully.",
                "draft": post_content
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            
        except ImportError as ie:
            logging.error(f"Missing dependency: {ie}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Missing dependency: {ie}"}).encode('utf-8'))
        except Exception as e:
            logging.error(f"Error in marketing worker: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
