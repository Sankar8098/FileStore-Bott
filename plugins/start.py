import os
import asyncio
import humanize
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import subscribed, encode, decode, get_messages
from database.database import add_user, del_user, full_userbase, present_user

# Global Variables
titanxofficials = FILE_AUTO_DELETE
file_auto_delete = humanize.naturaldelta(titanxofficials)
banned_users = set()  # Set to store banned user IDs
ADMIN_USER_ID = [5821871362]  # Replace with actual admin IDs


# Middleware to Block Banned Users
@Bot.on_message(filters.private & ~filters.user(ADMIN_USER_ID))
async def block_banned_users(client: Client, message: Message):
    if message.from_user.id in banned_users:
        await message.reply("You are banned from using this bot.")
        return


# Ban Command
@Bot.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID))
async def ban_user(client, message):
    if len(message.command) < 2:
        await message.reply("Usage: /ban <user_id>")
        return
    try:
        user_id = int(message.command[1])
        banned_users.add(user_id)
        await message.reply(f"User {user_id} has been banned.")
    except ValueError:
        await message.reply("Invalid user ID. Please provide a valid integer.")


# Unban Command
@Bot.on_message(filters.command("unban") & filters.user(ADMIN_USER_ID))
async def unban_user(client, message):
    if len(message.command) < 2:
        await message.reply("Usage: /unban <user_id>")
        return
    try:
        user_id = int(message.command[1])
        banned_users.discard(user_id)
        await message.reply(f"User {user_id} has been unbanned.")
    except ValueError:
        await message.reply("Invalid user ID. Please provide a valid integer.")


# Start Command
@Bot.on_message(filters.command("start") & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    if message.from_user.id in banned_users:
        await message.reply("You are banned from using this bot.")
        return

    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        titanx_msgs = []  # List to keep track of sent messages

        for msg in messages:
            if bool(CUSTOM_CAPTION) and bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name,
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                titanx_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT,
                )
                titanx_msgs.append(titanx_msg)

            except FloodWait as e:
                await asyncio.sleep(e.value)
                titanx_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT,
                )
                titanx_msgs.append(titanx_msg)
            except Exception as e:
                print(f"Error copying message: {e}")
                pass

        k = await client.send_message(
            chat_id=message.from_user.id,
            text=f"<b>❗️ <u>IMPORTANT</u> ❗️</b>\n\nThis Video / File Will Be Deleted In {file_auto_delete} (Due To Copyright Issues).\n\n📌 Please Forward This Video / File To Somewhere Else And Start Downloading There.",
        )

        # Schedule the file deletion
        asyncio.create_task(delete_files(titanx_msgs, client, k))

        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🧠 Help", callback_data="help"),
                    InlineKeyboardButton("🔰 About", callback_data="about"),
                ]
            ]
        )
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id,
            ),
            reply_markup=reply_markup,
        )


# Delete Files
async def delete_files(messages, client, k):
    await asyncio.sleep(FILE_AUTO_DELETE)  # Wait for the duration specified in config.py
    for msg in messages:
        try:
            await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
        except Exception as e:
            print(f"Failed to delete the media {msg.id}: {e}")

    try:
        await k.edit_text("Your Video / File Has Been Deleted ✅")
    except Exception as e:
        print(f"Error editing the message: {e}")

