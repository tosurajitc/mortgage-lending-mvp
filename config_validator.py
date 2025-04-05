import os
from dotenv import load_dotenv
import logging

class ConfigValidator:
    def __init__(self):
        load_dotenv()
        logging.basicConfig(level=logging.INFO)
        self.required_configs = [
            # Copilot Studio Configurations
            'COPILOT_STUDIO_TOKEN_ENDPOINT',
            'COPILOT_STUDIO_API_KEY', 
            'COPILOT_STUDIO_BOT_ID',
            
            # Azure Configurations
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_DOCUMENT_INTELLIGENCE_KEY',
            'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT',
            
            # Cosmos DB Configurations
            'COSMOS_URI',
            'COSMOS_KEY',
            
            # Security
            'SECRET_KEY'
        ]
    
    def validate_configurations(self):
        """
        Validate critical configurations
        """
        logging.info("🔍 Starting Configuration Validation")
        
        validation_results = {
            'missing_configs': [],
            'config_status': True
        }
        
        for config in self.required_configs:
            value = os.getenv(config)
            if not value or value.strip() == '':
                logging.warning(f"❌ Missing Configuration: {config}")
                validation_results['missing_configs'].append(config)
                validation_results['config_status'] = False
            else:
                logging.info(f"✅ {config}: Configured")
        
        # Additional checks
        if len(validation_results['missing_configs']) > 0:
            logging.error("Configuration Validation FAILED")
            logging.error(f"Missing Configurations: {validation_results['missing_configs']}")
        else:
            logging.info("🎉 All Critical Configurations Validated Successfully!")
        
        return validation_results

    def security_recommendations(self):
        """
        Provide security recommendations
        """
        recommendations = [
            "Use strong, unique API keys",
            "Ensure HTTPS is used in production",
            "Implement rate limiting",
            "Use environment-specific configurations",
            "Rotate API keys regularly"
        ]
        
        logging.info("\n🛡️ Security Recommendations:")
        for rec in recommendations:
            logging.info(f"- {rec}")

# Run configuration validation
if __name__ == "__main__":
    validator = ConfigValidator()
    results = validator.validate_configurations()
    validator.security_recommendations()
    
    # Exit with non-zero status if configuration is invalid
    exit(0 if results['config_status'] else 1)