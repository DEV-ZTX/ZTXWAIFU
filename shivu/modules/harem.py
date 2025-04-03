#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
# For Waifu/Husbando telegram bots.
# Speacial thanks for this amazing repo: https://github.com/MyNameIsShekhar
# Updated and Added new commands, features and style by https://github.com/lovetheticx

# ⊢⊸⊸⊸⊸⊸ New Features ⊸⊸⊸⊸⊸ 
# ⊢ Added Harem Mode                  
# ⊢ Added more buttons for manage harem list
# ⊢ Added pagination for harem list
# ⊢ Updated harem message to new style
# ⊢ Updated max caption length for Harem message
# ⊢ User Friendly functions, easy to understand and use
# ⊢ And much more...
#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬


# <============================================== IMPORTS =========================================================>

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from itertools import groupby
import math
from html import escape
from shivu import PHOTO_URL, Config
import random
from shivu import collection, user_collection, application
from telegram.error import BadRequest

MAX_CAPTION_LENGTH = 1024

# <============================================= HAREM COMMAND =====================================================>

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    user_id = update.effective_user.id
    user = await user_collection.find_one({'id': user_id})
    context.user_data["harem_owner_id"] = user_id

    if not user or 'characters' not in user or not user['characters']:
        message = '⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n◈ ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀ! \n⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋'
        await update.message.reply_text(message) if update.message else await update.callback_query.edit_message_text(message)
        return
    
    characters = sorted(list(user['characters']), key=lambda x: (x['anime'], x['id']))
    character_counts = {k: sum(1 for _ in v) for k, v in groupby(characters, key=lambda x: x['id'])}
    rarity_mode = await get_user_rarity_mode(user_id)

    if rarity_mode != 'ᴅᴇꜰᴀᴜʟᴛ':
        characters = [char for char in characters if char.get('rarity') == rarity_mode]
    
    total_pages = max(1, math.ceil(len(characters) / 15))
    page = max(0, min(page, total_pages - 1))

    harem_message = f"<b>{escape(update.effective_user.first_name)}'ꜱ ʜᴀʀᴇᴍ - ᴘᴀɢᴇ {page+1}/{total_pages}</b>\n"
    current_characters = characters[page * 15 : (page + 1) * 15]
    grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}
    
    for anime, chars in grouped_characters.items():
        anime_count = await collection.count_documents({"anime": anime})
        harem_message += f'\n⌬<b>{anime} {len(chars)}/{anime_count}</b>\n⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n'
        for character in chars:
            count = character_counts.get(character['id'], 1)
            harem_message += f'➥{character["id"]} | {character["rarity"][0]} | {character["name"]} ×{count}\n'
        harem_message += "⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋\n"
    
    keyboard = [[InlineKeyboardButton(f"🌐 ꜱᴇᴇ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ({len(user['characters'])})", switch_inline_query=f"collection {user_id}")],
                [InlineKeyboardButton("ᴄʜᴀɴɢᴇ ʀᴀʀɪᴛʏ ᴍᴏᴅᴇ", callback_data="change_rarity_mode")]]
    
    if total_pages > 1:
        nav_buttons = []
        if page > 4:
            nav_buttons.append(InlineKeyboardButton("◀️ 5x", callback_data=f"harem:{page-5}:{user_id}"))
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ 1x", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("1x ▶️", callback_data=f"harem:{page+1}:{user_id}"))
        if page < total_pages - 5:
            nav_buttons.append(InlineKeyboardButton("5x ▶️", callback_data=f"harem:{page+5}:{user_id}"))
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        img_url = None
        if 'favorites' in user and user['favorites']:
            fav_character_id = user['favorites'][0]
            fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)
            if fav_character:
                img_url = fav_character.get('img_url')
        if not img_url and user['characters']:
            img_url = random.choice(user['characters']).get('img_url')

        if img_url:
            await update.message.reply_photo(photo=img_url, caption=harem_message, reply_markup=reply_markup, parse_mode='HTML') if update.message \
                else await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text(harem_message, reply_markup=reply_markup, parse_mode='HTML') if update.message \
                else await update.callback_query.edit_message_caption(caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
    except BadRequest:
        await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
    except Exception as e:
        print(f"Failed to edit message: {e}")

# <======================================== Haremmode Command ===================================================>
 
async def haremmode(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_rarity_mode = await get_user_rarity_mode(user_id)
    
    # Define all possible rarity modes
    all_rarities = [
        "⚪️ Common", "🟣 Rare", "🟡 Legendary",  
        "🟢 Medium", "💮 Special", "🔮 Limited",  
        "🎐 Celestial", "ᴅᴇꜰᴀᴜʟᴛ"
    ]
    names = [
        "⚪️ ᴄᴏᴍᴍᴏɴ", "🟣 ʀᴀʀᴇ", "🟡 ʟᴇɢᴇɴᴅᴀʀʏ", 
        "🟢 ᴍᴇᴅɪᴜᴍ", "💮 ꜱᴘᴇᴄɪᴀʟ", "🔮 ʟɪᴍɪᴛᴇᴅ", 
        "🎐 ᴄᴇʟᴇꜱᴛɪᴀʟ", "ᴅᴇꜰᴀᴜʟᴛ"
    ]
    
    # Create buttons with a checkmark for the current rarity mode
    rarities_buttons = []
    for rarity in all_rarities:
        name = names[all_rarities.index(rarity)]
        emoji = "✅ " if rarity == current_rarity_mode else ""
        rarities_buttons.append(InlineKeyboardButton(f"{emoji}{name}", callback_data=f"rarity:{rarity}"))
    
    # Format the buttons into a keyboard
    reply_markup = InlineKeyboardMarkup([
        rarities_buttons[i:i + 3] for i in range(0, len(rarities_buttons), 3)
    ])
    
    #picture_url = random.choice(Config.PHOTO_URL)    #REMOVE "#" set random picture from your config.py
    picture_url = 'https://graph.org/file/992f31b75e3fa1ebed9f8-43f6c2e69aafb3928a.jpg'
    
    if update.message:
        await update.message.reply_photo(photo=picture_url, caption="<b>⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋</b>\n<b>◈ ꜱᴇʟᴇᴄᴛ ᴀ ʀᴀʀɪᴛʏ ᴍᴏᴅᴇ:</b> \n<b>⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋</b>", reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.callback_query.message.reply_photo(photo=picture_url, caption="<b>⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋</b>\n<b>◈ ꜱᴇʟᴇᴄᴛ ᴀ ʀᴀʀɪᴛʏ ᴍᴏᴅᴇ:</b> \n<b>⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋⚋</b>", reply_markup=reply_markup, parse_mode='HTML')

# <============================================== Harem Callback =========================================================>
        
async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    print(f"Received callback: {query.data}")  # Debugging line

    try:
        _, page, user_id = query.data.split(':')
        page = int(page)
        user_id = int(user_id)
    except ValueError:
        await query.answer("Invalid callback data", show_alert=True)
        return

    await harem(update, context, page)
# <========================================== Haremmode Callback =====================================================>
    
async def change_rarity_mode_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = update.effective_user.id

    # Retrieve the ID of the user who issued the /harem command
    harem_owner_id = context.user_data.get("harem_owner_id")

    # Check if the user pressing the button is the harem owner
    if user_id != harem_owner_id:
        await query.answer("𝗗𝗢𝗡𝗧 𝗧𝗢𝗨𝗖𝗛 𝗔𝗪𝗪 💢", show_alert=True)
        return

    # Continue with changing the rarity mode
    await haremmode(update, context)
        
async def haremmode_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    print(f"Received callback data: {query.data}")  # Debugging

    harem_owner_id = context.user_data.get("harem_owner_id")
    if user_id != harem_owner_id:
        await query.answer("𝗗𝗢𝗡𝗧 𝗧𝗢𝗨𝗖𝗛 𝗔𝗪𝗪 💢", show_alert=True)
        return

    data = query.data.split(':')
    if len(data) != 2 or data[0] != 'rarity':
        await query.answer("Invalid callback data", show_alert=True)
        return

    rarity_mode = data[1]
    print(f"Changing rarity mode to: {rarity_mode}")  # Debugging

    await update_user_rarity_mode(user_id, rarity_mode)
    await harem(update, context)

# <======================================== Haremmode Command ===================================================>
# <==================================== Getting for User Rarity Mode ==================================================>
    
async def get_user_rarity_mode(user_id: int) -> str:
    user = await user_collection.find_one({'id': user_id})
    print(f"User data for rarity mode: {user}")  # Debugging
    return user.get('rarity_mode', 'ᴅᴇꜰᴀᴜʟᴛ') if user else 'ᴅᴇꜰᴀᴜʟᴛ'

# <============================================== FOR ERRORS =========================================================>
    
async def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")

# <============================================== HANDLERS ===========================================================>
    
application.add_handler(CommandHandler("cmode", haremmode, block=False))
application.add_handler(CommandHandler("harem", harem, block=False))
application.add_handler(CallbackQueryHandler(haremmode_callback, pattern=r"^rarity:"))
application.add_handler(CallbackQueryHandler(change_rarity_mode_callback, pattern=r"^change_rarity_mode$"))
application.add_handler(CallbackQueryHandler(harem_callback, pattern=r"^harem"))
application.add_error_handler(error)

# <============================================== END ================================================================>
# https://github.com/lovetheticx
