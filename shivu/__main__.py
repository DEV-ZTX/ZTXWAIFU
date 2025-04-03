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
    
    # Store entire character data instead of just the ID
    sent_characters[chat_id] = character  

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"""<b>{character['rarity'][0]}Oᴡᴏ! ᴀ {character['rarity'][2:]} ᴄᴏsᴘʟᴀʏ ʜᴀs ᴀᴘᴘᴇᴀʀᴇᴅ!</b>\n<b>ᴀᴅᴅ ʜᴇʀ ᴛᴏ ʏᴏᴜʀ ʜᴀʀᴇᴍ ʙʏ sᴇɴᴅɪɴɢ</b>\n<b>/guess ɴᴀᴍᴇ</b>""",
        parse_mode='HTML'
    )

async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        print(f"[ERROR] No character found for chat_id: {chat_id}")
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_html("<b>❌ You can't use these types of words.</b>")
        return

    # Ensure last_character exists
    character = last_characters.get(chat_id)
    if not character:
        print(f"[ERROR] last_characters[{chat_id}] is missing!")
        return

    character_name = character['name'].lower()
    name_parts = character_name.split()

    # Ensure sent_characters exists
    if chat_id not in sent_characters or character['id'] not in sent_characters[chat_id]:
        print(f"[ERROR] sent_characters data is missing for chat_id: {chat_id}")
        return

    time_sent = sent_characters[chat_id][character['id']]
    time_taken = time.time() - time_sent
    minutes, seconds = divmod(int(time_taken), 60)

    # Checking if guess matches character name
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id

        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})

            await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
        else:
            new_user_data = {
                'id': user_id,
                'username': update.effective_user.username if hasattr(update.effective_user, 'username') else '',
                'first_name': update.effective_user.first_name,
                'characters': [character],
            }
            print(f"[INFO] Inserting new user: {new_user_data}")
            await user_collection.insert_one(new_user_data)

        keyboard = [[InlineKeyboardButton("🌐 See Collection", switch_inline_query_current_chat=f"collection.{user_id}")]]
        message = (
            f'✅ <b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You got a new waifu! \n\n'
            f'🌸 𝗡𝗔𝗠𝗘: <b>{character["name"]}</b>\n'
            f'❇️ 𝗔𝗡𝗜𝗠𝗘: <b>{character["anime"]}</b>\n'
            f'{character["rarity"][0]} 𝗥𝗔𝗥𝗜𝗧𝗬: <b>{character["rarity"]}</b>\n\n'
            f'⌛️ 𝗧𝗜𝗠𝗘 𝗧𝗔𝗞𝗘𝗡: {minutes} minutes and {seconds} seconds'
        )

        await update.message.reply_text(message, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        print(f"[INFO] Incorrect guess from {user_id}: {guess}")
        await update.message.reply_text(
            '❌ <b>Character name is incorrect. Try guessing again!</b>', parse_mode='HTML'
        )

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_html('<b>ɢɪᴠᴇ ᴍᴇ ᴀ ᴡᴀɪғᴜ ɪᴅ ᴛᴏᴏ 🤖</b>')
        return

    character_id = context.args[0]
    user = await user_collection.find_one({'id': user_id})

    if not user:
        await update.message.reply_html('<b>ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀɴʏ ᴡᴀɪғᴜs ɪɴ ʏᴏᴜʀ ʜᴀʀᴇᴍ 😢</b>')
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await update.message.reply_html('<b>ʏᴏᴜ ᴅᴏɴᴛ ᴏᴡɴ ᴛʜɪꜱ ᴡᴀɪꜰᴜ🤨</b>')
        return

    buttons = [
        [InlineKeyboardButton("🟢 Yes", callback_data=f"yes_{character_id}"), 
         InlineKeyboardButton("🔴 No", callback_data=f"no_{character_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_photo(
        photo=character["img_url"],
        caption=f"<b>Do you want to make this waifu your favorite..!</b>\n↬ <code>{character['name']}</code> <code>({character['anime']})</code>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_yes(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    character_id = query.data.split('_')[1]

    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': [character_id]}})
    await query.edit_message_caption(caption="<b>ᴡᴀɪғᴜ ʜᴀs ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ᴀs ᴀ ғᴀᴠᴏʀɪᴛᴇ!</b>", parse_mode="HTML")

async def handle_no(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer("Okay, no worries!")
    await query.edit_message_caption(caption="canceled.")

async def inlinequery(update: Update, context: CallbackContext) -> None:
    """Handles inline queries."""
    results = []  # Define your inline query results
    await update.inline_query.answer(results)
    
def main() -> None:
    """Run bot."""
    application.add_handler(CommandHandler("guess", guess))
    application.add_handler(CommandHandler("fav", fav))
    application.add_handler(InlineQueryHandler(inlinequery))
    application.add_handler(CallbackQueryHandler(handle_yes, pattern="yes_*"))
    application.add_handler(CallbackQueryHandler(handle_no, pattern="no_*"))
    # application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
    
