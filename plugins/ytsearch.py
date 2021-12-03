from pyrogram import Client as app, filters
from pyrogram.types import Message
from youtube_search import YoutubeSearch


@app.on_message(filters.command(["search"]))
async def ytsearch(_, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("/search (masukan judul lagu)!")
            return
        query = message.text.split(None, 1)[1]
        m = await message.reply_text("🔎 Mencari Lagu...")
        results = YoutubeSearch(query, max_results=5).to_dict()
        text = ""
        for i in range(5):
            text += f"Judul : {results[i]['title']}\n"
            text += f"Durasi : {results[i]['duration']}\n"
            text += f"Views : {results[i]['views']}\n"
            text += f"Channel : {results[i]['channel']}\n"
            text += f"https://youtube.com{results[i]['url_suffix']}\n\n"
            text += f"─────────────────────────────\n"
        await m.edit(text, disable_web_page_preview=True)
    except Exception as e:
        await message.reply_text(str(e))
