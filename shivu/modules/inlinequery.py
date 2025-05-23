#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
# For Waifu/Husbando telegram bots.
# Updated and Added new commands, features and style by https://github.com/lovetheticx
#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

import re
import time
import html
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING

from telegram import Update, InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, CallbackContext, CallbackQueryHandler, CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import user_collection, collection, application, db


# collection
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

# user_collection
db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

def append_emoji_labels(character_name: str, caption: str) -> str:
    if '👘' in character_name:
        caption += "\n\n👘𝑲𝒊𝒎𝒐𝒏𝒐👘"
    elif '❄️' in character_name:
        caption += "\n\n❄️𝑾𝒊𝒏𝒕𝒆𝒓❄️"
    elif '🐰' in character_name:
        caption += "\n\n🐰𝑩𝒖𝒏𝒏𝒚🐰"
    elif '🎮' in character_name:
        caption += "\n\n🎮𝑮𝒂𝒎𝒆🎮"
    elif '🎄' in character_name:
        caption += "\n\n🎄𝑪𝒉𝒓𝒊𝒔𝒕𝒎𝒂𝒔🎄"
    elif '🎃' in character_name:
        caption += "\n\n🎃𝑯𝒂𝒍𝒍𝒐𝒘𝒆𝒆𝒏🎃"
    elif '🏖️' in character_name:
        caption += "\n\n🏖️𝑺𝒖𝒎𝒎𝒆𝒓🏖️"
    elif '🧹' in character_name:
        caption += "\n\n🧹𝑴𝒂𝒊𝒅🧹"
    elif '🎨' in character_name:
        caption += "\n\n🎨𝑨𝒓𝒕𝒊𝒔𝒕🎨"
    elif '☔' in character_name:
        caption += "\n\n☔𝑹𝒂𝒊𝒏☔"
    elif '🎒' in character_name:
        caption += "\n\n🎒𝑺𝒄𝒉𝒐𝒐𝒍🎒"
    elif '🎊' in character_name:
        caption += "\n\n🎊𝑪𝒉𝒆𝒆𝒓𝒍𝒆𝒂𝒅𝒆𝒓𝒔🎊"
    elif '🏨' in character_name:
        caption += "\n\n🏨𝑵𝒖𝒓𝒔𝒆🏨"
    elif '🪼' in character_name:
        caption += "\n\n🪼𝑴𝒂𝒓𝒊𝒏𝒆🪼"
    elif '🎸' in character_name:
        caption += "\n\n🎸𝑹𝒐𝒄𝒌🎸"
    elif '💞' in character_name:
        caption += "\n\n💞𝑽𝒂𝒍𝒆𝒏𝒕𝒊𝒏𝒆💞"
    elif '🌸' in character_name:
          caption += "\n\n🌸𝑩𝒍𝒐𝒔𝒔𝒐𝒎🌸"
    elif '🤓' in character_name:
          caption += "\n\n🤓𝑵𝒆𝒓𝒅🤓"
    elif '🏀' in character_name:
          caption += "\n\n🏀𝑩𝒂𝒔𝒌𝒆𝒕𝒃𝒂𝒍𝒍🏀"
    elif '💍' in character_name:
          caption += "\n\n💍𝑾𝒆𝒅𝒅𝒊𝒏𝒈💍"
    return caption

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    search_terms = query.split(" ")[1:] if query.startswith("collection.") else []  # ✅ Define search_terms

    if query.startswith('collection.'):
        user_id = str(query.split(' ')[0].split('.')[1])  
        if user_id.isdigit():
            if user_id in user_collection_cache:
                user = user_collection_cache[user_id]
            else:
                user = await user_collection.find_one({'id': int(user_id)})

            if user:
                all_characters = list({v['id']: v for v in user['characters']}.values())

                # ✅ Check if search_terms exist before applying regex
                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    all_characters = [
                        character for character in all_characters
                        if regex.search(character['name']) or regex.search(character['anime'])
                    ]
            else:
                all_characters = []
        else:
            all_characters = []
    else:  # ✅ Ensure this aligns properly
        if query:
            regex = re.compile(query, re.IGNORECASE)
            all_characters = list(
                await collection.find({"$or": [{"name": regex}, {"anime": regex}]}).to_list(length=None)
            )
        else:
            if 'all_characters' in all_characters_cache:
                all_characters = all_characters_cache['all_characters']
            else:
                all_characters = list(await collection.find({}).to_list(length=None))
                all_characters_cache['all_characters'] = all_characters

    characters = all_characters[offset:offset+50]
    if len(characters) > 50:
        characters = characters[:50]
        next_offset = str(offset + 50)
    else:
        next_offset = str(offset + len(characters))

    results = []
    for character in characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_characters = await collection.count_documents({'anime': character['anime']})

        if query.startswith('collection.'):
            user_character_count = sum(c['id'] == character['id'] for c in user['characters'])
            user_anime_characters = sum(c['anime'] == character['anime'] for c in user['characters'])
            caption = f"<b>⫸OᴡO ʟᴏᴏᴋ ᴀᴛ <a href='tg://user?id={str(user['id'])}'>{escape(user.get('first_name', str(user['id'])))}</a>'ꜱ ᴡᴀɪꜰᴜ</b>\n\n"       # Check for tags in character's name

            if '👘' in character['name']:

                    caption += "\n\n👘𝑲𝒊𝒎𝒐𝒏𝒐👘 "

            elif '❄️' in character['name']:

                    caption += "\n\n❄️𝑾𝒊𝒏𝒕𝒆𝒓❄️"

            elif '🐰' in character['name']:

                    caption += "\n\n🐰𝑩𝒖𝒏𝒏𝒚🐰"

            elif '🎮' in character['name']:

                    caption += "\n\n 🎮𝑮𝒂𝒎𝒆🎮 "

            elif '🎄' in character['name']:

                    caption += "\n\n🎄𝑪𝒉𝒓𝒊𝒔𝒕𝒎𝒂𝒔🎄"

            elif '🎃' in character['name']:

                    caption += "\n\n🎃𝑯𝒂𝒍𝒍𝒐𝒘𝒆𝒆𝒏🎃"

            elif '🏖️' in character['name']:

                    caption += "\n\n🏖️𝑺𝒖𝒎𝒎𝒆𝒓🏖️ "

            elif '🧹' in character['name']:

                    caption += "\n\n🧹𝑴𝒂𝒊𝒅🧹"

            elif '🎨𝑨𝒓𝒕𝒊𝒔𝒕🎨' in character['name']:

                    caption += "\n\n🎨𝑨𝒓𝒕𝒊𝒔𝒕🎨"

            elif '☔' in character['name']:

                    caption += "\n\n☔𝑹𝒂𝒊𝒏☔"

            elif '🎒' in character['name']:

                    caption += "\n\n🎒𝑺𝒄𝒉𝒐𝒐𝒍🎒"

            elif '🏨' in character['name']:

                    caption += "\n\n🏨𝑵𝒖𝒓𝒔𝒆🏨"

            elif '🎊' in character['name']:

                    caption += "\n\n🎊𝑪𝒉𝒆𝒆𝒓𝒍𝒆𝒂𝒅𝒆𝒓𝒔🎊"

            elif '🪼' in character['name']:

                    caption += "\n\n🪼𝑴𝒂𝒓𝒊𝒏𝒆🪼"

            elif '🌸' in character['name']:

                    caption += "\n\n🌸𝑩𝒍𝒐𝒔𝒔𝒐𝒎🌸"

            elif '💞' in character['name']:

                    caption += "\n\n💞𝑽𝒂𝒍𝒆𝒏𝒕𝒊𝒏𝒆💞"

            elif '🎸' in character['name']:
                  
                    caption += "\n\n🎸𝑹𝒐𝒄𝒌🎸"

            elif '🤓' in character['name']:
                                     
                    caption += "\n\n🤓𝑵𝒆𝒓𝒅🤓"

            elif '🏀' in character['name']:
                    
                    caption += "\n\n🏀𝑩𝒂𝒔𝒌𝒆𝒕𝒃𝒂𝒍𝒍🏀"

            elif '💍' in character['name']:
                  
                    caption += "\n\n💍𝑾𝒆𝒅𝒅𝒊𝒏𝒈💍"
        else:
            caption = (
            f"<b>Look At This Cosplay....!!!</b>\n\n"
            f"<b>{character['anime']}</b>\n"
            f"<b>{character['id']}:</b> {character['name']}\n"
            f"( <b>{character['rarity'][0]}𝙍𝘼𝙍𝙄𝙏𝙔:</b> {character['rarity'][2:]} )"
            f"\n\n<b>Gʟᴏʙᴀʟʟʏ Gʀᴀʙʙᴇᴅ {global_count} Tɪᴍᴇꜱ</b>"
        )
    # Check for tags in character's name
            if '👘' in character['name']:

                    caption += "\n\n👘𝑲𝒊𝒎𝒐𝒏𝒐👘 "

            elif '❄️' in character['name']:

                    caption += "\n\n❄️𝑾𝒊𝒏𝒕𝒆𝒓❄️"

            elif '🐰' in character['name']:

                    caption += "\n\n🐰𝑩𝒖𝒏𝒏𝒚🐰"

            elif '🎮' in character['name']:

                    caption += "\n\n 🎮𝑮𝒂𝒎𝒆🎮 "

            elif '🎄' in character['name']:

                    caption += "\n\n🎄𝑪𝒉𝒓𝒊𝒔𝒕𝒎𝒂𝒔🎄"

            elif '🎃' in character['name']:

                    caption += "\n\n🎃𝑯𝒂𝒍𝒍𝒐𝒘𝒆𝒆𝒏🎃"

            elif '🏖️' in character['name']:

                    caption += "\n\n🏖️𝑺𝒖𝒎𝒎𝒆𝒓🏖️ "

            elif '🧹' in character['name']:

                    caption += "\n\n🧹𝑴𝒂𝒊𝒅🧹"

            elif '🎨𝑨𝒓𝒕𝒊𝒔𝒕🎨' in character['name']:

                    caption += "\n\n🎨𝑨𝒓𝒕𝒊𝒔𝒕🎨"

            elif '☔' in character['name']:

                    caption += "\n\n☔𝑹𝒂𝒊𝒏☔"

            elif '🎒' in character['name']:

                    caption += "\n\n🎒𝑺𝒄𝒉𝒐𝒐𝒍🎒"

            elif '🏨' in character['name']:

                    caption += "\n\n🏨𝑵𝒖𝒓𝒔𝒆🏨"

            elif '🎊' in character['name']:

                    caption += "\n\n🎊𝑪𝒉𝒆𝒆𝒓𝒍𝒆𝒂𝒅𝒆𝒓𝒔🎊"

            elif '🪼' in character['name']:

                    caption += "\n\n🪼𝑴𝒂𝒓𝒊𝒏𝒆🪼"

            elif '🌸' in character['name']:

                    caption += "\n\n🌸𝑩𝒍𝒐𝒔𝒔𝒐𝒎🌸"

            elif '💞' in character['name']:

                    caption += "\n\n💞𝑽𝒂𝒍𝒆𝒏𝒕𝒊𝒏𝒆💞"

            elif '🎸' in character['name']:
                  
                    caption += "\n\🎸𝑹𝒐𝒄𝒌🎸"

            elif '🤓' in character['name']:
                                     
                    caption += "\n\n🤓𝑵𝒆𝒓𝒅🤓"

            elif '🏀' in character['name']:
                    
                    caption += "\n\n🏀𝑩𝒂𝒔𝒌𝒆𝒕𝒃𝒂𝒍𝒍🏀"
            
            elif '💍' in character['name']:
                    
                    caption += "\n\n💍𝑾𝒆𝒅𝒅𝒊𝒏𝒈💍"
            
        
        # Add inline button for showing top grabbers
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 ᴛᴏᴘ 10 ɢʀᴀʙʙᴇʀꜱ", callback_data=f"show_top_grabbers_{character['id']}")]
        ])

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['img_url'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                caption=caption,
                parse_mode='HTML',
                reply_markup=keyboard  # Add the keyboard here
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

async def show_top_grabbers(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    print("Received Callback Query:", query.data)  # Debugging

    # Extract character_id from callback data
    if query.data.startswith("show_top_grabbers_"):
        character_id = query.data.replace("show_top_grabbers_", "")

        try:
            character_id = int(character_id)  # Ensure it's an integer
        except ValueError:
            await query.answer("Invalid character ID.", show_alert=True)
            return

    cursor = user_collection.aggregate([
        {"$match": {"characters.id": character_id}},
        {"$project": {
            "user_id": 1,
            "username": 1,
            "first_name": 1,
            "character_count": {
                "$size": {
                    "$filter": {
                        "input": "$characters",
                        "as": "character",
                        "cond": {"$eq": ["$$character.id", character_id]}
                    }
                }
            }
        }},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])

    leaderboard_data = await cursor.to_list(length=10)

    if not leaderboard_data:
        # If no grabbers found, inform the user via an alert
        await query.answer("No grabbers found for this character.", show_alert=True)
        return  # Exit the function early

    # Format the leaderboard message
    leaderboard_message = "<b>🌐 ᴛᴏᴘ 10 ɢʀᴀʙʙᴇʀꜱ ᴏꜰ ᴛʜɪꜱ ᴄʜᴀʀᴀᴄᴛᴇʀ:</b>\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username')
        first_name = user.get('first_name', 'Unknown')

        if username:
            display_name = f"<a href='https://t.me/{username}'>{html.escape(first_name)}</a>"
        else:
            display_name = html.escape(first_name)

        character_count = user.get('character_count', 0)
        leaderboard_message += f"┣ {i:02d}.➥ {display_name} ➩ {character_count}\n"

    # Send the leaderboard message
    await query.message.reply_text(leaderboard_message, parse_mode="HTML")
    await query.answer()  # Acknowledge button press

    await query.edit_message_text(
        text=leaderboard_message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    # Add "Back" button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↻ ʙᴀᴄᴋ", callback_data=f"show_character_{character_id}")]
    ])

    await query.answer()
    await query.edit_message_text(text=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)

    # Add "Back" button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↻ ʙᴀᴄᴋ", callback_data=f"show_character_{character_id}")]
    ])

    await query.answer()
    await query.edit_message_text(text=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)
    # Add "Back" button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↻ ʙᴀᴄᴋ", callback_data=f"show_character_{character_id}")]
    ])

    await query.answer()
    await query.edit_message_text(text=leaderboard_message, parse_mode='HTML', reply_markup=keyboard)


async def show_character_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    character_id = int(query.data.split('_')[2])  # Convert to integer

    # Fetch character information
    character = await collection.find_one({'id': character_id})
    if not character:
        await query.answer("Character not found.")
        return

    global_count = await user_collection.count_documents({'characters.id': character_id})
    anime_characters = await collection.count_documents({'anime': character['anime']})

    caption = (
        f"<b>Lᴏᴏᴋ Aᴛ Tʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ....!!</b>\n\n"
        f"<b>{character['id']}:</b> {character['name']}\n"
        f"<b>{character['anime']}</b>\n"
        f"( <b>{character['rarity'][0]} 𝙍𝘼𝙍𝙄𝙏𝙔:</b> {character['rarity'][2:]} )"
        f"\n\n<b>Gʟᴏʙᴀʟʟʏ Gʀᴀʙʙᴇᴅ {global_count} Tɪᴍᴇꜱ</b>"
    )
    caption = append_emoji_labels(character['name'], caption)

    # Add inline button for showing top grabbers
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ᴛᴏᴘ 10 ɢʀᴀʙʙᴇʀꜱ", callback_data=f"top_grabbers_{character_id}")]
    ])

    await query.answer()
    await query.edit_message_text(text=caption, parse_mode='HTML', reply_markup=keyboard)

# Register the new handler
application.add_handler(CallbackQueryHandler(show_character_info, pattern=r"^show_character_"))
application.add_handler(CallbackQueryHandler(show_top_grabbers, pattern=r"^show_top_grabbers_\d+$"))
application.add_handler(InlineQueryHandler(inlinequery, block=False))

# by https://github.com/lovetheticx
