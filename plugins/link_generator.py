from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id

# Store banned users
banned_users = set()

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('ban'))
async def ban_user(client: Client, message: Message):
    try:
        reply = message.reply_to_message
        if not reply:
            await message.reply("Reply to the user's message to ban them.", quote=True)
            return

        banned_user_id = reply.from_user.id
        if banned_user_id in ADMINS:
            await message.reply("You cannot ban an admin.", quote=True)
            return

        banned_users.add(banned_user_id)
        await message.reply(f"User {banned_user_id} has been banned successfully.", quote=True)
    except Exception as e:
        await message.reply(f"Error: {e}", quote=True)

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('unban'))
async def unban_user(client: Client, message: Message):
    try:
        reply = message.reply_to_message
        if not reply:
            await message.reply("Reply to the user's message to unban them.", quote=True)
            return

        banned_user_id = reply.from_user.id
        if banned_user_id in banned_users:
            banned_users.remove(banned_user_id)
            await message.reply(f"User {banned_user_id} has been unbanned successfully.", quote=True)
        else:
            await message.reply("This user is not banned.", quote=True)
    except Exception as e:
        await message.reply(f"Error: {e}", quote=True)

@Bot.on_message(filters.private & ~filters.user(ADMINS))
async def check_ban(client: Client, message: Message):
    if message.from_user.id in banned_users:
        await message.reply("You are banned from using this bot.", quote=True)
        return

    # Handle normal commands/messages for non-banned users
    await message.reply("You are allowed to use this bot.", quote=True)

# Existing commands like 'batch' and 'genlink' should include a check for banned users
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    if message.from_user.id in banned_users:
        await message.reply("You are banned from using this bot.", quote=True)
        return

    while True:
        try:
            first_message = await client.ask(
                text="Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply(
                "❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel",
                quote=True,
            )
            continue

    while True:
        try:
            second_message = await client.ask(
                text="Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
            )
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply(
                "❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel",
                quote=True,
            )
            continue

    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔁 Share URL", url=f"https://telegram.me/share/url?url={link}")]]
    )
    await second_message.reply_text(
        f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup
    )
    
