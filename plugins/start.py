from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_NAME as bn
from helpers.filters import other_filters2
from time import time
from datetime import datetime
from helpers.decorators import authorized_users_only
from config import BOT_USERNAME, ASSISTANT_USERNAME

START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60 ** 2 * 24),
    ("hour", 60 ** 2),
    ("min", 60),
    ("sec", 1),
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return "inf"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append("{} {}{}".format(amount, unit, "" if amount == 1 else "s"))
    return ", ".join(parts)


@Client.on_message(other_filters2)
async def start(_, message: Message):
        await message.reply_text(
        f"""<b>Hello Friend, {message.from_user.first_name} 👏
Saya Alexa, Saya akan membantumu memutar music di Voice Chat Telegram Groups & Channel, dengan fitur-fitur yang menarik.
\n❗Ketik /help untuk melihat panduan pemakaiannya
❗Ketik /start untuk memuat ulang.
\n───────────────────────────────────
\n__Semua orang pasti mati, tapi tidak semua orang dapat memberi arti. Pastikan hidupmu berarti/bermanfaat untuk orang lain__.
\n───────────────────────────────────
\n❃ Manage by :  [OWNER](https://t.me/pfffttt)  
❃ Support dengan doa aja guys! Thanks!
❃ NB : Maaf jika ada kekurangan didalam bot ini
</b>
        """,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(

                        "⁉️ ᴛᴀᴍʙᴀʜᴋᴀɴ ᴋᴇ ɢʀᴜʙ ⁉️", url=f"https://t.me/alexagroup_bot?startgroup=true")
                ],
                [
                    InlineKeyboardButton(

                        "☕ ᴜᴘᴅᴀᴛᴇ", url=f"https://t.me/overthinkingid"), 

                    InlineKeyboardButton(

                        "ᴏᴡɴᴇʀ ☕", url=f"https://t.me/ppfffttt")
                ],
                [
                    InlineKeyboardButton(
                        "✍️ ᴅᴀꜰᴛᴀʀ ᴘᴇʀɪɴᴛᴀʜ ✍️", url="https://telegra.ph/ROBOT-04-23-2"
                    )
                ]
            ]
        ),
     disable_web_page_preview=True
    )
