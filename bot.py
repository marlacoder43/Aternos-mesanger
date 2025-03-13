from telethon import TelegramClient, events, Button
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import asyncio

# Bot sozlamalari
API_ID = 22225255  # O'z API_ID raqamingizni kiriting
API_HASH = "6cb04f39cc07170b75d1ce675eeb65b8"
BOT_TOKEN = "7393925268:AAEPvmlU3MN-y0PmJrQvRFI8gp-moeqfNSs"

bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Foydalanuvchi login ma'lumotlarini saqlash
user_data = {}

# Chrome headless rejimda ishlashi uchun sozlash
chrome_options = Options()
chrome_options.add_argument("--headless")  # Headless rejim
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# ChromeDriver yo‘lini belgilash
service = Service("/usr/bin/chromedriver")

# /start buyrug'i
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    chat = event.chat_id
    message = "👋 Salom! Aternos serveringizni boshqarish uchun tizimga kiring.\n👇 Quyidagilardan birini tanlang:"
    buttons = [[Button.inline("🔑 Login", b"login")]]
    await bot.send_message(chat, message, buttons=buttons)

# Login tugmasi bosilganda
@bot.on(events.CallbackQuery(data=b"login"))
async def login_step1(event):
    chat = event.chat_id
    await bot.send_message(chat, "📝 Iltimos, Aternos loginini kiriting:")
    user_data[chat] = {"step": "awaiting_username"}

# Username va parol qabul qilish
@bot.on(events.NewMessage)
async def handle_login(event):
    chat = event.chat_id
    if chat in user_data:
        if user_data[chat]["step"] == "awaiting_username":
            user_data[chat]["username"] = event.text
            user_data[chat]["step"] = "awaiting_password"
            await bot.send_message(chat, "🔑 Endi parolingizni kiriting:")
        elif user_data[chat]["step"] == "awaiting_password":
            user_data[chat]["password"] = event.text
            await bot.send_message(chat, "⏳ Login tekshirilmoqda...")

            # Aternos'ga login qilish
            login_success = await aternos_login(user_data[chat]["username"], user_data[chat]["password"])

            if login_success:
                await bot.send_message(chat, "✅ Login muvaffaqiyatli! Sizning serverlaringiz:")
                await bot.send_message(chat, "📜 [Server 1] Online\n📜 [Server 2] Offline")  # Serverlar ro‘yxatini chiqarish
            else:
                await bot.send_message(chat, "❌ Xatolik! Login yoki parol noto‘g‘ri.")

            del user_data[chat]

# Aternos'ga Selenium orqali login qilish
async def aternos_login(username, password):
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://aternos.org/go/")
        time.sleep(3)

        driver.find_element(By.NAME, "user").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        time.sleep(5)  # Yuklanishini kutamiz

        if "dashboard" in driver.current_url:
            driver.quit()
            return True
        else:
            driver.quit()
            return False
    except Exception as e:
        print("Xatolik:", e)
        return False

print("Bot ishlayapti...")
bot.run_until_disconnected()
