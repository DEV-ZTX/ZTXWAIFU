import importlib
import time
import random
import re
import asyncio
from html import escape 
import threading
import os
import http.server
import socketserver

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, CommandHandler, CallbackContext, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES


locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

# Function to run the HTTP server
"""def run_server():
    PORT = int(os.getenv('PORT', 4000))  # Default to port 4000 if PORT is not set
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()

# Start the HTTP server in a separate thread
threading.Thread(target=run_server).start()"""

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)


last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]
    async with lock:
        message_counts[chat_id] = message_counts.get(chat_id, 0) + 1
        if message_counts[chat_id] % 100 == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    all_characters = list(await collection.find({}).to_list(length=None))
    if chat_id not in sent_characters:
        sent_characters[chat_id] = {}
    character = random.choice([c for c in all_characters if c['id'] not in sent_characters[chat_id]])
    sent_characters[chat_id][character['id']] = time.time()
    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"""<b>{character['rarity'][0]}Oᴡᴏ! ᴀ {character['rarity'][2:]} ᴄᴏsᴘʟᴀʏ ʜᴀs ᴀᴘᴘᴇᴀʀᴇᴅ!</b>\n<b>ᴀᴅᴅ ʜᴇʀ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ ʙʏ sᴇɴᴅɪɴɢ</b>\n<b>/guess ɴᴀᴍᴇ</b>""",
        parse_mode='HTML')

async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in sent_characters or not sent_characters[chat_id]:
        await update.message.reply_text("❌ No character available to guess.")
        return

    character = sent_characters[chat_id]  # Retrieve the character

    # Ensure context.args is valid
    if not context.args:
        await update.message.reply_text("❌ Please provide a guess.")
        return

    guess = ' '.join(context.args).strip().lower()
    if any(banned in guess for banned in ["()", "&"]):
        await update.message.reply_text("❌ Invalid Guess Format")
        return

    correct_name = character.get('name', '').lower()
    if not correct_name:
        await update.message.reply_text("❌ Wrong Guess! try again.")
        return

    # Check if the guess is correct
    if guess in correct_name.split() or guess == correct_name:
        first_correct_guesses[chat_id] = user_id
        
        # Store character in user's collection
        await user_collection.update_one(
            {'id': user_id}, 
            {'$push': {'characters': character}}, 
            upsert=True
        )

        del sent_characters[chat_id]  # Remove character after successful guess

        keyboard = [[InlineKeyboardButton("See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]
        await update.message.reply_text(
            f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You Guessed a New Character ✅️\n\n'
            f'𝗖𝗢𝗦𝗣𝗟𝗔𝗬: <b>{character["name"]}</b>\n'
            f'𝗔𝗡𝗜𝗠𝗘: <b>{character["anime"]}</b>\n'
            f'𝗥𝗔𝗜𝗥𝗧𝗬: <b>{character["rarity"]}</b>\n\n'
            'Character added to Your harem!',
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text('❌ Please provide a Character ID')
        return
    character_id = context.args[0]
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('❌ No Characters in Your Collection')
        return
    if not any(c['id'] == character_id for c in user['characters']):
        await update.message.reply_text('❌ Character Not Found in Your Collection')
        return
    await user_collection.update_one({'id': user_id}, {'$addToSet': {'favorites': character_id}})
    await update.message.reply_text(f'⭐ Character {character_id} added to Favorites')

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    results = []

    if query.startswith('collection.'):
        user_id = query.split('.')[1]
        if not user_id.isdigit():
            return
        
        user_data = await user_collection.find_one({'id': int(user_id)})
        if not user_data or 'characters' not in user_data:
            return
        
        for character in user_data['characters']:
            results.append(
                InlineQueryResultArticle(
                    id=str(character['id']),
                    title=character['name'],
                    description=f"Anime: {character['anime']}\nRarity: {character['rarity']}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"Character: {character['name']}\nAnime: {character['anime']}\nRarity: {character['rarity']}"
                    )
                )
            )

    await update.inline_query.answer(results, cache_time=0)

application.add_handler(CommandHandler("guess", guess))
application.add_handler(CommandHandler("fav", fav))
application.add_handler(MessageHandler(filters.ALL, message_counter))
application.add_handler(InlineQueryHandler(inlinequery))

if __name__ == "__main__":
    application.run_polling(drop_pending_updates=True)

