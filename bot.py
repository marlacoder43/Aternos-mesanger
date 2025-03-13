from telethon import TelegramClient, events, Button
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import asyncio

# Bot settings
API_ID = 22225255  # Your API ID
API_HASH = "6cb04f39cc07170b75d1ce675eeb65b8"
BOT_TOKEN = "7393925268:AAEPvmlU3MN-y0PmJrQvRFI8gp-moeqfNSs"

bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# User session storage
user_data = {}

# Chrome Headless Mode settings
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# ChromeDriver path
service = Service("/usr/bin/chromedriver")

# /start command
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    chat = event.chat_id
    message = "👋 Welcome! Manage your Aternos Minecraft server.\n👇 Choose an option:"
    buttons = [
        [Button.inline("🔑 Login", b"login"), Button.inline("🆕 Register", b"register")]
    ]
    await bot.send_message(chat, message, buttons=buttons)

# Register button clicked
@bot.on(events.CallbackQuery(data=b"register"))
async def register_step1(event):
    chat = event.chat_id
    await bot.send_message(chat, "📝 Please enter a username for your Aternos account:")
    user_data[chat] = {"step": "awaiting_register_username"}

@bot.on(events.NewMessage)
async def handle_registration(event):
    chat = event.chat_id
    if chat in user_data:
        step = user_data[chat]["step"]
        
        if step == "awaiting_register_username":
            user_data[chat]["username"] = event.text
            user_data[chat]["step"] = "awaiting_register_password"
            await bot.send_message(chat, "🔑 Now enter a password for your account:")

        elif step == "awaiting_register_password":
            user_data[chat]["password"] = event.text
            user_data[chat]["step"] = "awaiting_register_confirm_password"
            await bot.send_message(chat, "🔐 Please confirm your password:")

        elif step == "awaiting_register_confirm_password":
            if event.text != user_data[chat]["password"]:
                await bot.send_message(chat, "❌ Passwords do not match! Please enter again:")
                return
            user_data[chat]["step"] = "awaiting_register_email"
            await bot.send_message(chat, "📧 Now enter your email address:")

        elif step == "awaiting_register_email":
            user_data[chat]["email"] = event.text
            await bot.send_message(chat, "⏳ Creating your account...")
            
            success = await aternos_register(chat, user_data[chat]["username"], user_data[chat]["password"], user_data[chat]["email"])

            if success:
                await bot.send_message(chat, "✅ Registration successful! You can now login.")
            else:
                await bot.send_message(chat, "❌ Registration failed! Username may already be taken or an error occurred.")

            del user_data[chat]  # Clear user session

# Aternos account registration automation
async def aternos_register(chat, username, password, email):
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://aternos.org/register/")
        time.sleep(3)

        # Enter username
        username_input = driver.find_element(By.NAME, "user")
        username_input.send_keys(username)
        time.sleep(1)

        # Accept terms & privacy policy
        driver.find_element(By.NAME, "tos").click()
        driver.find_element(By.NAME, "privacy").click()
        time.sleep(1)

        # Click "Next"
        driver.find_element(By.CLASS_NAME, "next").click()
        time.sleep(3)

        # If username is taken, ask again
        if "already taken" in driver.page_source:
            driver.quit()
            await bot.send_message(chat, "❌ Username is already taken. Please enter a new one:")
            user_data[chat]["step"] = "awaiting_register_username"
            return False

        # Enter password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(1)

        # Confirm password
        confirm_password_input = driver.find_element(By.NAME, "password_repeat")
        confirm_password_input.send_keys(password)
        time.sleep(1)

        # Click "Next"
        driver.find_element(By.CLASS_NAME, "next").click()
        time.sleep(3)

        # Enter email
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(email)
        time.sleep(1)

        # Click "Register"
        driver.find_element(By.CLASS_NAME, "register").click()
        time.sleep(5)

        # Check if registration was successful
        if "welcome" in driver.page_source:
            driver.quit()
            return True
        else:
            driver.quit()
            return False

    except Exception as e:
        print("Error:", e)
        return False

print("Bot is running...")
bot.run_until_disconnected()
