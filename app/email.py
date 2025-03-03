from mailjet_rest import Client
from .config import settings
from fastapi import HTTPException


mailjet = Client(auth=(settings.mailjet_api_key, settings.mailjet_api_secret), version='v3.1')

async def send_email(to_email: str, name: str):
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "madehinsamuel@gmail.com",  # Replace with your verified sender email
                    "Name": "Keepsy"  # Replace with your name or app name
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": name  
                    }
                ],
                "TemplateID": 6776296,
                "TemplateLanguage": True,  # Enable variable substitution
                "Variables": {
                    "firstname": name  # Dynamic variable for the template
                }
            }
        ]
    }
    result = mailjet.send.create(data=data)
    if result.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"message": "Email sent successfully"}