import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler, CallbackContext
)
from utils import chunk_text, generate_video

# توكن البوت (خاصّ وآمن)
TOKEN = '7285374518:AAH8xiizyg_I9Ih8oet8HePXTxkJ0c-T1zY'

# مراحل المحادثة
(TYPE, ASPECT, QUALITY, FPS, STORY) = range(5)

def keyboard_markup(options):
    return ReplyKeyboardMarkup(options, resize_keyboard=True, one_time_keyboard=True)

# قوائم الأزرار
VIDEO_TYPES   = [["كرتوني", "واقعي"]]
ASPECT_RATIOS = [["9:16", "16:9"], ["1:1", "4:5"]]
QUALITIES     = [["منخفض", "متوسط"], ["عالي", "فائق الدقة"]]
FPS_OPTIONS   = [["12fps", "24fps"], ["30fps"]]

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "أهلاً! اختر نوع الفيديو:",
        reply_markup=keyboard_markup(VIDEO_TYPES)
    )
    return TYPE

def choose_type(update: Update, context: CallbackContext):
    context.user_data['type'] = update.message.text
    update.message.reply_text(
        "حسنًا، اختر القياس:",
        reply_markup=keyboard_markup(ASPECT_RATIOS)
    )
    return ASPECT

def choose_aspect(update: Update, context: CallbackContext):
    context.user_data['aspect'] = update.message.text
    update.message.reply_text(
        "الآن اختر الجودة:",
        reply_markup=keyboard_markup(QUALITIES)
    )
    return QUALITY

def choose_quality(update: Update, context: CallbackContext):
    context.user_data['quality'] = update.message.text
    update.message.reply_text(
        "حدد الإطارات في الثانية:",
        reply_markup=keyboard_markup(FPS_OPTIONS)
    )
    return FPS

def choose_fps(update: Update, context: CallbackContext):
    context.user_data['fps'] = update.message.text
    update.message.reply_text("أرسل الآن القصة الكاملة:")
    return STORY

def receive_story(update: Update, context: CallbackContext):
    story = update.message.text
    prompts = chunk_text(story, max_words=100)
    video_path = generate_video(prompts, context.user_data)
    with open(video_path, 'rb') as vid:
        update.message.reply_video(vid)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("تم الإلغاء. ابدأ من جديد بإرسال /start.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TYPE:    [MessageHandler(Filters.text & ~Filters.command, choose_type)],
            ASPECT:  [MessageHandler(Filters.text & ~Filters.command, choose_aspect)],
            QUALITY: [MessageHandler(Filters.text & ~Filters.command, choose_quality)],
            FPS:     [MessageHandler(Filters.text & ~Filters.command, choose_fps)],
            STORY:   [MessageHandler(Filters.text & ~Filters.command, receive_story)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
