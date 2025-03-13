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
    buttons = [[Button.inline("🔑 Login", b"login")]]
    await bot.send_message(chat, message, buttons=buttons)

# Login process
@bot.on(events.CallbackQuery(data=b"login"))
async def login_step1(event):
    chat = event.chat_id
    await bot.send_message(chat, "📝 Please enter your Aternos username:")
    user_data[chat] = {"step": "awaiting_username"}

@bot.on(events.NewMessage)
async def handle_login(event):
    chat = event.chat_id
    if chat in user_data:
        if user_data[chat]["step"] == "awaiting_username":
            user_data[chat]["username"] = event.text
            user_data[chat]["step"] = "awaiting_password"
            await bot.send_message(chat, "🔑 Now enter your password:")
        elif user_data[chat]["step"] == "awaiting_password":
            user_data[chat]["password"] = event.text
            await bot.send_message(chat, "⏳ Logging in...")

            # Login to Aternos
            login_success = await aternos_login(chat, user_data[chat]["username"], user_data[chat]["password"])

            if login_success:
                await show_main_menu(chat)
            else:
                await bot.send_message(chat, "❌ Login failed! Incorrect username or password.")

            del user_data[chat]

# Aternos Login function
async def aternos_login(chat, username, password):
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://aternos.org/go/")
        time.sleep(3)

        driver.find_element(By.NAME, "user").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

        time.sleep(5)

        if "dashboard" in driver.current_url:
            user_data[chat]["driver"] = driver  # Store session
            return True
        else:
            driver.quit()
            return False
    except Exception as e:
        print("Error:", e)
        return False

# Show main menu after login
async def show_main_menu(chat):
    driver = user_data[chat]["driver"]
    driver.get("https://aternos.org/servers/")

    time.sleep(3)
    
    servers = driver.find_elements(By.CLASS_NAME, "server-name")  # Find servers
    buttons = []

    if servers:
        for server in servers:
            server_name = server.text.strip()
            buttons.append([Button.inline(f"🌍 {server_name}", f"server_{server_name}".encode())])
    else:
        await bot.send_message(chat, "⚠️ You don't have any servers.")

    buttons.append([Button.inline("➕ Create Server", b"create_server")])  # Create server button
    await bot.send_message(chat, "🛠 Your Servers:", buttons=buttons)

# Handle server creation
@bot.on(events.CallbackQuery(data=b"create_server"))
async def choose_server_type(event):
    chat = event.chat_id
    await bot.send_message(chat, "🛠 Choose server type:", buttons=[
        [Button.inline("🟢 Java", b"server_java"), Button.inline("🔵 Bedrock", b"server_bedrock")]
    ])

@bot.on(events.CallbackQuery(pattern=b"server_"))
async def ask_server_name(event):
    chat = event.chat_id
    server_type = event.data.decode().split("_")[1]
    user_data[chat] = {"step": "awaiting_server_name", "server_type": server_type}
    await bot.send_message(chat, "📌 Enter a name for your server:")

@bot.on(events.NewMessage)
async def create_server(event):
    chat = event.chat_id
    if chat in user_data and user_data[chat]["step"] == "awaiting_server_name":
        server_name = event.text
        server_type = user_data[chat]["server_type"]

        await bot.send_message(chat, f"⏳ Creating {server_type} server named '{server_name}'...")
        success = await aternos_create_server(chat, server_name, server_type)

        if success:
            await bot.send_message(chat, f"✅ Server '{server_name}' created successfully!")
        else:
            await bot.send_message(chat, "❌ Failed to create server!")

        del user_data[chat]

# Aternos Server Creation function
async def aternos_create_server(chat, server_name, server_type):
    try:
        driver = user_data[chat]["driver"]
        driver.get("https://aternos.org/servers/")
        time.sleep(3)

        driver.find_element(By.CLASS_NAME, "addserver").click()  # Click add server
        time.sleep(2)

        # Select server type
        if server_type == "java":
            driver.find_element(By.CLASS_NAME, "java").click()
        else:
            driver.find_element(By.CLASS_NAME, "bedrock").click()
        
        time.sleep(2)

        # Enter server name
        name_box = driver.find_element(By.CLASS_NAME, "server-name-input")
        name_box.clear()
        name_box.send_keys(server_name)

        # Confirm server creation
        driver.find_element(By.CLASS_NAME, "confirm").click()
        time.sleep(5)

        return True
    except Exception as e:
        print("Error:", e)
        return False

print("Bot is running...")
bot.run_until_disconnected()
