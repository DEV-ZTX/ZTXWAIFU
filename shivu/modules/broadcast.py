#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
# For Waifu/Husbando telegram bots.
# Updated and Added new commands, features and style by https://github.com/lovetheticx
#▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

# <============================================ IMPORTS =======================================================>

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler 
from shivu import application, top_global_groups_collection, pm_users, OWNER_ID 

# <====================================== BROADCAST FUNCTION ==================================================>

async def broadcast(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != 7757912959: # Add your own user id here
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text("Please reply to a message to broadcast.")
        return

    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await pm_users.distinct("_id")

    shuyaa = list(set(all_chats + all_users))

    failed_sends = 0
    successful_sends = 0

    for chat_id in shuyaa:
        try:
            await context.bot.forward_message(chat_id=chat_id,
                                              from_chat_id=message_to_broadcast.chat_id,
                                              message_id=message_to_broadcast.message_id)
            successful_sends += 1
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1

    await update.message.reply_text(f"Broadcast complete. Successful sends: {successful_sends}. Failed to send to {failed_sends} chats/users.")


# <============================================ HANDLER =======================================================>

application.add_handler(CommandHandler("broadcast", broadcast, block=False))

# by https://github.com/lovetheticx
