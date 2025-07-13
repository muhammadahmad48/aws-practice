import os
import json
import boto3
from typing import Dict, List, Union, Optional
from botocore.exceptions import ClientError
from pydantic import BaseModel, AnyHttpUrl
from pydantic_settings import  BaseSettings
from functools import cached_property

class Settings(BaseSettings):
    # AWS credentials for accessing Secrets Manager (from environment variables)
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create base settings instance for AWS credentials
base_settings = Settings()


class SecretSchema(BaseModel):
    POSTGRES_USER: str = None
    POSTGRES_PASSWORD: str = None
    POSTGRES_SERVER: str = None
    POSTGRES_PORT: str = None
    POSTGRES_DB: str = None

    SECRET_KEY: str = None
    PYTHON_ENVIRONMENT:str=None
    SMTP_HOST: str = None
    SMTP_PORT: str = None
    SMTP_USER: str = None
    SMTP_PASSWORD: str = None
    SENDER_EMAIL: str = None
    SMTP_FROM_NAME: str = None

    VERIFF_API_KEY: str = None
    VERIFF_API_SHARED_SECRET_KEY: str = None
    VERIFF_BASE_URL: str = None
    VERIFF_CALLBACK_URL: str = None

    GOOGLE_CLIENT_ID: str = None

    SENDGRID_API_KEY: str = None
    SEND_GRID_EMAIL: str = None
    SEND_GRID_NAME: str = None

    WELCOME_EN_EMAIL_TEMPLATE_ID: str = None
    WELCOME_FR_EMAIL_TEMPLATE_ID: str = None
    SUBMIT_SELL_YOUR_BUSINESS_EMAIL_TEMPLATE_ID: str = None
    CRITERIA_SAVED_AS_BUYER_EMAIL_TEMPLATE_ID: str = None
    MESSAGE_RECEIVED_FROM_CONTACT_EMAIL_TEMPLATE_ID: str = None
    BUSINESS_PUBLISHED_EMAIL_TEMPLATE_ID: str = None
    BUSINESS_EDITED_EMAIL_TEMPLATE_ID: str = None
    BUSINESS_ARCHIVED_EMAIL_TEMPLATE_ID: str = None
    REQUEST_MORE_DETAILS_SELLER_EMAIL_TEMPLATE_ID: str = None
    ACCESS_GRANTED_TO_BUYER_EMAIL_TEMPLATE_ID: str = None

    SKRIBBLE_API_KEY: str = None
    SKRIBBLE_USERNAME: str = None
    SKRIBBLE_URL: str = None

    BACKEND_URL: str = None
    FRONTEND_BASE_URL: str = None

    ADMIN_EMAIL: str = None
    
    FRONTEND_IS_HTTPS: bool = None
    BACKEND_IS_HTTPS: bool = None
    ALLOW_ORIGINS: str = None
    DOMAIN: str = None
    AWS_REGION:str = None
    S3_BUCKET_NAME:str = None
    S3_BUCKET_ARN:str = None



def get_secret_values(secret_name: str, region: str = "eu-central-2") -> SecretSchema:
    """
    Get all key-value pairs from a specific AWS secret
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        region: AWS region
    
    Returns:
        SecretSchema object with all key-value pairs from the secret
    """
    
    try:
        # Get the secret
        client = boto3.client('secretsmanager',aws_access_key_id=base_settings.AWS_ACCESS_KEY_ID,aws_secret_access_key=base_settings.AWS_SECRET_ACCESS_KEY, region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
        
        # Parse JSON secret
        try:
            secret_data = json.loads(secret_string)
            if isinstance(secret_data, dict):
                # Convert boolean strings to actual booleans for specific fields
                boolean_fields = ['FRONTEND_IS_HTTPS', 'BACKEND_IS_HTTPS']
                for field in boolean_fields:
                    if field in secret_data and isinstance(secret_data[field], str):
                        secret_data[field] = secret_data[field].lower() in ('true', '1', 'yes', 'on')
                
                # Return SecretSchema object
                return SecretSchema(**secret_data)
            else:
                # Single value secret
                return SecretSchema(**{secret_name: str(secret_data)})
        except json.JSONDecodeError:
            # Plain text secret
            return SecretSchema(**{secret_name: secret_string})
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ Error getting secret '{secret_name}': {error_code}")
        print("📁 Falling back to environment variables")
        return SecretSchema()
    except Exception as e:
        print(f"❌ Unexpected error getting secret '{secret_name}': {str(e)}")
        print("📁 Falling back to environment variables")
        return SecretSchema()


class SecretManager(BaseSettings):    
    
    @cached_property  # ← UNCOMMENTED - WILL SHOW LOGS!
    def SECRET_VALUES(self) -> SecretSchema:
        secrets=get_secret_values("lumaya-backend-env", "eu-central-2")        
        return secrets
    
    @property
    def FRONTEND_IS_HTTPS(self) -> bool:
      return str(self.SECRET_VALUES.FRONTEND_IS_HTTPS or "false").lower() == "true"
    
    @property
    def BACKEND_IS_HTTPS(self) -> bool:
       return str(self.SECRET_VALUES.BACKEND_IS_HTTPS or "false").lower() == "true"
        
    @property
    def ALLOW_ORIGINS(self) -> str:
        return self.SECRET_VALUES.ALLOW_ORIGINS or ""
    
    @property
    def DOMAIN(self) -> str:
        return self.SECRET_VALUES.DOMAIN or "" 

    @property
    def ENVIRONMENT(self) -> str:
        return self.SECRET_VALUES.PYTHON_ENVIRONMENT or "development" 


    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lumaya"
    PROJECT_DESCRIPTION: str = (
        "Lumaya Advanced Backend is a FastAPI project that uses SQLAlchemy for database interactions, "
        "JWT for secure authentication, and includes configurations for CORS, SMTP, and PostgreSQL. "
        "This backend is designed to be scalable, secure, and easy to integrate with frontend applications."
    )
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Database Configuration
    @property
    def POSTGRES_USER(self) -> str:
        return self.SECRET_VALUES.POSTGRES_USER or ""
    
    @property
    def POSTGRES_PASSWORD(self) -> str:
        return self.SECRET_VALUES.POSTGRES_PASSWORD or ""
    
    @property
    def POSTGRES_SERVER(self) -> str:
        return self.SECRET_VALUES.POSTGRES_SERVER or "localhost"
    
    @property
    def POSTGRES_PORT(self) -> str:
        return self.SECRET_VALUES.POSTGRES_PORT or "5432"
    
    @property
    def POSTGRES_DB(self) -> str:
        return self.SECRET_VALUES.POSTGRES_DB or ""
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT Configuration
    @property
    def SECRET_KEY(self) -> str:
        return self.SECRET_VALUES.SECRET_KEY or ""
    
    ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # SMTP Configuration
    @property
    def SMTP_HOST(self) -> str:
        return self.SECRET_VALUES.SMTP_HOST or ""
    
    @property
    def SMTP_PORT(self) -> int:
        port_str = self.SECRET_VALUES.SMTP_PORT or "587"
        return int(port_str)
    
    @property
    def SMTP_USER(self) -> str:
        return self.SECRET_VALUES.SMTP_USER or ""
    
    @property
    def SMTP_PASSWORD(self) -> str:
        return self.SECRET_VALUES.SMTP_PASSWORD or ""
    
    @property
    def SMTP_SENDER_EMAIL(self) -> str:
        return self.SECRET_VALUES.SENDER_EMAIL or ""
    
    @property
    def SMTP_FROM_NAME(self) -> str:
        return self.SECRET_VALUES.SMTP_FROM_NAME or ""

    @property
    def AWS_REGION(self) -> str:
        return self.SECRET_VALUES.AWS_REGION or ""

    @property
    def S3_BUCKET_NAME(self) -> str:
        return self.SECRET_VALUES.S3_BUCKET_NAME or "lumaya-bucket"
    
    @property
    def S3_BUCKET_ARN(self) -> str:
        return self.SECRET_VALUES.S3_BUCKET_ARN or "arn:aws:s3:::lumaya-bucket-dev"

    # Veriff API Secret Keys
    @property
    def VERIFF_API_KEY(self) -> str:
        return self.SECRET_VALUES.VERIFF_API_KEY or ""
    
    @property
    def VERIFF_API_SHARED_SECRET_KEY(self) -> str:
        return self.SECRET_VALUES.VERIFF_API_SHARED_SECRET_KEY or ""
    
    @property
    def VERIFF_BASE_URL(self) -> str:
        return self.SECRET_VALUES.VERIFF_BASE_URL or ""
    
    @property
    def VERIFF_CALLBACK_URL(self) -> str:
        return self.SECRET_VALUES.VERIFF_CALLBACK_URL or "https://lumaya-web.hashlogics.com/en"

    # Google client secrets
    @property
    def GOOGLE_CLIENT_ID(self) -> str:
        return self.SECRET_VALUES.GOOGLE_CLIENT_ID or "client id"

    # SendGrid Configuration
    @property
    def SEND_GRID_KEY(self) -> str:
        return self.SECRET_VALUES.SENDGRID_API_KEY or ""
    
    @property
    def SEND_GRID_EMAIL(self) -> str:
        return self.SECRET_VALUES.SEND_GRID_EMAIL or ""
    
    @property
    def SEND_GRID_NAME(self) -> str:
        return self.SECRET_VALUES.SEND_GRID_NAME or ""

    # Email Template IDs
    @property
    def WELCOME_EN_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.WELCOME_EN_EMAIL_TEMPLATE_ID or ""
    
    @property
    def WELCOME_FR_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.WELCOME_FR_EMAIL_TEMPLATE_ID or ""
    
    @property
    def SUBMIT_SELL_YOUR_BUSINESS_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.SUBMIT_SELL_YOUR_BUSINESS_EMAIL_TEMPLATE_ID or ""
    
    @property
    def CRITERIA_SAVED_AS_BUYER_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.CRITERIA_SAVED_AS_BUYER_EMAIL_TEMPLATE_ID or ""
    
    @property
    def MESSAGE_RECEIVED_FROM_CONTACT_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.MESSAGE_RECEIVED_FROM_CONTACT_EMAIL_TEMPLATE_ID or ""
    
    @property
    def BUSINESS_PUBLISHED_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.BUSINESS_PUBLISHED_EMAIL_TEMPLATE_ID or ""
    
    @property
    def BUSINESS_EDITED_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.BUSINESS_EDITED_EMAIL_TEMPLATE_ID or ""
    
    @property
    def BUSINESS_ARCHIVED_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.BUSINESS_ARCHIVED_EMAIL_TEMPLATE_ID or ""
    
    @property
    def REQUEST_MORE_DETAILS_SELLER_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.REQUEST_MORE_DETAILS_SELLER_EMAIL_TEMPLATE_ID or ""
    
    @property
    def ACCESS_GRANTED_TO_BUYER_EMAIL_TEMPLATE_ID(self) -> str:
        return self.SECRET_VALUES.ACCESS_GRANTED_TO_BUYER_EMAIL_TEMPLATE_ID or ""

    # Skribble secrets
    @property
    def SKRIBBLE_API_KEY(self) -> str:
        return self.SECRET_VALUES.SKRIBBLE_API_KEY or ""
    
    @property
    def SKRIBBLE_USERNAME(self) -> str:
        return self.SECRET_VALUES.SKRIBBLE_USERNAME or ""
    
    @property
    def SKRIBBLE_URL(self) -> str:
        return self.SECRET_VALUES.SKRIBBLE_URL or "https://api.skribble.com/v2"
    
    @property
    def BACKEND_URL(self) -> str:
        return self.SECRET_VALUES.BACKEND_URL or ""
    
    @property
    def ADMIN_EMAIL(self) -> str:
        return self.SECRET_VALUES.ADMIN_EMAIL or "isabelle@lumaya.ch"

    # Referral secrets
    @property
    def FRONTEND_BASE_URL(self) -> str:
        return self.SECRET_VALUES.FRONTEND_BASE_URL or ""
    
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields
 
        
settings = SecretManager()