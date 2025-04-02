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
# ⊢ Now you can use status command to check profile status
# ⊢ And much more...
#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬


# <============================================== IMPORTS =========================================================>
from pyrogram import Client, filters
from shivu import shivuu, collection, user_collection, group_user_totals_collection
import random
import asyncio

async def get_user_collection():
    return await user_collection.find({}).to_list(length=None)

async def get_progress_bar(user_waifus_count, total_waifus_count):
    bar_width = 10
    progress = user_waifus_count / total_waifus_count if total_waifus_count != 0 else 0
    progress_percent = progress * 100
    filled_width = int(progress * bar_width)
    empty_width = bar_width - filled_width
    progress_bar = "▰" * filled_width + "▱" * empty_width
    return progress_bar, progress_percent

async def get_chat_top(chat_id: int, user_id: int) -> int:
    pipeline = [
        {"$match": {"group_id": chat_id}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    cursor = group_user_totals_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('user_id') == user_id:
            return i
    return 0

async def get_global_top(user_id: int) -> int:
    pipeline = [
        {"$project": {"id": 1, "characters_count": {"$size": {"$ifNull": ["$characters", []]}}}},
        {"$sort": {"characters_count": -1}}
    ]
    cursor = user_collection.aggregate(pipeline)
    leaderboard_data = await cursor.to_list(length=None)
    
    for i, user in enumerate(leaderboard_data, start=1):
        if user.get('id') == user_id:
            return i
    return 0

@shivuu.on_message(filters.command(["status", "profile"]))
async def send_grabber_status(client, message):
    try:
        loading_message = await message.reply("㊣ 𝖕𝖑𝖊𝖆𝖘𝖊 𝖜𝖆𝖎𝖙")
        for i in range(1, 6):
            await asyncio.sleep(1)
            await loading_message.edit_text("㊣ 𝖕𝖑𝖊𝖆𝖘𝖊 𝖜𝖆𝖎𝖙 " + "►" * i)

        user_collection_data = await get_user_collection()
        user_collection_count = len(user_collection_data)
        user_id = message.from_user.id
        user = await user_collection.find_one({'id': user_id})
        total_count = len(user.get('characters', [])) if user else 0
        total_waifus_count = await collection.count_documents({})
        chat_top = await get_chat_top(message.chat.id, user_id)
        global_top = await get_global_top(user_id)
        progress_bar, progress_percent = await get_progress_bar(total_count, total_waifus_count)
        
        grabber_status = (
            f"╒═══「 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢 」\n"
            f"╰─➩ ᴜsᴇʀ: `{message.from_user.first_name}`\n"
            f"╰─➩ ᴜsᴇʀ ɪᴅ: `{message.from_user.id}`\n"
            f"╰─➩ ᴛᴏᴛᴀʟ ᴡᴀɪғᴜ: `{total_count}/{total_waifus_count}` ({progress_percent:.3f}%)\n"
            f"╰─➩ ᴜꜱᴇʀ ʟᴇᴠᴇʟ: {user_collection_count // 100 + 1}\n"
            f"╰─➩ ᴘʀᴏɢʀᴇss ʙᴀʀ: {progress_bar}\n"
            f"╰────────────────── \n\n"
            f"╭──────────────────\n"
            f"╭─➩ 🌍ᴄʜᴀᴛ ᴛᴏᴘ: `{chat_top}`\n"
            f"╰─➩ 🌎ɢʟᴏʙᴀʟ ᴛᴏᴘ: `{global_top}`\n"
            f"╰──────────────────"
        )
        
        user_photo = None
        if message.from_user.photo:
            photos = await client.get_profile_photos(user_id, limit=1)
            if photos:
                user_photo = await client.download_media(photos[0].file_id)
        
        if user_photo:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=user_photo,
                caption=grabber_status
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=grabber_status
            )
        
        await loading_message.delete()
    except Exception as e:
        print(f"Error: {e}")

