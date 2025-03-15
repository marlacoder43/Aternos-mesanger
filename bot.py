import asyncio
from telethon import TelegramClient, events
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import database
import config

# Telethon bot
bot = TelegramClient('bot', config.API_ID, config.API_HASH).start(bot_token=config.BOT_TOKEN)

# Selenium sozlamalari
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Ko‘rinmas rejim
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Foydalanuvchidan login va parol so‘rash"""
    user_id = event.sender_id
    if database.get_user(user_id):
        await event.respond("✅ Siz allaqachon tizimga kirgansiz! `/servers` buyrug‘ini bering.")
    else:
        await event.respond("🔐 Aternos loginni yuboring:")
        bot.add_event_handler(get_login, events.NewMessage(from_users=user_id))

async def get_login(event):
    """Foydalanuvchining loginini olish"""
    user_id = event.sender_id
    username = event.text
    await event.respond("🔑 Endi parolingizni yuboring:")
    bot.add_event_handler(lambda e: get_password(e, user_id, username), events.NewMessage(from_users=user_id))

async def get_password(event, user_id, username):
    """Foydalanuvchining parolini olish va bazaga saqlash"""
    password = event.text
    database.save_user(user_id, username, password)
    await event.respond("✅ Ma'lumotlar saqlandi! `/servers` buyrug‘ini bering.")

@bot.on(events.NewMessage(pattern="/servers"))
async def get_servers(event):
    """Aternos sahifasidan foydalanuvchi serverlarini olish"""
    user_id = event.sender_id
    user_data = database.get_user(user_id)
    if not user_data:
        await event.respond("⚠ Siz hali login kiritmagansiz. Iltimos, `/start` bosing.")
        return

    username, password = user_data
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Aternos login qilish
        driver.get("https://aternos.org/go/")
        driver.find_element(By.NAME, "user").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password, Keys.RETURN)
        await asyncio.sleep(5)

        # Serverlarni skaner qilish
        driver.get("https://aternos.org/servers/")
        await asyncio.sleep(3)

        servers = driver.find_elements(By.CLASS_NAME, "server-name")
        server_list = [s.text for s in servers]

        if server_list:
            response = "🌐 Sizning serverlaringiz:\n" + "\n".join([f"🔹 {s}" for s in server_list])
        else:
            response = "⚠ Sizda hech qanday server topilmadi."

        await event.respond(response)
    except Exception as e:
        await event.respond(f"❌ Xatolik: {e}")
    finally:
        driver.quit()

print("✅ Bot ishga tushdi!")
bot.run_until_disconnected()