import os
import logging
import random
import datetime
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import httpx

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY bulunamadı.")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN bulunamadı.")

logging.basicConfig(level=logging.INFO)
USER_HISTORY = {}
USER_STATS = {}
USER_LANG_PREF = {}
USER_TODOS = {}
JOKES = [
    "Geçen gün fırına gittim, ekmek küsmüş: 'Beni koy, koy, dedim koydum gelmedi.'",
    "Bilgisayarım öksürdü, virüs sandım, meğer tozmuş.",
    "Matematik sorusu: 'Neden ıspanak sevmezsiniz?' Cevap: 'Kara sevdaya tutulmuşum da ondan.'",
]
QUOTES = [
    "Başarı, hazırlık ile fırsatın buluştuğu yerdir. – Seneca",
    "Yapabileceğini düşün, yapabileceğini yap. – Goethe",
    "Her büyük hayal, yürek gerektirir. – Walt Disney",
]
FACTS = [
    "Bir karınca kendi ağırlığının 50 katını taşıyabilir.",
    "Dünya yüzeyinin %71’i sudur.",
    "Venüs, Güneş Sistemi'nde saat yönünde dönen tek gezegendir.",
]
http_client = httpx.AsyncClient(timeout=15.0)

def detect_language(text: str) -> str:
    try:
        code = detect(text)
        return "tr" if code == "tr" else "en"
    except LangDetectException:
        return "en"

def get_system_prompt(lang_code: str) -> str:
    return "Sen yardımcı bir asistansın. Kullanıcının dilinde yanıt ver." if lang_code == "tr" \
        else "You are a helpful assistant. Reply in the user's language."

def add_to_history(user_id: int, role: str, content: str):
    history = USER_HISTORY.setdefault(user_id, [])
    history.append({"role": role, "content": content})
    if len(history) > 6:
        del history[0]

def increment_stat(user_id: int):
    USER_STATS[user_id] = USER_STATS.get(user_id, 0) + 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = update.effective_user.language_code or "en"
    USER_LANG_PREF[user_id] = "tr" if lang.startswith("tr") else "en"
    text = "👋 Merhaba! AskzenBot'a hoş geldin. Komut listesi için /help yazabilirsin." \
        if USER_LANG_PREF[user_id] == "tr" \
        else "👋 Hello! Welcome to AskzenBot. Type /help for commands."
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = USER_LANG_PREF.get(user_id, "en")
    if lang == "tr":
        text = (
            "/help - Komut listesi\n"
            "/lang <tr|en> - Dil tercihini değiştir\n"
            "/reset - Sohbet geçmişini temizle\n"
            "/stats - İstek istatistiklerini göster\n"
            "/joke - Rastgele şaka\n"
            "/quote - Rastgele alıntı\n"
            "/fact - Rastgele bilgi\n"
            "/translate <hedef_dil> <metin> - Metni çevir\n"
            "/summary <metin> - Metni özetle\n"
            "/define <kelime> - Kelime tanımı yap\n"
            "/todo_add <madde> - Yapılacak ekle\n"
            "/todo_list - Yapılacak liste\n"
            "/todo_clear - Yapılacak temizle\n"
            "/ping - Gecikmeyi ölç\n"
            "/time - Mevcut zamanı göster\n"
            "/roll <sayi> - 1 ila sayı arasında rastgele sayı\n"
            "/flip - Yazı-tura at\n"
            "/calc <ifade> - Matematik hesaplama\n"
            "/echo <metin> - Yazılanı tekrar yazar\n"
            "/about - Bot hakkında bilgi\n"
            "/user - Kullanıcı bilgilerini göster\n"
            "/random <min> <max> - Rastgele sayı üret\n"
            "/poem <konu> - Konuya şiir oluştur\n"
            "/story <konu> - Konuya hikaye oluştur\n"
        )
    else:
        text = (
            "/help - Show commands\n"
            "/lang <tr|en> - Change language\n"
            "/reset - Clear history\n"
            "/stats - Show usage stats\n"
            "/joke - Get random joke\n"
            "/quote - Get random quote\n"
            "/fact - Get random fact\n"
            "/translate <target_lang> <text> - Translate text\n"
            "/summary <text> - Summarize text\n"
            "/define <word> - Define a word\n"
            "/todo_add <item> - Add to to-do list\n"
            "/todo_list - Show to-do list\n"
            "/todo_clear - Clear to-do list\n"
            "/ping - Measure latency\n"
            "/time - Show current time\n"
            "/roll <number> - Roll a number\n"
            "/flip - Flip a coin\n"
            "/calc <expression> - Math calculate\n"
            "/echo <text> - Echo text\n"
            "/about - About this bot\n"
            "/user - Show user info\n"
            "/random <min> <max> - Generate random number\n"
            "/poem <topic> - Create poem\n"
            "/story <topic> - Create story\n"
        )
    await update.message.reply_text(text)

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if args and args[0].lower() in ("tr", "en"):
        USER_LANG_PREF[user_id] = args[0].lower()
        msg = "Dil tercihin Türkçe olarak ayarlandı." if args[0].lower()=="tr" else "Language set to English."
        await update.message.reply_text(msg)
    else:
        lang = USER_LANG_PREF.get(user_id,"en")
        err = "Kullanım: /lang <tr|en>" if lang=="tr" else "Usage: /lang <tr|en>"
        await update.message.reply_text(err)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_HISTORY[user_id] = []
    lang = USER_LANG_PREF.get(user_id, "en")
    msg = "Sohbet geçmişi temizlendi." if lang=="tr" else "Conversation history cleared."
    await update.message.reply_text(msg)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = USER_STATS.get(user_id, 0)
    lang = USER_LANG_PREF.get(user_id,"en")
    msg = f"Toplam {count} istek gönderdiniz." if lang=="tr" else f"You have sent {count} requests."
    await update.message.reply_text(msg)

async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(JOKES))

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(QUOTES))

async def fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(FACTS))

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    lang = USER_LANG_PREF.get(user_id, "en")
    if len(args) < 2:
        err = "Kullanım: /translate <hedef_dil> <metin>" if lang=="tr" else "Usage: /translate <target_lang> <text>"
        await update.message.reply_text(err)
        return
    target = args[0]
    text_to_translate = " ".join(args[1:])
    system_prompt = f"You are a translator. Translate to {target}."
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role":"system","content":system_prompt},{"role":"user","content":text_to_translate}],
        "max_tokens":256,"temperature":0.2
    }
    headers = {"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"}
    try:
        r = await http_client.post("https://openrouter.ai/api/v1/chat/completions",json=payload,headers=headers)
        data = r.json()
        reply = data["choices"][0]["message"]["content"] if r.status_code==200 else data.get("error",{}).get("message","Hata")
        await update.message.reply_text(reply)
    except Exception:
        err = "❌ Çeviri yapılamadı." if lang=="tr" else "❌ Translation failed."
        await update.message.reply_text(err)

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = " ".join(context.args)
    lang = USER_LANG_PREF.get(user_id,"en")
    if not text:
        err = "Kullanım: /summary <metin>" if lang=="tr" else "Usage: /summary <text>"
        await update.message.reply_text(err)
        return
    system_prompt = "You are a summarizer. Summarize the following text."
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages":[{"role":"system","content":system_prompt},{"role":"user","content":text}],
        "max_tokens":128,"temperature":0.2
    }
    headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"}
    try:
        r=await http_client.post("https://openrouter.ai/api/v1/chat/completions",json=payload,headers=headers)
        data=r.json()
        reply=data["choices"][0]["message"]["content"] if r.status_code==200 else data.get("error",{}).get("message","Hata")
        await update.message.reply_text(reply)
    except Exception:
        err="❌ Özet alınamadı." if lang=="tr" else "❌ Summarization failed."
        await update.message.reply_text(err)

async def define_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    word = " ".join(context.args)
    lang = USER_LANG_PREF.get(user_id,"en")
    if not word:
        err = "Kullanım: /define <kelime>" if lang=="tr" else "Usage: /define <word>"
        await update.message.reply_text(err)
        return
    system_prompt = "You are a dictionary. Provide a clear definition."
    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages":[{"role":"system","content":system_prompt},{"role":"user","content":word}],
        "max_tokens":64,"temperature":0.2
    }
    headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"}
    try:
        r=await http_client.post("https://openrouter.ai/api/v1/chat/completions",json=payload,headers=headers)
        data=r.json()
        reply=data["choices"][0]["message"]["content"] if r.status_code==200 else data.get("error",{}).get("message","Hata")
        await update.message.reply_text(reply)
    except Exception:
        err="❌ Tanım bulunamadı." if lang=="tr" else "❌ Definition failed."
        await update.message.reply_text(err)

async def todo_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    item = " ".join(context.args)
    lang = USER_LANG_PREF.get(user_id,"en")
    if not item:
        err = "Kullanım: /todo_add <madde>" if lang=="tr" else "Usage: /todo_add <item>"
        await update.message.reply_text(err)
        return
    USER_TODOS.setdefault(user_id,[]).append(item)
    msg="Listeye eklendi." if lang=="tr" else "Added to to-do list."
    await update.message.reply_text(msg)

async def todo_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = USER_LANG_PREF.get(user_id,"en")
    todos = USER_TODOS.get(user_id,[])
    if not todos:
        msg="Yapılacak listeniz boş." if lang=="tr" else "Your to-do list is empty."
        await update.message.reply_text(msg)
        return
    text="\n".join(f"{i+1}. {item}" for i,item in enumerate(todos))
    await update.message.reply_text(text)

async def todo_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = USER_LANG_PREF.get(user_id,"en")
    USER_TODOS[user_id]=[]
    msg="Yapılacak liste temizlendi." if lang=="tr" else "To-do list cleared."
    await update.message.reply_text(msg)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time=datetime.datetime.now()
    message=await update.message.reply_text("Pong...")
    latency=(datetime.datetime.now()-start_time).total_seconds()*1000
    await message.edit_text(f"Pong! {int(latency)} ms")

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    lang=USER_LANG_PREF.get(user_id,"en")
    now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg=f"Şu anki zaman: {now}" if lang=="tr" else f"Current time: {now}"
    await update.message.reply_text(msg)

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    lang=USER_LANG_PREF.get(user_id,"en")
    args=context.args
    if not args or not args[0].isdigit():
        err="Kullanım: /roll <sayi>" if lang=="tr" else "Usage: /roll <number>"
        await update.message.reply_text(err)
        return
    n=int(args[0])
    result=random.randint(1, max(1,n))
    await update.message.reply_text(str(result))

async def flip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    lang=USER_LANG_PREF.get(user_id,"en")
    result=random.choice(["Yazı","Tura"]) if lang=="tr" else random.choice(["Heads","Tails"])
    await update.message.reply_text(result)

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    lang=USER_LANG_PREF.get(user_id,"en")
    expr=" ".join(context.args)
    if not expr:
        err="Kullanım: /calc <ifade>" if lang=="tr" else "Usage: /calc <expression>"
        await update.message.reply_text(err)
        return
    try:
        allowed="0123456789+-*/(). "
        if any(ch not in allowed for ch in expr):
            raise ValueError
        result=eval(expr)
        await update.message.reply_text(str(result))
    except Exception:
        err="❌ Geçersiz ifade." if lang=="tr" else "❌ Invalid expression."
        await update.message.reply_text(err)

async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=" ".join(context.args)
    if text:
        await update.message.reply_text(text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    lang=USER_LANG_PREF.get(user_id,"en")
    msg="AskzenBot v1.1 - Ücretsiz OpenRouter AI destekli, hızlı ve çok özellikli bir Telegram botudur." \
        if lang=="tr" \
        else "AskzenBot v1.1 - A fast, multi-feature Telegram bot powered by free OpenRouter AI."
    await update.message.reply_text(msg)

async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user=update.effective_user
    text=f"ID: {user.id}\nAd: {user.full_name}\nKullanıcı adı: @{user.username or 'yok'}"
    await update.message.reply_text(text)

async def random_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    lang=USER_LANG_PREF.get(user_id,"en")
    args=context.args
    if len(args)<2 or not args[0].isdigit() or not args[1].isdigit():
        err="Kullanım: /random <min> <max>" if lang=="tr" else "Usage: /random <min> <max>"
        await update.message.reply_text(err)
        return
    mn, mx=int(args[0]), int(args[1])
    if mn>mx: mn, mx = mx, mn
    await update.message.reply_text(str(random.randint(mn,mx)))

async def poem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    topic=" ".join(context.args)
    lang=USER_LANG_PREF.get(user_id,"en")
    if not topic:
        err="Kullanım: /poem <konu>" if lang=="tr" else "Usage: /poem <topic>"
        await update.message.reply_text(err)
        return
    system_prompt="You are a poet. Write a short poem about the topic."
    payload={"model":"mistralai/mistral-7b-instruct","messages":[{"role":"system","content":system_prompt},{"role":"user","content":topic}],"max_tokens":128,"temperature":0.7}
    headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"}
    try:
        r=await http_client.post("https://openrouter.ai/api/v1/chat/completions",json=payload,headers=headers)
        data=r.json()
        reply=data["choices"][0]["message"]["content"] if r.status_code==200 else data.get("error",{}).get("message","Hata")
        await update.message.reply_text(reply)
    except Exception:
        err="❌ Şiir oluşturulamadı." if lang=="tr" else "❌ Could not generate poem."
        await update.message.reply_text(err)

async def story_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    topic=" ".join(context.args)
    lang=USER_LANG_PREF.get(user_id,"en")
    if not topic:
        err="Kullanım: /story <konu>" if lang=="tr" else "Usage: /story <topic>"
        await update.message.reply_text(err)
        return
    system_prompt="You are a storyteller. Write a short story about the topic."
    payload={"model":"mistralai/mistral-7b-instruct","messages":[{"role":"system","content":system_prompt},{"role":"user","content":topic}],"max_tokens":256,"temperature":0.7}
    headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"}
    try:
        r=await http_client.post("https://openrouter.ai/api/v1/chat/completions",json=payload,headers=headers)
        data=r.json()
        reply=data["choices"][0]["message"]["content"] if r.status_code==200 else data.get("error",{}).get("message","Hata")
        await update.message.reply_text(reply)
    except Exception:
        err="❌ Hikaye oluşturulamadı." if lang=="tr" else "❌ Could not generate story."
        await update.message.reply_text(err)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id=update.effective_user.id
    user_text=update.message.text
    manual_pref=USER_LANG_PREF.get(user_id)
    detected=detect_language(user_text)
    lang=manual_pref or detected
    USER_LANG_PREF[user_id]=lang
    add_to_history(user_id,"user",user_text)
    increment_stat(user_id)
    system_prompt=get_system_prompt(lang)
    payload={"model":"mistralai/mistral-7b-instruct","messages":[{"role":"system","content":system_prompt}] + USER_HISTORY.get(user_id,[]), "max_tokens":128, "temperature":0.6}
    headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"}
    try:
        r=await http_client.post("https://openrouter.ai/api/v1/chat/completions",json=payload,headers=headers)
        data=r.json()
        if r.status_code==200:
            reply=data["choices"][0]["message"]["content"]
        else:
            raise Exception(data.get("error",{}).get("message","Bilinmeyen hata"))
        add_to_history(user_id,"assistant",reply)
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"GPT ERROR: {e}")
        err="❌ GPT yanıtı alınamadı. Lütfen daha sonra tekrar deneyin." if lang=="tr" else "❌ Could not generate a response. Try again later."
        await update.message.reply_text(err)

def main():
    app=ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help",help_command))
    app.add_handler(CommandHandler("lang",lang_command))
    app.add_handler(CommandHandler("reset",reset_command))
    app.add_handler(CommandHandler("stats",stats_command))
    app.add_handler(CommandHandler("joke",joke_command))
    app.add_handler(CommandHandler("quote",quote_command))
    app.add_handler(CommandHandler("fact",fact_command))
    app.add_handler(CommandHandler("translate",translate_command))
    app.add_handler(CommandHandler("summary",summary_command))
    app.add_handler(CommandHandler("define",define_command))
    app.add_handler(CommandHandler("todo_add",todo_add))
    app.add_handler(CommandHandler("todo_list",todo_list))
    app.add_handler(CommandHandler("todo_clear",todo_clear))
    app.add_handler(CommandHandler("ping",ping_command))
    app.add_handler(CommandHandler("time",time_command))
    app.add_handler(CommandHandler("roll",roll_command))
    app.add_handler(CommandHandler("flip",flip_command))
    app.add_handler(CommandHandler("calc",calc_command))
    app.add_handler(CommandHandler("echo",echo_command))
    app.add_handler(CommandHandler("about",about_command))
    app.add_handler(CommandHandler("user",user_command))
    app.add_handler(CommandHandler("random",random_command))
    app.add_handler(CommandHandler("poem",poem_command))
    app.add_handler(CommandHandler("story",story_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))
    app.run_polling()

if __name__=="__main__":
    main()
