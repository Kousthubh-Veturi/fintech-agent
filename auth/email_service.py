"""
Email service for password reset and verification
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@fintechagent.com')
        self.sg = SendGridAPIClient(api_key=self.api_key) if self.api_key else None
        
    def send_password_reset(self, to_email: str, reset_token: str, frontend_url: str = "http://localhost:3000") -> bool:
        """Send password reset email"""
        if not self.sg:
            logger.warning("SendGrid not configured, password reset email not sent")
            return False
            
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Password Reset</h1>
            </div>
            <div style="padding: 30px; background: #f8fafc;">
                <h2 style="color: #1e293b;">Reset Your Password</h2>
                <p style="color: #64748b; line-height: 1.6;">
                    You requested to reset your password. Click the button below to create a new password.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #3b82f6; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #64748b; font-size: 14px;">
                    This link will expire in 1 hour. If you didn't request this reset, please ignore this email.
                </p>
                <p style="color: #64748b; font-size: 12px; margin-top: 30px;">
                    If the button doesn't work, copy this link: {reset_url}
                </p>
            </div>
        </div>
        """
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="Reset Your Password - Fintech Agent",
            html_content=html_content
        )
        
        try:
            response = self.sg.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False
    
    def send_verification_email(self, to_email: str, verification_token: str, frontend_url: str = "http://localhost:3000") -> bool:
        """Send email verification"""
        if not self.sg:
            logger.warning("SendGrid not configured, verification email not sent")
            return False
            
        verify_url = f"{frontend_url}/verify-email?token={verification_token}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Welcome!</h1>
            </div>
            <div style="padding: 30px; background: #f8fafc;">
                <h2 style="color: #1e293b;">Verify Your Email</h2>
                <p style="color: #64748b; line-height: 1.6;">
                    Welcome to Fintech Agent! Please verify your email address to complete your registration.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background: #10b981; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Verify Email
                    </a>
                </div>
                <p style="color: #64748b; font-size: 14px;">
                    This link will expire in 24 hours.
                </p>
                <p style="color: #64748b; font-size: 12px; margin-top: 30px;">
                    If the button doesn't work, copy this link: {verify_url}
                </p>
            </div>
        </div>
        """
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="Verify Your Email - Fintech Agent",
            html_content=html_content
        )
        
        try:
            response = self.sg.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False

    def send_2fa_backup_codes(self, to_email: str, backup_codes: list) -> bool:
        """Send 2FA backup codes"""
        if not self.sg:
            logger.warning("SendGrid not configured, backup codes email not sent")
            return False
            
        codes_html = "<br>".join([f"<code style='background: #f1f5f9; padding: 4px 8px; border-radius: 4px;'>{code}</code>" for code in backup_codes])
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">2FA Backup Codes</h1>
            </div>
            <div style="padding: 30px; background: #f8fafc;">
                <h2 style="color: #1e293b;">Your Backup Codes</h2>
                <p style="color: #64748b; line-height: 1.6;">
                    Here are your 2FA backup codes. Save them in a secure place - you can use each code only once.
                </p>
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    {codes_html}
                </div>
                <p style="color: #dc2626; font-size: 14px; font-weight: bold;">
                    Keep these codes secure and don't share them with anyone!
                </p>
            </div>
        </div>
        """
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="Your 2FA Backup Codes - Fintech Agent",
            html_content=html_content
        )
        
        try:
            response = self.sg.send(message)
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send backup codes email: {e}")
            return False

# Global email service instance
email_service = EmailService()
