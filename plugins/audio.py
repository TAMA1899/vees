from os import path

from pyrogram import Client
from pyrogram.types import Message, Voice
from pytgcalls.types.input_stream import InputAudioStream
from Client import callsmusic, queues

import converter
from youtube import youtube

from config import BOT_NAME as bn, DURATION_LIMIT, UPDATES_CHANNEL, AUD_IMG, QUE_IMG, GROUP_SUPPORT
from helpers.filters import command, other_filters
from helpers.decorators import errors
from helpers.errors import DurationLimitError
from helpers.gets import get_url, get_file_name
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ACTV_CALLS = []

@Client.on_message(command("audio") & other_filters)
@errors
async def stream(_, message: Message):
    chat_id = message.chat.id

    lel = await message.reply("🔁 **Mencari Lagu**...")
    sender_id = message.from_user.id
    sender_name = message.from_user.first_name

    keyboard = InlineKeyboardMarkup(
            [
            [
                    InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/pejuangairdrops"),
                    InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/ppfffttt"),
            ],
                    [InlineKeyboardButton("❌", callback_data="cls")],
            ]
        )

    audio = (message.reply_to_message.audio or message.reply_to_message.voice) if message.reply_to_message else None
    url = get_url(message)

    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ Lagu lebih lama dari {DURATION_LIMIT} menit. Tidak Diizinkan!"
            )

        file_name = get_file_name(audio)
        file_path = await converter.convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name)) else file_name
        )
    elif url:
        file_path = await converter.convert(youtube.download(url))
    else:
        return await lel.edit_text("Pfft!")
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))    
    if int(chat_id) in ACTV_CALLS:
        position = await queues.put(chat_id, file=file_path)
        await message.reply_photo(
        photo=f"{QUE_IMG}",
        reply_markup=keyboard,
        caption=f"📋 **Judul :** [{title[:60]}]({url})\n⏱ **Durasi :** {duration}\n⚡ __Powered by Alexa__")
        return await lel.delete()
    else:
        await callsmusic.pytgcalls.join_group_call(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        file_path,
                    ),
                ),
                stream_type=StreamType().local_stream,
            ) 
        costumer = message.from_user.mention
        await message.reply_photo(
        photo=f"{AUD_IMG}",
        reply_markup=keyboard,
        caption=f"📋 **Judul :** [{title[:60]}]({url})\n⚡ __Powered by Alexa__"
        )
        return await lel.delete()
