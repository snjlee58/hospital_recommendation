"""
Main application entry point for hospital recommendation service
"""
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.web.routes import HospitalRecommendationApp


def main():
    """Main application entry point"""
    # Only show startup message if not in reloader
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        print("🏥 Hospital Recommendation AI Service Starting...")
    
    try:
        app = HospitalRecommendationApp()
        
        # Only show success message if not in reloader
        if not os.environ.get('WERKZEUG_RUN_MAIN'):
            print("✅ Application initialized successfully")
            print("🌐 Starting web server on http://localhost:5000")
        
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"❌ Error starting application: {str(e)}")
        raise


if __name__ == "__main__":
    main() 