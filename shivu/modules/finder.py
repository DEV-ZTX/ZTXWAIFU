import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection
import time
import html
from html import escape
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

DEVS = (7757912959)

@bot.on_message(filters.command(["waifufind"]))
async def waifufind(_, message: t.Message):
    if len(message.command) < 2:
        return await message.reply_text("\U0001F516ᴘʟᴇᴀꜱᴇ ᴡʀɪᴛᴇ ᴡᴀɪꜰᴜ ɪᴅ ᴛᴏᴏ", quote=True)
    
    # Pad the waifu ID with zeros to ensure it is 4 characters long
    waifu_id = message.command[1].zfill(4)
    waifu = await collection.find_one({'id': waifu_id})
    
    if not waifu:
        return await message.reply_text("ᴛʜᴇʀᴇ'ꜱ ɴᴏ ᴀɴʏ ᴡᴀɪꜰᴜ ᴡɪᴛʜ ᴛʜɪꜱ ɪᴅ ❌", quote=True)
    
    # Get the top 10 users with the most of this waifu in the current chat
    top_users = await user_collection.aggregate([
        {'$match': {'characters.id': waifu_id}},
        {'$unwind': '$characters'},
        {'$match': {'characters.id': waifu_id}},
        {'$group': {'_id': '$id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]).to_list(length=5)
    
    # Get the usernames of the top users
    usernames = []
    for user_info in top_users:
        user_id = user_info['_id']
        try:
            user = await bot.get_users(user_id)
            usernames.append(user.username if user.username else f"➥ {user_id}")
        except Exception as e:
            print(e)
            usernames.append(f"{user_id}")
    
    # Construct the caption
    caption = (
        f"💠 𝗔𝗕𝗢𝗨𝗧 𝗪𝗔𝗜𝗙𝗨:\n"
        f"┏━━━━━━━━━━━━━⧫\n"
        f"◈𝗡𝗔𝗠𝗘: {waifu['name']}\n"
        f"◈𝗥𝗔𝗥𝗜𝗧𝗬: {waifu['rarity']}\n"
        f"◈𝗔𝗡𝗜𝗠𝗘: {waifu['anime']}\n"
        f"◈𝗜𝗗: {waifu['id']}\n"
        f"┗━━━━━━━━━━━━━⧫\n\n"
        f"⨈ ʜᴇʀᴇ ɪꜱ ᴛʜᴇ ʟɪꜱᴛ ᴏꜰ ᴜꜱᴇʀꜱ ᴡʜᴏ ʜᴀᴠᴇ ᴡᴀɪꜰᴜꜱ:\n"
    )
    for i, user_info in enumerate(top_users):
        count = user_info['count']
        username = usernames[i]
        caption += f"┣ {i:02d}.➥ [{username}](tg://user?id={user_info['_id']}) ⇒ {count}\n"

    
    # Reply with the waifu information and top users
    await message.reply_photo(photo=waifu['img_url'], caption=caption)

@bot.on_message(filters.command(["anime"]))
async def anime(_, message: t.Message):
    if len(message.command) < 2:
        return await message.reply_text("⛔ᴘʟᴇᴀꜱᴇ ᴡʀɪᴛᴇ ᴀɴɪᴍᴇ ɴᴀᴍᴇ", quote=True)

    anime_name = " ".join(message.command[1:])
    characters = await collection.find({'anime': {'$regex': anime_name, '$options': 'i'}}).to_list(length=None)
    
    if not characters:
        return await message.reply_text(f"⛔ᴡᴀɪꜰᴜꜱ ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰʀᴏᴍ ᴛʜɪꜱ ᴀɴɪᴍᴇ: {anime_name}.", quote=True)

    # Create the message with character details
    captions = [
        f"🎏 𝑵𝒂𝒎𝒆: {char['name']}\n🆔 𝑰𝑫: {char['id']}\n💌 𝑹𝒂𝒓𝒊𝒕𝒚: {char['rarity']}\n"
        for char in characters
    ]
    response = "\n".join(captions)

    # Add an inline button for searching characters from this anime
    search_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 See Characters", switch_inline_query_current_chat=anime_name)]
    ])

    # Send the message with the inline button
    await message.reply_text(
        f"🍁 𝑪𝒉𝒂𝒓𝒂𝒄𝒕𝒆𝒓𝒔 𝒇𝒓𝒐𝒎 {anime_name}:\n\n{response}",
        reply_markup=search_button,
        quote=True
    )
