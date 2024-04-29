import telebot
import pangea.exceptions as pe
from pangea.config import PangeaConfig
from pangea.services import Redact
import fireworks.client
import os

TELE_TOKEN = os.environ.get("tele-token")

bot = telebot.TeleBot(TELE_TOKEN)
bot.set_webhook()

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    suggestion = "To generate text/image, you can use the /generate_text or /generate_image command followed by your prompt"

    bot.send_message(message.chat.id, suggestion)


bot.infinity_polling(timeout=10, long_polling_timeout = 5)

