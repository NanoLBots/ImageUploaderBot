import logging
import os
import uvloop

from imagehost.aio import ImageHost
from imagehost.exceptions import ApiError
from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
uvloop.install()

mime_types_allowed = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp',
    'image/svg+xml'
]
max_size_allowed = 10_485_760

bot = Client(
    name='imageuploadbot',
    api_id=int(os.getenv('API_ID')),
    api_hash=os.getenv('API_HASH'),
    bot_token=os.getenv('BOT_TOKEN'),
    parse_mode=ParseMode.MARKDOWN
)
imageup = ImageHost(
    api_key=os.getenv('API_KEY')
)


@bot.on_message(filters.new_chat_members)
async def new_members(cl: Client, m: Message):
    if cl.me.id in [x.id for x in m.new_chat_members]:
        await m.reply(
            '🤖 __**Thanks for adding me to your group, if you need help check the `/help` command.**__'
        )


@bot.on_message(filters.command('start') & filters.private)
async def start_cmd(cl: Client, m: Message):
    await m.reply(
        f"👋 Hello {m.from_user.mention} I'm a bot that can **turn your images into links**, **maximum 10 MB** (__so "
        'that the telegram preview works__) I also support groups.\n\n__Created By @samuel_ks__',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        '➕ Add me to a group',
                        url=f'https://t.me/{cl.me.username}?startgroup'
                    )
                ]
            ]
        )
    )


@bot.on_message(filters.command('help'))
async def help_cmd(_, m: Message):
    await m.reply(
        "**Need Help?**\n\n__It's simple to use me, in private, just send me a photo or photo file and I'll get back "
        'to you with your link.\n\nUsing me in groups is very simple too, reply to a message that contains an image or '
        'image file with the command "`/link`" and I will return your link.__'
    )


@bot.on_message(filters.private & (filters.photo | filters.document))
@bot.on_message(filters.group & filters.reply & filters.command('link'))
async def send_image_link(_, m: Message):
    if m.reply_to_message:
        m = m.reply_to_message
    if m.document:
        if m.document.mime_type not in mime_types_allowed:
            await m.reply('**This file type is not supported.**')
            return
        file_size = m.document.file_size
    else:
        file_size = m.photo.file_size
    if file_size > max_size_allowed:
        await m.reply('**The file size exceeds 10MB** (__understand that this is necessary for the Telegram '
                      'preview to be preserved__).')
        return
    progress = await m.reply('⬇️ **Downloading your image...**')
    path = await m.download()
    await progress.edit('⬆️ **Uploading your image...**')
    try:
        image = await imageup.upload(path)
        os.remove(path)
        await progress.edit(image['image']['url'])
    except ApiError as e:
        await progress.edit(
            f'**An error has occurred and your image cannot be uploaded:\n\n**||`{e.message}`||'
        )
        if os.path.exists(path):
            os.remove(path)


@bot.on_message(filters.command('repo'))
async def send_repo(_, m: Message):
    await m.reply('https://github.com/samuelmarc/ImageUploaderBot')


async def main():
    await bot.start()
    logging.warning('📸 Bot Started!')
    await idle()
    await bot.stop()
    logging.warning('🔌 Bot Stopped.')


bot.run(main())
