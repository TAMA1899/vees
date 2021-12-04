
import os
from os import path
from typing import Callable
from pyrogram import Client, filters
from pyrogram.types import Message, Voice, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserAlreadyParticipant
from Client import callsmusic, queues
from Client.callsmusic import client as USER
from helpers.admins import get_administrators
import requests
import aiohttp
import yt_dlp
from youtube_search import YoutubeSearch
import converter
from youtube import youtube
from config import DURATION_LIMIT, que, SUDO_USERS, UPDATES_CHANNEL
from cache.admins import admins as a
from helpers.filters import command
from helpers.decorators import errors, authorized_users_only
from helpers.errors import DurationLimitError
from helpers.gets import get_url, get_file_name
from helpers.channelmusic import get_chat_id
import aiofiles
import ffmpeg
from PIL import Image, ImageFont, ImageDraw
from pytgcalls import StreamType
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream

import asyncio
from helpers.fsub import handle_force_subscribe
from pyrogram.errors import FloodWait, UserNotParticipant

# plus
chat_id = None
DISABLED_GROUPS = []
useer = "NaN"
ACTV_CALLS = []


def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes or cb.from_user.id in SUDO_USERS:
            return await func(client, cb)
        await cb.answer("You ain't allowed!", show_alert=True)
        return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((190, 550), f"Title: {title}", (255, 255, 255), font=font)
    draw.text((190, 590), f"Duration: {duration}", (255, 255, 255), font=font)
    draw.text((190, 630), f"Views: {views}", (255, 255, 255), font=font)
    draw.text(
        (190, 670),
        f"Added By: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")
    
@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if UPDATES_CHANNEL:
      fsub = await handle_force_subscribe(client, message)
      if fsub == 400:
        return 
    if message.chat.id in DISABLED_GROUPS:
        return    
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("__Tidak Ada Playlist__")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "__Lagu Yang Sedang dimainkan__ di {}".format(message.chat.title)
    msg += "\n\nJudul : " + now_playing
    msg += "\nRequest Dari :" + by
    temp.pop(0)
    if temp:
        msg += "\n────────────────────────────"
        msg += "\n__Antrian Lagu :__"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n\nJudul : {name}"
            msg += f"\nRequest Dari : {usr}\n"
    await message.reply_text(msg)
    

@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("_Sedang tidak Memutar lagu__")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "__Lagu Yang Sedang dimainkan__ di {}".format(cb.message.chat.title)
        msg += "\n\nJudul : " + now_playing
        msg += "\nRequest Dari" + by
        temp.pop(0)
        if temp:
            msg += "\n────────────────────────────"
            msg += "\n__Antrian Lagu__"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n\nJudul : {name}"
                msg += f"\nRequest Dari : {usr}\n"
        await cb.message.edit(msg) 
    


@Client.on_message(
    command("mt") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "I only recognize `/mt on` and `/mt off`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status in ["OFF", "Off", "off"]:
        lel = await message.reply("Processing...")
        if message.chat.id not in DISABLED_GROUPS:
            await lel.edit("This Chat is not In maintainence mode")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"Maintainence Mode disabled In **{message.chat.title}** Chat"
        )

    elif status in ["ON", "On", "on"]:
        lel = await message.reply("Processing...")

        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("maintainence mode  already active in This Chat")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"Maintainence mode is now enabled in **{message.chat.title}** Chat"
        )
    else:
        await message.reply_text(
            "I only recognize `/mt on` and `/mt off`"
        )


@Client.on_callback_query(filters.regex(pattern=r"^(cls)$"))
@cb_admin_check
@authorized_users_only
async def m_cb(b, cb):
    global que
    qeue = que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    chat_id = cb.message.chat.id
    m_chat = cb.message.chat

    if type_ == "cls":
        await cb.answer("Closed menu")
        await cb.message.delete()


# play
@Client.on_message(
    command("play")
    & filters.group
    & ~filters.edited
    & ~filters.forwarded
    & ~filters.via_bot
)
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return    
    if UPDATES_CHANNEL:
      fsub = await handle_force_subscribe(_, message)
      if fsub == 400:
        return
    lel = await message.reply("🔄 **Tunggu**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "Alexa"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>Ingatlah untuk menambahkan {user.first_name} ke Channel Anda</b>",
                    )
                    pass
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "⚠️ __Jadikan Bot sebagai Admin dulu__",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "I joined this group for playing music in VC"
                    )
                    await lel.edit(
                        "__helper userbot joined your chat__",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🔴 Flood Wait Error 🔴 \nUser {user.first_name} couldn't join your group due to heavy requests for userbot! Make sure user is not banned in group."
                        "\n\nOr manually add assistant to your Group and try again</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"__Tambahkan Assisten Manual__ : @alexassisten"
        )
        return
    text_links=None
    await lel.edit("🔎 **Mencari Lagu**")
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ **Lagu dengan durasi lebih dari** `{DURATION_LIMIT}` **menit. Tidak Diizinkan!**"
            )
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/robotprojectx"),
                    InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/ppfffttt"),
                ],
                [InlineKeyboardButton(text="❌", callback_data="cls")],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/8ac47b3c81b8427f1979d.jpg"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Locally added"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🎵 **Music Sedang Diproses**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:25]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "❁ <b>Lagu</b> tidak ditemukan.\n❁ Ketik /play (judul lagu).\n❁ Ketik /search (judul lagu)."
            )
            print(str(e))
            return
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/pejuangairdrops"),
                    InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/ppfffttt"),
                ],
                [InlineKeyboardButton(text="❌", callback_data="cls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("🎵 **Music Sedang Diproses**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        
        try:
          results = YoutubeSearch(query, max_results=6).to_dict()
        except:
          await lel.edit("**Ketik /play Judul Lagu**")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "__Silahkan Pilih lagu yang ingin Anda Putar:__\n\n"
            j = 0
            useer=user_name
            emojilist = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣"]

            while j < 6:
                toxxt += f"{emojilist[j]} [{results[j]['title']}](https://youtube.com{results[j]['url_suffix']})\n"
                toxxt += f" ├ **Durasi** : {results[j]['duration']}\n"
                toxxt += f" ├ **Views** : {results[j]['views']}\n\n"

                j += 1            
            koyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2️⃣", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3️⃣", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5️⃣", callback_data=f'plll 4|{query}|{user_id}'),
                        InlineKeyboardButton("6️⃣", callback_data=f'plll 5|{query}|{user_id}'),
                    ],
                    [InlineKeyboardButton(text="❌", callback_data="cls")],
                ]
            )          
            await lel.edit(toxxt,reply_markup=koyboard,disable_web_page_preview=True)
            # WHY PEOPLE ALWAYS LOVE PORN ?? (A point to think)
            return
            # Returning to pornhub
        except:
            await lel.edit("__Tidak ada hasil yang cukup untuk dipilih.. Mulai bermain langsung...__")
                        
            # print(results)
            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:25]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"thumb{title}.jpg"
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]

            except Exception as e:
                await lel.edit(
                    "❁ <b>Music</b> tidak ditemukan.\n❁ Ketik /play (judul lagu).\n❁ Ketik /search (judul lagu)."
                )
                print(str(e))
                return
            dlurl=url
            dlurl=dlurl.replace("youtube","youtubepp")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                    InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/pejuangairdrops"),
                    InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/ppfffttt"),
                ],
                    [InlineKeyboardButton(text="❌", callback_data="cls")],
                ]
            )
            requested_by = message.from_user.first_name
            await generate_cover(requested_by, title, views, duration, thumbnail)
            file_path = await convert(youtube.download(url))   
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption = f"📋 **Judul :** [{title}]({url}) \n#️⃣ **Antrian** : {position}",
                   reply_markup=keyboard)
       
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            message.reply("__Voice Chat Group tidak aktif, Saya tidak dapat bergabung__")
            return
        await message.reply_photo(
            photo="final.png",
            caption = f"📋 **Judul :** [{title[:60]}]({url})\n⏱️ **Durasi :** {duration}\n" \
                    + f"👤 **Request Dari :** {message.from_user.mention}",
                   reply_markup=keyboard)

    os.remove("final.png")
    return await lel.delete()


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que

    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    #useer_id = cb.message.reply_to_message.from_user.id
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("__Lagu Tidak ditemukan__")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("❌ Bukan Kamu Yang Mencari Lagu!", show_alert=True)
        return
    await cb.message.edit("🎵 **Music Sedang Diproses**")
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name
    
    results = YoutubeSearch(query, max_results=5).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"][:25]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://youtube.com{resultss}"
    
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"❌ Lagu lebih lama dari {DURATION_LIMIT} menit. Tidak Diizinkan!")
            return
    except:
        pass
    try:
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
            [
            [
                    InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇ", url="https://t.me/pejuangairdrops"),
                    InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/ppfffttt"),
            ],
                    [InlineKeyboardButton("❌", callback_data="cls")],
            ]
        )
    requested_by = useer_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await converter.convert(youtube.download(url))  
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS.append(int(x.chat_id))
    if int(chat_id) in ACTV_CALLS:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption = f"📋 **Judul :** [{title[:60]}]({url})\n⏱️ **Durasi** : {duration}\n#️⃣ **Antrian** : {position}", 
                   reply_markup=keyboard,
        )
        os.remove("final.png")
        
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        
        await callsmusic.pytgcalls.join_group_call(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        file_path,
                    ),
                ),
                stream_type=StreamType().local_stream,
            ) 
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption = f"📋 **Judul :** [{title[:60]}]({url})\n⏱ **Durasi :** {duration}\n" \
                    + f"👤 **Request Dari :** {r_by.mention}",
                    reply_markup=keyboard,
        )
        os.remove("final.png")

# Have u read all. If read RESPECT :-)
