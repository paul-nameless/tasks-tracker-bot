import config
import redis
import telebot

bot = telebot.TeleBot(config.API_TOKEN)
db = redis.Redis.from_url(config.REDIS_URI)
