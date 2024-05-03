import telebot
import pangea.exceptions as pe
from pangea.config import PangeaConfig
from pangea.services import Redact
import fireworks.client
import os

TELE_TOKEN = os.environ.get("teletoken")
token = os.environ.get("pangeatoken")
domain = os.environ.get("pangeadomain")

config = PangeaConfig(domain=domain)

bot = telebot.TeleBot(TELE_TOKEN)
bot.set_webhook()


@bot.message_handler(commands=['generate_text'])
def generate_text(message):
    bot.send_message(message.chat.id, "Please enter prompt")
    bot.register_next_step_handler(message, get_prompt)


def get_prompt(message):
    try:
        prompt = message.text
        redacted_msg = go_redact(prompt)
        print(f"warning message: {redacted_msg}")

        if redacted_msg != message.text:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "PII Information Found")
            bot.send_message(message.chat.id, redacted_msg)
            prompt = redacted_msg
        bot.send_message(message.chat.id, "Waiting for LLM to fetch the result")
        completion = fireworks.client.ChatCompletion.create(
              "accounts/fireworks/models/llama-v2-7b-chat",
              messages=[{"role": "user", "content": prompt}],
              temperature=0.7,
              n=2,
              max_tokens=400)
        bot.send_message(message.chat.id, completion.choices[0].message.content)

    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred. Please try again.")

def get_prompt_completion(message):
    print("testing prompt")
    try:
        print(f"message: {message}")
        completion = fireworks.client.ChatCompletion.create(
              "accounts/fireworks/models/llama-v2-7b-chat",
              messages=[{"role": "user", "content": message.text}],
              temperature=0.7,
              n=2,
              max_tokens=400)
        bot.send_message(message.chat.id, completion.choices[0].message.content)
    
    except Exception as e:
        print("Error occured:",str(e))


def go_redact(text):
    redact = Redact(token, config=config)
    try:
        redact_response = redact.redact(text=text, rulesets=["PII"])
        print(f"Redacted text: {redact_response.result.redacted_text}")

        return redact_response.result.redacted_text

    except pe.PangeaAPIException as e:
        print(f"Embargo Request Error: {e.response.summary}")
        for err in e.errors:
            print(f"\t{err.detail} \n")
        return False


@bot.message_handler(commands=['generate_image'])
def generate_image(message):
    bot.send_message(message.chat.id, "Please enter your prompt")
    bot.register_next_step_handler(message, generate_image_completion)

def generate_image_completion(message):
    try:
        prompt = message.text
        redacted_msg = go_redact(prompt)
     
        if redacted_msg != message.text:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "PII Information Found")
            bot.send_message(message.chat.id, redacted_msg)
            prompt = redacted_msg

        bot.send_message(message.chat.id, "Waiting for LLM to fetch the result")

        url = "https://api.fireworks.ai/inference/v1/image_generation/accounts/fireworks/models/stable-diffusion-xl-1024-v1-0"
        headers = {
            "Content-Type": "application/json",
            "Accept": "image/jpeg",
            "Authorization": f"Bearer {fireworks.client.apikey} "  
        }

        
        data = {
            "height": 1024,
            "width": 1024,
            "steps": 30,
            "seed": 1,
            "safety_check": False,
            "prompt": prompt
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            bot.send_photo(message.chat.id, response.content)
        else:
            print("Error:", response.text)
    except Exception as e:
        bot.send_message(message.chat.id, "An error occurred. Please try again.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    suggestion = "To generate text/image, you can use the /generate_text or /generate_image command followed by your prompt"

    bot.send_message(message.chat.id, suggestion)


bot.infinity_polling(timeout=10, long_polling_timeout = 5)

