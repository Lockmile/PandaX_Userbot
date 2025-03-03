

import re
from datetime import datetime

from telethon import Button, functions
from telethon.events import CallbackQuery
from telethon.utils import get_display_name

from ... import pandaub, SqL, tgbot
import logging

from ...Var import Config
from . import edit_delete, edit_or_reply
from ...helpers.utils import _format, get_user_from_event, reply_id
from ...sql_helper import global_collectionjson as sql
from ...sql_helper import global_list as sqllist
from ...sql_helper import pmpermit_sql
from . import mention

plugin_category = "plugins"
LOGS = logging.getLogger(__name__)
cmdhd = Config.COMMAND_HAND_LER

gvarstatus = SqL.getdb
addgvar = SqL.setdb
delgvar = SqL.deldb




async def do_pm_permit_action(event, chat):  # sourcery no-metrics
    reply_to_id = await reply_id(event)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    me = await event.client.get_me()
    mention = f"[{chat.first_name}](tg://user?id={chat.id})"
    my_mention = f"[{me.first_name}](tg://user?id={me.id})"
    first = chat.first_name
    last = chat.last_name
    fullname = f"{first} {last}" if last else first
    username = f"@{chat.username}" if chat.username else mention
    userid = chat.id
    my_first = me.first_name
    my_last = me.last_name
    my_fullname = f"{my_first} {my_last}" if my_last else my_first
    my_username = f"@{me.username}" if me.username else my_mention
    if str(chat.id) not in PM_WARNS:
        PM_WARNS[str(chat.id)] = 0
    totalwarns = Config.MAX_FLOOD_IN_PMS + 1
    warns = PM_WARNS[str(chat.id)] + 1
    remwarns = totalwarns - warns
    if PM_WARNS[str(chat.id)] >= Config.MAX_FLOOD_IN_PMS:
        try:
            if str(chat.id) in PMMESSAGE_CACHE:
                await event.client.delete_messages(
                    chat.id, PMMESSAGE_CACHE[str(chat.id)]
                )
                del PMMESSAGE_CACHE[str(chat.id)]
        except Exception as e:
            LOGS.info(str(e))
        custompmblock = gvarstatus("pmblock") or None
        if custompmblock is not None:
            USER_BOT_WARN_ZERO = custompmblock.format(
                mention=mention,
                first=first,
                last=last,
                fullname=fullname,
                username=username,
                userid=userid,
                my_first=my_first,
                my_last=my_last,
                my_fullname=my_fullname,
                my_username=my_username,
                my_mention=my_mention,
                totalwarns=totalwarns,
                warns=warns,
                remwarns=remwarns,
            )
        else:
            USER_BOT_WARN_ZERO = f"**Kamu melakukan spam disini ** {my_mention}**'Maaf jika terblock otomatis saya asistance bot penjaga room chat ini.**"
        msg = await event.reply(USER_BOT_WARN_ZERO)
        await event.client(functions.contacts.BlockRequest(chat.id))
        the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Message Count:** {PM_WARNS[str(chat.id)]}"
        del PM_WARNS[str(chat.id)]
        sql.del_collection("pmwarns")
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmwarns", PM_WARNS, {})
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
        try:
            return await event.client.send_message(
                BOTLOG_CHATID,
                the_message,
            )
        except BaseException:
            return
    custompmpermit = gvarstatus("pmpermit_txt") or None
    if custompmpermit is not None:
        USER_BOT_NO_WARN = custompmpermit.format(
            mention=mention,
            first=first,
            last=last,
            fullname=fullname,
            username=username,
            userid=userid,
            my_first=my_first,
            my_last=my_last,
            my_fullname=my_fullname,
            my_username=my_username,
            my_mention=my_mention,
            totalwarns=totalwarns,
            warns=warns,
            remwarns=remwarns,
        )
    else:
        USER_BOT_NO_WARN = """
╔════════════════════╗
 ✅ 𝗡𝗢 𝗦𝗣𝗔𝗠 𝗣𝗟𝗘𝗔𝗦𝗘 ✅
╚════════════════════╝
• Saya belum menyetujui anda untuk PM.
• Tunggu sampai saya menyetujui PM anda.
• Jangan Spam Chat atau anda akan otomatis diblokir.
╔════════════════════╗
 𝗣𝗲𝘀𝗮𝗻 𝗢𝘁𝗼𝗺𝗮𝘁𝗶𝘀 𝗕𝘆 -𝗨𝘀𝗲𝗿𝗕𝗼𝘁
╚════════════════════╝"""
    addgvar("pmpermit_text", USER_BOT_NO_WARN)
    PM_WARNS[str(chat.id)] += 1
    try:
        results = await event.client.inline_query(Config.TG_BOT_USERNAME, "pmpermit")
        msg = await results[0].click(chat.id, reply_to=reply_to_id, hide_via=True)
    except Exception as e:
        LOGS.error(e)
        msg = await event.reply(USER_BOT_NO_WARN)
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    PMMESSAGE_CACHE[str(chat.id)] = msg.id
    sql.del_collection("pmwarns")
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmwarns", PM_WARNS, {})
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})


async def do_pm_options_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = "╔════════════════════╗\n✅ 𝗡𝗢 𝗦𝗣𝗔𝗠 𝗣𝗟𝗘𝗔𝗦𝗘 ✅\n╚════════════════════╝\n• Saya belum menyetujui anda untuk PM.\n• Tunggu sampai saya menyetujui PM anda.\n• Jangan Spam Chat atau anda akan otomatis diblokir.\n╔════════════════════╗\n𝗣𝗲𝘀𝗮𝗻 𝗢𝘁𝗼𝗺𝗮𝘁𝗶𝘀 𝗕𝘆 -𝗨𝘀𝗲𝗿𝗕𝗼𝘁\n╚════════════════════╝\n"
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"**Jika saya ingat dengan benar, saya menyebutkan dalam pesan saya sebelumnya bahwa ini bukan tempat yang tepat bagi Anda untuk melakukan spam. \n Meskipun Anda mengabaikan pesan itu. Jadi, saya hanya memblokir Anda. \n Sekarang Anda tidak dapat melakukan apa pun kecuali tuan saya online dan membuka blokir Anda.**"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Reason:** __He/She didn't opt for any provided options and kept on messaging.__"
    sqllist.rm_from_list("pmoptions", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_enquire_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = f"""╔════════════════════╗
                     ✅ 𝗡𝗢 𝗦𝗣𝗔𝗠 𝗣𝗟𝗘𝗔𝗦𝗘 ✅
                   ╚════════════════════╝
                   • Saya belum menyetujui anda untuk PM.
                   • Tunggu sampai saya menyetujui PM anda.
                   • Jangan Spam Chat atau anda akan otomatis diblokir.
                   ╔════════════════════╗
                    𝗣𝗲𝘀𝗮𝗻 𝗢𝘁𝗼𝗺𝗮𝘁𝗶𝘀 𝗕𝘆 -𝗨𝘀𝗲𝗿𝗕𝗼𝘁
                   ╚════════════════════╝"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"**If I remember correctly I mentioned in my previous message that this is not the right place for you to spam. \
Though you ignored that message. So, I simply blocked you. \
Now you can't do anything unless my master comes online and unblocks you.**"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**Reason:** __He/She opted for enquire option but didn't wait after being told also and kept on messaging so blocked.__"
    sqllist.rm_from_list("pmenquire", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_request_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """__Hei bersabarlah. Tuanku belum melihat pesanmu. \ Tuan saya biasanya menanggapi orang, meskipun saya tidak tahu tentang beberapa pengguna yang luar biasa.__ __Tuan saya akan merespons ketika dia kembali online, jika dia mau.__ **Tolong jangan spam kecuali Anda ingin diblokir dan dilaporkan.**"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"**If I remember correctly I mentioned in my previous message that this is not the right place for you to spam. \
Though you ignored me and messaged me. So, i simply blocked you. \
Now you can't do anything unless my master comes online and unblocks you.**"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**Reason:** __He/She opted for the request option but didn't wait after being told also so blocked.__"
    sqllist.rm_from_list("pmrequest", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_chat_action(event, chat):
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(chat.id) not in PM_WARNS:
        text = """Hei! Saya sedang sibuk sekarang saya sudah meminta Anda untuk menunggu tahu. Setelah pekerjaan saya selesai. Kita bisa bicara tapi tidak benar tahu. Semoga kamu mengerti Tuan saya akan merespons ketika dia kembali online, jika dia mau.**Tolong jangan spam kecuali Anda ingin diblokir dan dilaporkan.**"""
        await event.reply(text)
        PM_WARNS[str(chat.id)] = 1
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
        # await asyncio.sleep(5)
        # await msg.delete()
        return None
    del PM_WARNS[str(chat.id)]
    sql.del_collection("pmwarns")
    sql.add_collection("pmwarns", PM_WARNS, {})
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    USER_BOT_WARN_ZERO = f"""**Jika saya ingat dengan benar saya sebutkan dalam pesan saya sebelumnya ini bukan tempat yang tepat bagi Anda untuk spam. Meskipun Anda mengabaikan pesan itu. Jadi, saya hanya memblokir Anda. Sekarang Anda tidak dapat melakukan apa pun kecuali tuan saya online dan membuka blokir Anda.**"""
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                \n**Reason:** __He/She select opted for the chat option but didn't wait after being told also so blocked.__"
    sqllist.rm_from_list("pmchat", chat.id)
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


async def do_pm_spam_action(event, chat):
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    try:
        if str(chat.id) in PMMESSAGE_CACHE:
            await event.client.delete_messages(chat.id, PMMESSAGE_CACHE[str(chat.id)])
            del PMMESSAGE_CACHE[str(chat.id)]
    except Exception as e:
        LOGS.info(str(e))
    USER_BOT_WARN_ZERO = f"**If I remember correctly I mentioned in my previous message this is not the right place for you to spam. \
Though you ignored that message. So, I simply blocked you. \
Now you can't do anything unless my master comes online and unblocks you.**"
    await event.reply(USER_BOT_WARN_ZERO)
    await event.client(functions.contacts.BlockRequest(chat.id))
    the_message = f"#BLOCKED_PM\
                            \n[{get_display_name(chat)}](tg://user?id={chat.id}) is blocked\
                            \n**Reason:** he opted for spam option and messaged again."
    sqllist.rm_from_list("pmspam", chat.id)
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    try:
        return await event.client.send_message(
            BOTLOG_CHATID,
            the_message,
        )
    except BaseException:
        return


@pandaub.ilhammansiz_cmd(incoming=True, func=lambda e: e.is_private, edited=False)
async def on_new_private_message(event):
    if gvarstatus("pmpermit") is None:
        return
    chat = await event.get_chat()
    if chat.bot or chat.verified:
        return
    if pmpermit_sql.is_approved(chat.id):
        return
    if str(chat.id) in sqllist.get_collection_list("pmspam"):
        return await do_pm_spam_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmchat"):
        return await do_pm_chat_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmrequest"):
        return await do_pm_request_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmenquire"):
        return await do_pm_enquire_action(event, chat)
    if str(chat.id) in sqllist.get_collection_list("pmoptions"):
        return await do_pm_options_action(event, chat)
    await do_pm_permit_action(event, chat)


@pandaub.ilhammansiz_cmd(outgoing=True, func=lambda e: e.is_private, edited=False)
async def you_dm_other(event):
    if gvarstatus("pmpermit") is None:
        return
    chat = await event.get_chat()
    if chat.bot or chat.verified:
        return
    if str(chat.id) in sqllist.get_collection_list("pmspam"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmchat"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmrequest"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmenquire"):
        return
    if str(chat.id) in sqllist.get_collection_list("pmoptions"):
        return
    if event.text and event.text.startswith(
        (
            f"{cmdhd}block",
            f"{cmdhd}disapprove",
            f"{cmdhd}a",
            f"{cmdhd}da",
            f"{cmdhd}approve",
        )
    ):
        return
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    start_date = str(datetime.now().strftime("%B %d, %Y"))
    if not pmpermit_sql.is_approved(chat.id) and str(chat.id) not in PM_WARNS:
        pmpermit_sql.approve(
            chat.id, get_display_name(chat), start_date, chat.username, "For Outgoing"
        )
        try:
            PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
        except AttributeError:
            PMMESSAGE_CACHE = {}
        if str(chat.id) in PMMESSAGE_CACHE:
            try:
                await event.client.delete_messages(
                    chat.id, PMMESSAGE_CACHE[str(chat.id)]
                )
            except Exception as e:
                LOGS.info(str(e))
            del PMMESSAGE_CACHE[str(chat.id)]
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})


@tgbot.on(CallbackQuery(data=re.compile(rb"show_pmpermit_options")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who messages you, not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = f"""Ok, Now you are accessing the availabe menu of my master, {mention}.
__Let's make this smooth and let me know why you are here.__

**Choose one of the following reasons why you are here:**"""
    buttons = [
        (Button.inline(text="To enquire something.", data="to_enquire_something"),),
        (Button.inline(text="To request something.", data="to_request_something"),),
        (Button.inline(text="To chat with my master.", data="to_chat_with_my_master"),),
        (
            Button.inline(
                text="To spam my master's inbox.",
                data="to_spam_my_master_inbox",
            ),
        ),
    ]
    sqllist.add_to_list("pmoptions", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    await event.edit(text, buttons=buttons)


@tgbot.on(CallbackQuery(data=re.compile(rb"to_enquire_something")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit this options for user who messages you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """__Oke. Permintaan Anda telah terdaftar. Jangan spam kotak masuk master saya sekarang. \ Tuan saya sedang sibuk sekarang, Ketika Tuan saya online, dia akan memeriksa pesan Anda dan melakukan ping kepada Anda. \ Kemudian kita dapat memperpanjang percakapan ini tetapi tidak sekarang.__"""
    sqllist.add_to_list("pmenquire", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@tgbot.on(CallbackQuery(data=re.compile(rb"to_request_something")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit this options for user who messages you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """__Oke. Saya telah memberi tahu tuan saya tentang ini. Ketika dia datang online\ atau ketika tuan saya bebas, dia akan melihat ke dalam obrolan ini dan akan melakukan ping kepada Anda sehingga kami dapat mengobrol dengan ramah.__\ ** Tapi sekarang tolong jangan spam kecuali Anda ingin diblokir.**"""
    sqllist.add_to_list("pmrequest", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@tgbot.on(CallbackQuery(data=re.compile(rb"to_chat_with_my_master")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who message you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = """__Yaa tentu kita bisa mengobrol ramah tapi tidak sekarang. kita dapat memiliki ini\ beberapa waktu lain. Saat ini saya sedikit sibuk. ketika saya online dan jika saya bebas. Saya akan ping Anda, ini pasti Damm.__"""
    sqllist.add_to_list("pmchat", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@tgbot.on(CallbackQuery(data=re.compile(rb"to_spam_my_master_inbox")))
async def on_plug_in_callback_query_handler(event):
    if event.query.user_id == event.client.uid:
        text = "Idoit these options are for users who message you. not for you"
        return await event.answer(text, cache_time=0, alert=True)
    text = "`███████▄▄███████████▄\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓█░░░░░░░░░░░░░░█\
         \n▓▓▓▓▓▓███░░░░░░░░░░░░█\
         \n██████▀▀▀█░░░░██████▀ \
         \n░░░░░░░░░█░░░░█\
         \n░░░░░░░░░░█░░░█\
         \n░░░░░░░░░░░█░░█\
         \n░░░░░░░░░░░█░░█\
         \n░░░░░░░░░░░░▀▀`\
         \n**So uncool, this is not your home. Go bother somewhere else.\
         \n\nAnd this is your last warning if you send one more message you will be blocked automatically.**"
    sqllist.add_to_list("pmrequesr", event.query.user_id)
    try:
        PM_WARNS = sql.get_collection("pmspam").json
    except AttributeError:
        PM_WARNS = {}
    if str(event.query.user_id) in PM_WARNS:
        del PM_WARNS[str(event.query.user_id)]
        sql.del_collection("pmwarns")
        sql.add_collection("pmwarns", PM_WARNS, {})
    sqllist.rm_from_list("pmoptions", event.query.user_id)
    await event.edit(text)


@pandaub.ilhammansiz_cmd(
    pattern="pmguard (on|off)$",
    command=("pmguard", plugin_category),
    info={
        "header": "To turn on or turn off pmpermit.",
        "usage": "{tr}pmguard on/off",
    },
)
async def pmpermit_on(event):
    "Turn on/off pmpermit."
    input_str = event.pattern_match.group(1)
    if input_str == "on":
        if gvarstatus("pmpermit") is None:
            addgvar("pmpermit", "true")
            await edit_delete(
                event, " __Permit telah diaktifkan untuk akun Anda dengan sukses__"
            )
        else:
            await edit_delete(
                event, "__Permit telah diaktifkan untuk akun Anda dengan sukses__"
            )
    else:
        if gvarstatus("pmpermit") is not None:
            delgvar("pmpermit")
            await edit_delete(
                event, "__Permit telah dinonaktifkan untuk akun Anda dengan sukses__"
            )
        else:
            await edit_delete(
                event, "__Permit telah dinonaktifkan untuk akun Anda dengan sukses__"
            )


@pandaub.ilhammansiz_cmd(
    pattern="(a|approve)(?: |$)(.*)",
    command=("approve", plugin_category),
    info={
        "header": "Menerima pesan pm.",
        "usage": [
            "{tr}a/approve <username/reply reason> in group",
            "{tr}a/approve <reason> in pm",
        ],
    },
)
async def approve_p_m(event):
    "To approve user to pm"
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(2)
    else:
        user, reason = await get_user_from_event(event, secondgroup=True)
        if not user:
            return
    if not reason:
        reason = "Not mentioned"
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    if not pmpermit_sql.is_approved(user.id):
        if str(user.id) in PM_WARNS:
            del PM_WARNS[str(user.id)]
        start_date = str(datetime.now().strftime("%B %d, %Y"))
        pmpermit_sql.approve(
            user.id, get_display_name(user), start_date, user.username, reason
        )
        chat = user
        if str(chat.id) in sqllist.get_collection_list("pmspam"):
            sqllist.rm_from_list("pmspam", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmchat"):
            sqllist.rm_from_list("pmchat", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmrequest"):
            sqllist.rm_from_list("pmrequest", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmenquire"):
            sqllist.rm_from_list("pmenquire", chat.id)
        if str(chat.id) in sqllist.get_collection_list("pmoptions"):
            sqllist.rm_from_list("pmoptions", chat.id)
        await edit_delete(
            event,
            f"__Menerima pesan pm__ [{user.first_name}](tg://user?id={user.id})\n**Alasan :** __{reason}__",
        )
        try:
            PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
        except AttributeError:
            PMMESSAGE_CACHE = {}
        if str(user.id) in PMMESSAGE_CACHE:
            try:
                await event.client.delete_messages(
                    user.id, PMMESSAGE_CACHE[str(user.id)]
                )
            except Exception as e:
                LOGS.info(str(e))
            del PMMESSAGE_CACHE[str(user.id)]
        sql.del_collection("pmwarns")
        sql.del_collection("pmmessagecache")
        sql.add_collection("pmwarns", PM_WARNS, {})
        sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    else:
        await edit_delete(
            event,
            f"[{user.first_name}](tg://user?id={user.id}) __Ok sekarang kita bisa chatan mau tanya apa?__",
        )


@pandaub.ilhammansiz_cmd(
    pattern="(da|disapprove)(?: |$)(.*)",
    command=("disapprove", plugin_category),
    info={
        "header": "To disapprove user to direct message you.",
        "note": "This command works only for approved users",
        "options": {"all": "To disapprove all approved users"},
        "usage": [
            "{tr}da/disapprove <username/reply> in group",
            "{tr}da/disapprove in pm",
            "{tr}da/disapprove all - To disapprove all users.",
        ],
    },
)
async def disapprove_p_m(event):
    "To disapprove user to direct message you."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(2)

    else:
        reason = event.pattern_match.group(2)
        if reason != "all":
            user, reason = await get_user_from_event(event, secondgroup=True)
            if not user:
                return
    if reason == "all":
        pmpermit_sql.disapprove_all()
        return await edit_delete(
            event, "__Ok! I have disapproved everyone succesfully.__"
        )
    if not reason:
        reason = "Not Mentioned."
    if pmpermit_sql.is_approved(user.id):
        pmpermit_sql.disapprove(user.id)
        await edit_or_reply(
            event,
            f"[{user.first_name}](tg://user?id={user.id}) __is disapproved to personal message me.__\n**Reason:**__ {reason}__",
        )
    else:
        await edit_delete(
            event,
            f"[{user.first_name}](tg://user?id={user.id}) __is not yet approved__",
        )


@pandaub.ilhammansiz_cmd(
    pattern="block(?: |$)(.*)",
    command=("block", plugin_category),
    info={
        "header": "Memblockir pengguna meresahkan.",
        "usage": [
            "{tr}block <username/reply reason> di group",
            "{tr}block <reason> in pm",
        ],
    },
)
async def block_p_m(event):
    "To block user to direct message you."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
        reason = event.pattern_match.group(1)
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
    if not reason:
        reason = "Not Mentioned."
    try:
        PM_WARNS = sql.get_collection("pmwarns").json
    except AttributeError:
        PM_WARNS = {}
    try:
        PMMESSAGE_CACHE = sql.get_collection("pmmessagecache").json
    except AttributeError:
        PMMESSAGE_CACHE = {}
    if str(user.id) in PM_WARNS:
        del PM_WARNS[str(user.id)]
    if str(user.id) in PMMESSAGE_CACHE:
        try:
            await event.client.delete_messages(user.id, PMMESSAGE_CACHE[str(user.id)])
        except Exception as e:
            LOGS.info(str(e))
        del PMMESSAGE_CACHE[str(user.id)]
    if pmpermit_sql.is_approved(user.id):
        pmpermit_sql.disapprove(user.id)
    sql.del_collection("pmwarns")
    sql.del_collection("pmmessagecache")
    sql.add_collection("pmwarns", PM_WARNS, {})
    sql.add_collection("pmmessagecache", PMMESSAGE_CACHE, {})
    await event.client(functions.contacts.BlockRequest(user.id))
    await edit_delete(
        event,
        f"[{user.first_name}](tg://user?id={user.id}) __Berhasil memblok pesan kamu.__\n**Alasan:** __{reason}__",
    )


@pandaub.ilhammansiz_cmd(
    pattern="unblock(?: |$)(.*)",
    command=("unblock", plugin_category),
    info={
        "header": "Membuka block .",
        "usage": [
            "{tr}unblock <username/reply reason> di group",
            "{tr}unblock <reason> in pm",
        ],
    },
)
async def unblock_pm(event):
    "To unblock a user."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __for working of this plugin__",
        )
    if event.is_private:
        user = await event.get_chat()
    else:
        user, reason = await get_user_from_event(event)
        if not user:
            return
    if not reason:
        reason = "Not Mentioned."
    await event.client(functions.contacts.UnblockRequest(user.id))
    await event.edit(
        f"[{user.first_name}](tg://user?id={user.id}) __Membuka pesan blokir anda .__\n**Alasan:** __{reason}__"
    )


@pandaub.ilhammansiz_cmd(
    pattern="listapproved$",
    command=("listapproved", plugin_category),
    info={
        "header": "To see list of approved users.",
        "usage": [
            "{tr}listapproved",
        ],
    },
)
async def approve_p_m(event):
    "To see list of approved users."
    if gvarstatus("pmpermit") is None:
        return await edit_delete(
            event,
            f"__Turn on pmpermit by doing __`{cmdhd}pmguard on` __to work this plugin__",
        )
    approved_users = pmpermit_sql.get_all_approved()
    APPROVED_PMs = "**Current Approved PMs**\n\n"
    if len(approved_users) > 0:
        for user in approved_users:
            APPROVED_PMs += f"• 🐼 {_format.mentionuser(user.first_name , user.user_id)}\n**ID:** `{user.user_id}`\n**UserName:** @{user.username}\n**Date: **__{user.date}__\n**Reason: **__{user.reason}__\n\n"
    else:
        APPROVED_PMs = "`You haven't approved anyone yet`"
    await edit_or_reply(
        event,
        APPROVED_PMs,
        file_name="approvedpms.txt",
        caption="`Current Approved PMs`",
    )
