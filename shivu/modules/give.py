from pyrogram import Client, filters
from shivu import db, collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection
import asyncio
from shivu import shivuu as app
from shivu import sudo_users

DEV_LIST = [7678359785, 7757912959]

async def give_character(receiver_id, character_id):
    character = await collection.find_one({'id': character_id})

    if character:
        try:
            await user_collection.update_one(
                {'id': receiver_id},
                {'$push': {'characters': {'$each': [character]}}},  # Ensuring it's a list
                upsert=True  # Ensures user document exists
            )

            img_url = character['img_url']
            caption = (
                f"Successfully Given To {receiver_id}\n"
                f"Information As Follows\n"
                f"⫸Rarity: {character['rarity']}\n"
                f"⫸Anime: {character['anime']}\n"
                f"⫸Name: {character['name']}\n"
                f"⫸ID: {character['id']}"
            )

            return img_url, caption
        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("Character not found.")

@app.on_message(filters.command(["give"]) & filters.reply & filters.user(DEV_LIST))
async def give_character_command(client, message):
    print("Received /give command")

    if not message.reply_to_message:
        await message.reply_text("You need to reply to a user's message to give a character!")
        return

    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply_text("Please provide a character ID.")
            return

        character_id = str(command_parts[1])
        receiver_id = message.reply_to_message.from_user.id

        print(f"Giving character {character_id} to {receiver_id}")

        result = await give_character(receiver_id, character_id)

        if result:
            img_url, caption = result
            if not img_url:
                img_url = "https://via.placeholder.com/300"  # Placeholder image if missing

            await message.reply_photo(photo=img_url, caption=caption)
    except ValueError as e:
        print(f"ValueError: {e}")
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in give_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")

@app.on_message(filters.command(["add"]) & filters.user(DEV_LIST))
async def add_characters_command(client, message):
    user_id_to_add_characters_for = message.from_user.id
    result_message = await add_all_characters_for_user(user_id_to_add_characters_for)
    await message.reply_text(result_message)

async def kill_character(receiver_id, character_id):
    character = await collection.find_one({'id': character_id})

    if character:
        try:
            await user_collection.update_one(
                {'id': receiver_id},
                {'$pull': {'characters': {'id': str(character_id)}}}  # Convert character_id to string
            )

            return f"⫸ Successfully removed character `{character_id}` from user `{receiver_id}`"
        except Exception as e:
            print(f"Error updating user: {e}")
            raise
    else:
        raise ValueError("Character not found.")

@app.on_message(filters.command(["kill"]) & filters.reply & filters.user(DEV_LIST))
async def remove_character_command(client, message):
    if not message.reply_to_message:
        await message.reply_text("You need to reply to a message to remove a character!")
        return

    try:
        character_id = str(message.text.split()[1])
        receiver_id = message.reply_to_message.from_user.id
        result_message = await kill_character(receiver_id, character_id)
        await message.reply_text(result_message)
    except (IndexError, ValueError) as e:
        await message.reply_text(str(e))
    except Exception as e:
        print(f"Error in remove_character_command: {e}")
        await message.reply_text("An error occurred while processing the command.")
