import time
import json
import os
import hashlib
import logging
import threading
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
from functools import wraps
from collections import defaultdict, deque
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ChatPermissions, ChatMemberUpdated, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ChatMemberHandler
from telegram.error import NetworkError, TelegramError
from functools import wraps
import html
from telegram import ParseMode
from colorama import Fore, init
from keep_alive import keep_alive

keep_alive()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
init(autoreset=True)

md5_game_error = False
usage_count = defaultdict(int)
last_reset_time = defaultdict(lambda: time.time())
mailbox = {}
MAILBOX_FILE = "mailbox.json"
CHECKED_USERS_FILE = "checked_users.txt"
auto_messages = []
QUESTS_FILE = 'quests.json'
user_command_times = defaultdict(list)
md5_game_active = True
md5_bets = {}
md5_timer = 0
accepted_quests = {}
TOKEN = '8125944265:AAHwpN15SXbs8NxmkojkcdHouLl03_iuSQo'
TAIXIU_GROUP_ID = -1002500196343
ROOM_CHECK = -1002500196343
ROOM_KQ = -1002500196343
taixiu_game_active = False
taixiu_bets = {}
taixiu_timer = 0
recent_results = []
jackpot_amount = 30000
user_balances = {}
user_bet_times = {user_id: deque() for user_id in user_balances}
MESSAGE_COUNT_FILE = "message_count.json"
MESSAGE_THRESHOLD = 50
admin_id = 7719131045
ADMIN_ID = 7719131045
MENH_GIA = ['10000', '20000', '50000', '100000', '200000', '500000']
CODES_FILE = "code.txt"
PHIEN_FILE = "phien.txt"
RESULTS_FILE = "kqphientx.txt"
BALANCES_FILE = "sodu.txt"
custom_dice_values = {}
user_bet_times = defaultdict(deque)
GROUP_ID_1 = -1002152949507
GROUP_ID_2 = -1002152949507


def retry_on_failure(retries=3, delay=5):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except NetworkError as e:
                    print(f"Xảy ra lỗi mạng: {e}. Thử lại sau {delay} giây...")
                    time.sleep(delay)
                except TelegramError as e:
                    print(f"Xảy ra lỗi Telegram: {e}")
                    break
            return None

        return wrapper

    return decorator


def add_vip_user(update: Update, context: CallbackContext, user_id: int):
    with open("vip.txt", "a") as vip_file:
        vip_file.write(f"{user_id}\n")

    update.message.reply_text(
        f"User {user_id} has been added to the VIP list.")


def calculate_md5(dice1, dice2, dice3):
    random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    result_str = f"XROOM_MD5_( {dice1} - {dice2} - {dice3} )_{random_suffix}"
    md5_hash = hashlib.md5(result_str.encode()).hexdigest()
    return md5_hash, result_str


def add_vip(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        return
    if not update.message:
        return

    try:
        vip_user_id = int(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text("Lệnh ADMIN")
        return

    with open("vip.txt", "a") as vip_file:
        vip_file.write(f"{vip_user_id}\n")

    update.message.reply_text(
        f"Hoàn Thành {user_id}")


def load_vip_users():
    try:
        with open("vip.txt", "r") as vip_file:
            vip_users = {int(line.strip()) for line in vip_file}
    except FileNotFoundError:
        vip_users = set()
    return vip_users


def load_phien_number():
    try:
        with open(PHIEN_FILE, "r") as file:
            phien_number = int(file.read().strip())
    except FileNotFoundError:
        phien_number = 0
    return phien_number


def save_phien_number(phien_number):
    with open(PHIEN_FILE, "w") as file:
        file.write(str(phien_number))


def read_balances():
    if os.path.exists('sodu.txt'):
        with open('sodu.txt', 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    user_id, balance = parts
                    try:
                        user_balances[int(user_id)] = float(balance)
                    except ValueError:
                        print(f"Invalid balance for user {user_id}: {balance}")


def load_user_balances(filename='sodu.txt'):
    user_balances = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                user_id = int(parts[0])
                balance = float(parts[1])
                user_balances[user_id] = balance
            except ValueError:
                continue
    return user_balances


def save_user_balances():
    with open("sodu.txt", "w") as file:
        for user_id, balance in user_balances.items():
            file.write(f"{user_id} {balance}\n")


def format_currency(amount):
    return f"{int(amount):,} ₫"


def update_user_balance(user_id, amount):
    if user_id in user_balances:
        user_balances[user_id] += amount
    else:
        user_balances[user_id] = amount
    save_user_balances()


def load_recent_results():
    global recent_results
    try:
        with open(RESULTS_FILE, "r") as file:
            lines = file.readlines()
            if len(lines) >= 2:
                recent_results = [line.strip() for line in lines]
            else:
                recent_results = [""] * 2
    except FileNotFoundError:
        recent_results = [""] * 2


def save_recent_results():
    global recent_results
    try:
        with open(RESULTS_FILE, "w") as file:
            for result in recent_results:
                file.write(result + "\n")
    except Exception as e:
        print(f"Error saving recent results: {e}")


def format_recent_results():
    global recent_results
    recent_results_slice = recent_results[-10:]
    formatted_results = []

    for result in recent_results_slice:
        formatted_results.append(result)

    return " ".join(formatted_results)


def lock_chat(context, chat_id):
    context.bot.set_chat_permissions(chat_id=chat_id,
                                     permissions=ChatPermissions(
                                         can_send_messages=False,
                                         can_invite_users=True))


def unlock_chat(context, chat_id):
    context.bot.set_chat_permissions(chat_id=chat_id,
                                     permissions=ChatPermissions(
                                         can_send_messages=True,
                                         can_invite_users=True))


def save_game_state(phien_number, taixiu_timer, taixiu_bets):
    total_bet_tai = sum(amount for bets in taixiu_bets.values()
                        for choice, amount in bets if choice == 'T')
    total_bet_xiu = sum(amount for bets in taixiu_bets.values()
                        for choice, amount in bets if choice == 'X')
    with open('cuocphien.txt', 'w') as file:
        file.write(
            f"{phien_number}:{taixiu_timer}:{total_bet_tai}:{total_bet_xiu}")


def load_game_state():
    try:
        with open('cuocphien.txt', 'r') as file:
            data = file.read().strip().split(':')
            if len(data) == 6:
                phien_number = int(data[0])
                taixiu_timer = int(data[1])
                total_bet_tai = int(data[2])
                total_bet_xiu = int(data[3])
                return phien_number, taixiu_timer, total_bet_tai, total_bet_xiu
    except FileNotFoundError:
        return None
    except ValueError:
        return None
    return None


def clear_game_state():
    with open('cuocphien.txt', 'w') as file:
        file.write("")


@retry_on_failure(retries=3, delay=5)
def start_taixiu(update: Update, context: CallbackContext):
    global taixiu_game_active, taixiu_bets, taixiu_timer, recent_results, taixiu_betting_active

    state = load_game_state()
    if state:
        phien_number, taixiu_timer, total_bet_tai, total_bet_xiu = state
    else:
        phien_number = load_phien_number()
        taixiu_timer = 69

    if taixiu_game_active:
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=(
                f"⏳ Phiên {phien_number}. Còn {taixiu_timer}s để đặt cược ⏳\n\n"
                f"✅ Lệnh Cược : T/X dấu cách Cược/Max ✅\n\n"
                f"🔵 Cửa Tài: Tổng tiền {total_bet_tai} ₫\n\n"
                f"🔴 Cửa Xỉu: Tổng tiền {total_bet_xiu} ₫\n\n"
                f"💰 Hũ hiện tại : {format_currency(jackpot_amount)} 💰\n\n"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔵🔴 Xem Cầu ⚫️⚪️",
                                     url='https://t.me/zroomketqua')
            ]]))
        return

    taixiu_betting_active = True
    taixiu_game_active = True
    taixiu_bets = {}
    taixiu_timer = 69
    clear_game_state()

    context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                             text=(f"🎲 Bắt Đầu Nhận Cược 🎲\n\n"
                                   f"📌 Lệnh Cược: <T/X> <Cược/Max>\n\n"
                                   f"⏳ Còn {taixiu_timer}s để đặt cược ⏳\n\n"))

    threading.Thread(target=start_taixiu_timer, args=(update, context)).start()


@retry_on_failure(retries=3, delay=5)
def start_taixiu_timer(update: Update, context: CallbackContext):
    global taixiu_timer, taixiu_betting_active
    while taixiu_timer > 0:
        time.sleep(1)
        taixiu_timer -= 1
        if taixiu_timer % 20 == 0:
            keyboard = [[
                InlineKeyboardButton("🔵🔴 Xem Cầu ⚫️⚪️",
                                     url='https://t.me/zroomketqua')
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            phien_number = load_phien_number()
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=
                (f"⏳ Phiên {phien_number}. Còn {taixiu_timer}s để đặt cược ⏳\n\n"
                 f"🔵 Cửa Tài: Tổng tiền {sum(amount for bets in taixiu_bets.values() for choice, amount in bets if choice == 'T')} ₫\n\n"
                 f"🔴 Cửa Xỉu: Tổng tiền {sum(amount for bets in taixiu_bets.values() for choice, amount in bets if choice == 'X')} ₫\n\n"
                 f"💰 Hũ hiện tại : {format_currency(jackpot_amount)} 💰\n\n"),
                reply_markup=reply_markup)
            save_game_state(phien_number, taixiu_timer, taixiu_bets)

    phien_number = load_phien_number()
    taixiu_betting_active = False
    lock_chat(context, TAIXIU_GROUP_ID)
    context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                             text=(f"⌛️ Hết thời gian đặt cược!\n\n"
                                   f"🎲🎲🎲 BOT CHUẨN BỊ TUNG XÚC XẮC 🎲🎲🎲\n\n"))
    generate_taixiu_result(update, context)

def update_bet_amount(user_id, bet_amount):
    bets = {}

    # Read the current contents of the file
    if os.path.exists("tongcuoc.txt"):
        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                bets[line_user_id] = line_bet_amount  # Store as string to preserve decimal places

    # Update the bet amount for the user
    if str(user_id) in bets:
        current_bet_amount = float(bets[str(user_id)])
        updated_bet_amount = current_bet_amount + bet_amount
        bets[str(user_id)] = updated_bet_amount
    else:
        bets[str(user_id)] = bet_amount

    # Write the updated contents back to the file
    with open("tongcuoc.txt", "w") as file:
        for line_user_id, line_bet_amount in bets.items():
            file.write(f"{line_user_id} {line_bet_amount}\n")

def get_today_bets(user_id):
    bets = {}
    if os.path.exists("tongcuoc.txt"):
        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                bets[line_user_id] = float(line_bet_amount)  # Chuyển đổi sang float để giữ số thập phân

    return bets.get(str(user_id), 0)





def taixiu_bet(update: Update, context: CallbackContext):
    global taixiu_bets, taixiu_game_active, taixiu_timer, jackpot_amount, user_balances, taixiu_betting_active, md5_bets, md5_game_active, md5_timer

    if not update.message:
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    chat_id = update.message.chat_id
    is_private = chat_id == user_id
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return

    try:
        member = context.bot.get_chat_member(chat_id=update.message.chat_id,
                                             user_id=user_id)
        if member.status in [ChatMember.LEFT, ChatMember.KICKED]:
            update.message.reply_text("🚫 Cược không chấp nhận")
            return
    except:
        update.message.reply_text("🚫 Cược không chấp nhận")
        return

    message_text = update.message.text.strip().split()
    if len(message_text) != 2:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Vui lòng nhập theo định dạng:\n👉 [T/X] [số tiền cược]")
        return

    choice = message_text[0].upper()
    bet_amount_str = message_text[1].lower()

    if choice not in ['T', 'X']:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="🚫 Cược không chấp nhận")
        return

    if bet_amount_str == 'max':
        bet_amount = user_balances.get(user_id, 0)
    else:
        try:
            bet_amount = int(bet_amount_str)
        except ValueError:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="🚫 Cược không chấp nhận")
            return

    if bet_amount <= 0:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="🚫 Cược không chấp nhận")
        return

    vip_users = load_vip_users()

    if taixiu_game_active:
        #if user_id not in vip_users and bet_amount > 5000:
        #context.bot.send_message(
        #chat_id=update.effective_chat.id,
        #text="Bạn là tân thủ, cược tối đa 5,000 VND")
        #return
        if not taixiu_betting_active:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="🚫 Cược không chấp nhận")
            return
        if bet_amount <= 999:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Cược tối thiểu 1,000 VND")
            return
        if user_balances.get(user_id, 0) < bet_amount:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Số dư không đủ để đặt cược.")
            return

        current_time = time.time()
        bet_times = user_bet_times[user_id]
        bet_times.append(current_time)

        while bet_times and current_time - bet_times[0] > 10:
            bet_times.popleft()

        if len(bet_times) >= 10:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🚫 Bạn đã cược quá nhanh, vui lòng chờ.")
            return

        if user_id not in taixiu_bets:
            taixiu_bets[user_id] = []

        if choice == 'T':
            existing_bets = [
                bet for bet in taixiu_bets[user_id] if bet[0] in ['X']
            ]
        elif choice == 'X':
            existing_bets = [
                bet for bet in taixiu_bets[user_id] if bet[0] in ['T']
            ]

        if existing_bets:
            if choice in ['T', 'X']:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🌺 Bạn Chỉ Có Thể Cược 1 Cửa Tài hoặc Xỉu")
            return

        taixiu_bets[user_id].append((choice, bet_amount))
        user_balances[user_id] -= bet_amount
        jackpot_amount += bet_amount * 0.05

        update_bet_amount(user_id, bet_amount)

        if is_private:
            if choice in ['T', 'X']:
                bet_success_message = (
                    f"✅ Cược ẩn danh thành công {format_currency(bet_amount)} vào cửa {'Tài' if choice == 'T' else 'Xỉu'}\n💵 Số dư : {format_currency(user_balances[user_id])}"
                )
            else:
                bet_success_message = (
                    f"✅ Cược thành công {format_currency(bet_amount)} vào cửa {'Chẵn' if choice == 'C' else 'Lẻ'}. (ẨN DANH)\n"
                )
            update.message.reply_text(bet_success_message)
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=
                f"✅ Cược thành công {format_currency(bet_amount)} vào cửa {'Tài 🔵' if choice == 'T' else 'Xỉu 🔴' if choice == 'X' else 'Chẵn ⚪️' if choice == 'C' else 'Lẻ ⚫️'}. (ẨN DANH)"
            )
            context.bot.send_message(
                chat_id=ROOM_CHECK,
                text=
                (f"CƯỢC ROOM ẨN DANH\n"
                 f"USER ID : <code>{user_id}</code>\n"
                 f"Tiền Cược : {format_currency(bet_amount)}\n"
                 f"Cửa Cược: {'Tài 🔵' if choice == 'T' else 'Xỉu 🔴' if choice == 'X' else 'Chẵn ⚪️' if choice == 'C' else 'Lẻ ⚫️'}"
                 ),
                parse_mode='HTML')

        else:
            if choice in ['T', 'X']:
                bet_success_message = (
                    f"✅ Cược thành công {format_currency(bet_amount)} vào cửa {'Tài 🔵' if choice == 'T' else 'Xỉu 🔴'}\n💵 Số dư : {format_currency(user_balances[user_id])}")
            try:
                context.bot.send_message(chat_id=user_id,
                                         text=bet_success_message)
            except Exception as e:
                update.message.reply_text(
                    "🚫 Cược không chấp nhận: Không thể gửi tin nhắn riêng cho bạn."
                )
                return

            if choice in ['T', 'X']:
                update.message.reply_text(
                    f"Bạn đã cược {format_currency(bet_amount)} vào cửa {'Tài' if choice == 'T' else 'Xỉu'}.\n"
                    f"✅ Số dư: {format_currency(user_balances[user_id])}")
            context.bot.send_message(
                chat_id=ROOM_CHECK,
                text=
                (f"CƯỢC ROOM\n"
                 f"USER ID : <code>{user_id}</code>\n"
                 f"Tiền Cược : {format_currency(bet_amount)}\n"
                 f"Cửa Cược: {'Tài 🔵' if choice == 'T' else 'Xỉu 🔴' if choice == 'X' else 'Chưa chọn'}."
                 ),
                parse_mode='HTML')

            save_game_state(load_phien_number(), taixiu_timer, taixiu_bets)

    elif md5_game_active:
        if md5_timer <= 0:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="🚫 Cược không chấp nhận")
            return

        if bet_amount < 100:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Cược tối thiểu 100 VND")
            return

        if user_balances.get(user_id, 0) < bet_amount:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Số dư không đủ để đặt cược.")
            return

        current_time = time.time()
        bet_times = user_bet_times[user_id]
        bet_times.append(current_time)

        while bet_times and current_time - bet_times[0] > 10:
            bet_times.popleft()

        if len(bet_times) >= 3:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🚫 Bạn đã cược quá nhanh, vui lòng chờ.")
            return

        if user_id not in md5_bets:
            md5_bets[user_id] = []

        existing_bets = [bet for bet in md5_bets[user_id] if bet[0] != choice]
        if existing_bets:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="🌺 Bạn Chỉ Có Thể Cược 1 Cửa")
            return

        md5_bets[user_id].append((choice, bet_amount))
        user_balances[user_id] -= bet_amount

        update_bet_amount(user_id, bet_amount)

        if is_private:
            bet_success_message = (
                f"✅ Cược thành công {format_currency(bet_amount)} vào cửa {'Tài' if choice == 'T' else 'Xỉu'}. (ẨN DANH)\n"
            )
            update.message.reply_text(bet_success_message)
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=
                f"✅ Cược thành công {format_currency(bet_amount)} vào cửa {'Tài' if choice == 'T' else 'Xỉu'}. (ẨN DANH)"
            )
            context.bot.send_message(
                chat_id=ROOM_CHECK,
                text=(
                    f"🌺 CƯỢC ROOM MD5 ẨN DANH🌺\n"
                    f"USER ID : <code>{user_id}</code>\n"
                    f"Tiền Cược : {format_currency(bet_amount)}\n"
                    f"Cửa Cược: {'Tài ⚫️' if choice == 'T' else 'Xỉu ⚪️'} ."),
                parse_mode='HTML')

        else:
            bet_success_message = (
                f"✅ Cược thành công {format_currency(bet_amount)} vào cửa {'Tài' if choice == 'T' else 'Xỉu'}.")
            try:
                context.bot.send_message(chat_id=user_id,
                                         text=bet_success_message)
            except Exception as e:
                update.message.reply_text(
                    "🚫 Cược không chấp nhận: Không thể gửi tin nhắn riêng cho bạn."
                )
                return

            update.message.reply_text(
                f"Bạn đã cược {format_currency(bet_amount)} vào cửa {'Tài' if choice == 'T' else 'Xỉu'}.\n")
            context.bot.send_message(
                chat_id=ROOM_CHECK,
                text=(
                    f"🌺 CƯỢC ROOM MD5 🌺\n"
                    f"USER ID : <code>{user_id}</code>\n"
                    f"Tiền Cược : {format_currency(bet_amount)}\n"
                    f"Cửa Cược: {'Tài ⚫️' if choice == 'T' else 'Xỉu ⚪️'} ."),
                parse_mode='HTML')

        save_game_state(load_phien_number(), md5_timer, md5_bets)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="⌛️ Chưa mở cược !")
        return

def payout_winners(update: Update, context: CallbackContext, result):
    global taixiu_bets, user_balances, winning_streaks, losing_streaks

    winners = [
        user_id for user_id, bets in taixiu_bets.items()
        if any(choice == result for choice, amount in bets)
    ]
    losers = [
        user_id for user_id, bets in taixiu_bets.items()
        if not any(choice == result for choice, amount in bets)
    ]

    total_win_amount = 0
    total_lose_amount = 0

    for user_id in winners:
        win_amount = 0
        for choice, amount in taixiu_bets[user_id]:
            if choice == result:
                win_amount += amount * 1.95

        user_balances[user_id] = user_balances.get(user_id, 0) + win_amount
        context.bot.send_message(
            chat_id=user_id,
            text=
            f"✅ Thắng ZRoom kỳ <b>XX{load_phien_number()}</b> : {format_currency(win_amount)}\n💵 Số dư hiện tại 💵 : {format_currency(user_balances[user_id])}",
            parse_mode='HTML')

        total_win_amount += win_amount

        winning_streaks[user_id] = winning_streaks.get(user_id, 0) + 1
        losing_streaks[user_id] = 0


    for user_id in losers:
        lose_amount = sum(amount for choice, amount in taixiu_bets[user_id]
                          if choice != result)
        context.bot.send_message(
            chat_id=user_id,
            text=
            f"🛑 Thua ZRoom kỳ <b>XX{load_phien_number()}</b> : {format_currency(lose_amount)}.\n💵 Số dư hiện tại 💵: {format_currency(user_balances[user_id])}",parse_mode='HTML'
        )
        total_lose_amount += lose_amount

        losing_streaks[user_id] = losing_streaks.get(user_id, 0) + 1
        winning_streaks[user_id] = 0

    save_streaks("chuoithang.txt", winning_streaks)
    save_streaks("chuoithua.txt", losing_streaks)

    result_message = (f"🍀 Phiên: {load_phien_number()}\n"
                      f"🍀 Kết quả: {'🔵 TAI' if result == 'T' else '🔴 XIU' }\n"
                      f"🍀 Tổng thắng: {format_currency(total_win_amount)}\n"
                      f"🍀 Tổng thua: {format_currency(total_lose_amount)}")
    context.bot.send_message(chat_id=-1002155228022, text=result_message)

def save_streaks(filename, streaks):
    with open(filename, "w") as file:
        for user_id, streak in streaks.items():
            file.write(f"{user_id} {streak}\n")

def load_streaks(filename):
    streaks = {}
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                user_id, streak = line.strip().split()
                streaks[int(user_id)] = int(streak)
    return streaks


def save_streaks(filename, streaks):
    with open(filename, "w") as file:
        for user_id, streak in streaks.items():
            file.write(f"{user_id} {streak}\n")
def load_streaks(filename):
    streaks = {}
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                user_id, streak = line.strip().split()
                streaks[int(user_id)] = int(streak)
    return streaks




@retry_on_failure(retries=3, delay=5)
def set_custom_dice(update: Update, context: CallbackContext):
    global custom_dice_values

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if user_id not in ADMIN_ID or chat_id != -1002152949507:
        return

    if len(context.args) != 3:
        update.message.reply_text("Sai...")
        return

    try:
        dice1, dice2, dice3 = map(int, context.args)
        if not (1 <= dice1 <= 6 and 1 <= dice2 <= 6 and 1 <= dice3 <= 6):
            raise ValueError
        custom_dice_values = {"dice1": dice1, "dice2": dice2, "dice3": dice3}
        update.message.reply_text(f"Đã Chỉnh : {dice1}, {dice2}, {dice3}")
    except ValueError:
        update.message.reply_text("Sai...")


@retry_on_failure(retries=3, delay=5)
def set_dice_T(update: Update, context: CallbackContext):
    global custom_dice_values

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if chat_id != -1002152949507:
        return

    if user_id not in ADMIN_ID:
        return

    dice_values = []
    while sum(dice_values) < 11 or sum(dice_values) > 18:
        dice_values = [random.randint(1, 6) for _ in range(3)]
    custom_dice_values = {
        "dice1": dice_values[0],
        "dice2": dice_values[1],
        "dice3": dice_values[2]
    }
    update.message.reply_text(
        f"Chỉnh 'T': {dice_values[0]}, {dice_values[1]}, {dice_values[2]}")


@retry_on_failure(retries=3, delay=5)
def set_dice_X(update: Update, context: CallbackContext):
    global custom_dice_values

    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        return

    dice_values = []
    while sum(dice_values) < 3 or sum(dice_values) > 10:
        dice_values = [random.randint(1, 6) for _ in range(3)]
    custom_dice_values = {
        "dice1": dice_values[0],
        "dice2": dice_values[1],
        "dice3": dice_values[2]
    }
    update.message.reply_text(
        f"Chỉnh 'X': {dice_values[0]}, {dice_values[1]}, {dice_values[2]}")

@retry_on_failure(retries=3, delay=5)
def generate_taixiu_result(update: Update, context: CallbackContext):
    global taixiu_game_active, taixiu_bets, jackpot_amount, recent_results,user_balances

    if not taixiu_game_active:
        return

    time.sleep(random.uniform(0, 1))
    dice1 = context.bot.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value
    time.sleep(random.uniform(0, 1))
    dice2 = context.bot.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value
    time.sleep(random.uniform(0, 1.5))
    dice3 = context.bot.send_dice(chat_id=TAIXIU_GROUP_ID).dice.value

    time.sleep(random.uniform(0, 1.5))
    dice_values = [dice1, dice2, dice3]
    total = sum(dice_values)
    phien_number = load_phien_number()

    if total == 3:
        result = "X"
        result_emoji = "🟡"
        recent_results.append(result_emoji)
        save_recent_results()
        
        total_bet_amount = sum(amount for user_id, bets in taixiu_bets.items() for choice, amount in bets if choice == result)
        top_bettors = []

        for user_id, bets in taixiu_bets.items():
            for choice, amount in bets:
                if choice == result:
                    payout = (amount / total_bet_amount) * jackpot_amount
                    total_payout = payout + amount
                    update_user_balance(user_id, total_payout)
                    top_bettors.append((user_id, amount, total_payout))

                    context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"🎉 <b>Thắng Nổ Hũ Kỳ XX{phien_number}</b>: {format_currency(payout)}\n"
                        ),
                        parse_mode='HTML'
                    )

        context.bot.send_message(
            chat_id=-1002155228022,
            text=f"Nổ hũ Room {dice1} - {dice2} - {dice3}"
        )

        try:
            result_message = f"<b>Nổ Hũ Kỳ XX{phien_number}</b>\n"
            result_message += f"<b>Kết Quả {dice1} - {dice2} - {dice3}</b>\n\n"
            result_message += "<b>👉 ID Top - Tiền Cược - Tiền Nhận Hũ</b>\n"
            for user_id, bet_amount, payout in top_bettors:
                result_message += f"<a href='tg://user?id={user_id}'>{user_id}</a> - {format_currency(bet_amount)} - {format_currency(payout)}\n"

            pinned_message = context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=result_message,
                parse_mode='HTML'
            )
            context.bot.pin_chat_message(chat_id=TAIXIU_GROUP_ID,
                                         message_id=pinned_message.message_id,
                                         disable_notification=True)
        except Exception as e:
            logging.error(f"Failed to send new game message: {e}")

        jackpot_amount = 50000
        taixiu_game_active = False
        clear_game_state()
        
        try:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=("🎲 Phiên MD5 Sẽ Bắt Đầu Trong Giây Lát 🎲"),
            )
            unlock_chat(context, TAIXIU_GROUP_ID)
            time.sleep(5)
            increment_phien_number()
            time.sleep(5)
            start_md5_game(update, context)
        except Exception as e:
            logging.error(f"Failed to send new game message: {e}")

    elif total == 18:
        result = "T"
        result_emoji = "🟡"
        recent_results.append(result_emoji)
        save_recent_results()
        
        total_bet_amount = sum(amount for user_id, bets in taixiu_bets.items() for choice, amount in bets if choice == result)
        top_bettors = []

        for user_id, bets in taixiu_bets.items():
            for choice, amount in bets:
                if choice == result:
                    payout = (amount / total_bet_amount) * jackpot_amount
                    total_payout = payout + amount
                    update_user_balance(user_id, total_payout)
                    top_bettors.append((user_id, amount, total_payout))

                    context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"🎉 <b>Thắng Nổ Hũ Kỳ XX{phien_number}</b>: {format_currency(payout)}\n"
                        ),
                        parse_mode='HTML'
                    )

        context.bot.send_message(
            chat_id=-1002152949507,
            text=f"Nổ hũ Room {dice1} - {dice2} - {dice3}"
        )

        try:
            result_message = f"<b>Nổ Hũ Kỳ XX{phien_number}</b>\n"
            result_message += f"<b>Kết Quả {dice1} - {dice2} - {dice3}</b>\n\n"
            result_message += "<b>👉 ID Top - Tiền Cược - Tiền Nhận Hũ</b>\n"
            for user_id, bet_amount, payout in top_bettors:
                result_message += f"<a href='tg://user?id={user_id}'>{user_id}</a> - {format_currency(bet_amount)} - {format_currency(payout)}\n"

            pinned_message = context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=result_message,
                parse_mode='HTML'
            )
            context.bot.pin_chat_message(chat_id=TAIXIU_GROUP_ID,
                                         message_id=pinned_message.message_id,
                                         disable_notification=True)
        except Exception as e:
            logging.error(f"Failed to send new game message: {e}")

        jackpot_amount = 50000
        taixiu_game_active = False
        clear_game_state()
        
        try:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=("🎲 Phiên MD5 Sẽ Bắt Đầu Trong Giây Lát 🎲"),
            )
            unlock_chat(context, TAIXIU_GROUP_ID)
            time.sleep(5)
            increment_phien_number()
            time.sleep(5)
            start_md5_game(update, context)
        except Exception as e:
            logging.error(f"Failed to send new game message: {e}")

    else:
        if total >= 11:
            result = "T"
            result_emoji = "🔵"
        else:
            result = "X"
            result_emoji = "🔴"

        recent_results.append(result_emoji)
        if len(recent_results) > 10:
            recent_results.pop(0)
        save_recent_results()

        phien_number = load_phien_number()

        try:
            keyboard = [[
                InlineKeyboardButton(
                    "💵 Nạp Tiền 💵", url=f'https://t.me/zroom_tx_bot?start=nap')
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=(
                    f"🧾 Phiên #{phien_number}\n\n"
                    f"🎲 Kết quả: {dice1} - {dice2} - {dice3} 🎲\n\n"
                    f"Kết quả: {result_emoji} {'TÀI' if result == 'T' else 'XỈU'} - {total}\n\n"
                ),
                reply_markup=reply_markup
            )

            context.bot.send_message(
                chat_id=ROOM_KQ,
                text=(
                    f"🔜 Kết quả Xúc Xắc phiên #{phien_number}\n\n"
                    f"🎲 {dice1} - {dice2} - {dice3} 🎲\n\n"
                    f"🍀 {result_emoji} {'TÀI' if result == 'T' else 'XỈU'} - {total} 🍀\n\n"
                    f"📝 Kết quả 10 phiên gần nhất :\n"
                    f"     TÀI 🔵 | XỈU 🔴 | BÃO 🟡\n"
                    f"{format_recent_results()}"
                )
            )

        except Exception as e:
            logging.error(f"Failed to send result message: {e}")

        payout_winners(update, context, result)
        save_user_balances()

        taixiu_game_active = False
        clear_game_state()

        try:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=("🎲 Phiên Tài Xỉu Sẽ Bắt Đầu Trong Giây Lát 🎲"),
            )
            unlock_chat(context, TAIXIU_GROUP_ID)
            time.sleep(5)
            increment_phien_number()
            time.sleep(5)
            start_taixiu(update, context)
        except Exception as e:
            logging.error(f"Failed to send")
                          

def admin_md5_command(update: Update, context: CallbackContext):
    global md5_game_error
    md5_game_error = not md5_game_error
    status = "Đã bật" if md5_game_error else "Đã tắt"
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Trạng thái lỗi MD5 {status}.")


@retry_on_failure(retries=3, delay=5)
def start_md5_game(update: Update, context: CallbackContext):
    global md5_game_active, md5_bets, md5_timer, md5_game_error

    md5_game_active = True
    md5_bets = {}
    md5_timer = 49

    if md5_game_error:
        context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                 text=(f"🎲 Phiên Cược MD5 Bắt Đầu 🎲\n\n"
                                       f"📌 Lệnh Cược: <T/X> <Cược/Max>\n\n"
                                       f"⏳ Còn {md5_timer}s để đặt cược ⏳\n\n"
                                       f"❌ Lỗi Khi Khởi Tạo Mã MD5 ❌"))
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=("✅ Phiên MD5 Đã Được Dừng ✅\n"
                  "🎲 Phiên Tài Xỉu Sẽ Bắt Đầu Trong Giây Lát 🎲"))
        md5_game_error = False
        time.sleep(5)
        start_taixiu(update, context)
        return

    context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                             text=(f"🎲 Phiên Cược MD5 Bắt Đầu 🎲\n\n"
                                   f"📌 Lệnh Cược: <T/X> <Cược/Max>\n\n"
                                   f"⏳ Còn {md5_timer}s để đặt cược ⏳\n\n"
                                   f"🍀 Đã Tạo Thành Công MD5 Hash 🍀"))

    threading.Thread(target=md5_timer_countdown,
                     args=(update, context)).start()


@retry_on_failure(retries=3, delay=5)
def md5_timer_countdown(update: Update, context: CallbackContext):
    global md5_timer, md5_game_active

    while md5_timer > 0:
        time.sleep(1)
        md5_timer -= 1

        if md5_timer % 20 == 0:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=
                (f"⏳ Phiên MD5. Còn {md5_timer}s để đặt cược ⏳\n\n📌 Lệnh Cược: <T/X> <Cược/Max>"
                 ))

    md5_game_active = False
    context.bot.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text="⌛️ Hết thời gian đặt cược!\n\n🎲 Kết Quả Đang Được Mã Hóa 🎲")

    time.sleep(2)
    generate_md5_result(update, context)


@retry_on_failure(retries=3, delay=5)
def generate_md5_result(update: Update, context: CallbackContext):
    global md5_bets, user_balances, custom_dice_values

    if custom_dice_values:
        dice1 = custom_dice_values["dice1"]
        dice2 = custom_dice_values["dice2"]
        dice3 = custom_dice_values["dice3"]
        custom_dice_values = {}
    else:
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        dice3 = random.randint(1, 6)

    total = sum([dice1, dice2, dice3])

    if total >= 11:
        result = "T"
    else:
        result = "X"

    md5_hash, result_str = calculate_md5(dice1, dice2, dice3)
    context.bot.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text=(f"🎲 Xúc Xắc : {dice1} - {dice2} - {dice3} 🎲\n\n"
              f"✨ Kết quả: {'⚫ TÀI' if result == 'T' else '⚪ XỈU'} {total}\n\n"
              f"💥 Mã hóa MD5 : <code>{md5_hash}</code>\n\n"
              f"☄️ Kết quả mã hóa MD5 : <code>{result_str}</code>"),
        parse_mode='HTML')

    payout_md5_winners(update, context, result)

    try:
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=("🎲 Phiên Tài Xỉu Sẽ Bắt Đầu Trong Giây Lát 🎲"),
        )
        time.sleep(10)
        unlock_chat(context, TAIXIU_GROUP_ID)
        time.sleep(3)
        start_taixiu(update, context)
        result_messages = (f"🍀 BẮT ĐẦU NHẬN CƯỢC PHIÊN TÀI XỈU\n")
        context.bot.send_message(chat_id=-1002152949507, text=result_messages)
    except Exception as e:
        logging.error(f"Failed to send new game message: {e}")


@retry_on_failure(retries=3, delay=5)
def payout_md5_winners(update: Update, context: CallbackContext, result):
    global md5_bets, user_balances

    for user_id, bets in md5_bets.items():
        for choice, amount in bets:
            if choice == result:
                payout = amount * 2.45
                user_balances[user_id] += payout
                context.bot.send_message(
                    chat_id=user_id,
                    text=
                    f"🎉 Thắng Kỳ MD5 : {format_currency(payout)}\n💵 Số dư hiện tại 💵 : {format_currency(user_balances[user_id])}"
                )
    save_user_balances()
    result_message = (f"🍀 Phiên MD5 KẾT THÚC\n"
                      f"🍀 Kết quả: {'⚫ TAI' if result == 'T' else '⚪ XIU'}\n")
    context.bot.send_message(chat_id=-1002152949507, text=result_message)


def nap(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if not update.message:
        context.bot.send_message(
            chat_id=user.id,
            text=
            ("🏦 NẠP TIỀN 🏦\n\nLệnh Nạp : /nap [Số Tiền Nạp]\n\n⚠️ Lưu ý : \n\n"
             "❌ Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.\n\n"
             "✅ Nội dung phải CHÍNH XÁC. Nếu không sẽ không nạp được tiền.\n\n"
             "✅ NẠP TỐI THIỂU 10K. TRƯỜNG HỢP NẠP DƯỚI 10K, GAME KHÔNG HỖ TRỢ GIAO DỊCH LỖI.\n\n"
             "✅ SAU KHI NẠP SẼ THOÁT TÂN THỦ"))
        return

    message_text = update.message.text.split()
    if len(message_text) != 2:
        update.message.reply_text(
            "🏦 NẠP TIỀN 🏦\n\nLệnh Nạp : /nap [Số Tiền Nạp]\n\n⚠️ Lưu ý : \n\n"
            "❌ Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.\n\n"
            "✅ Nội dung phải CHÍNH XÁC. Nếu không sẽ không nạp được tiền.\n\n"
            "✅ NẠP TỐI THIỂU 10K. TRƯỜNG HỢP NẠP DƯỚI 10K, GAME KHÔNG HỖ TRỢ GIAO DỊCH LỖI.\n\n"
            "✅ SAU KHI NẠP SẼ THOÁT TÂN THỦ")
        return

    amount_str = message_text[1]
    user_id = user.id

    try:
        amount = int(amount_str)
    except ValueError:
        update.message.reply_text(
            "🏦 NẠP TIỀN 🏦\n\nLệnh Nạp : /nap [Số Tiền Nạp]\n\n⚠️ Lưu ý : \n\n"
            "❌ Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.\n\n"
            "✅ Nội dung phải CHÍNH XÁC. Nếu không sẽ không nạp được tiền.\n\n"
            "✅ NẠP TỐI THIỂU 10K. TRƯỜNG HỢP NẠP DƯỚI 10K, GAME KHÔNG HỖ TRỢ GIAO DỊCH LỖI.\n\n"
            "✅ SAU KHI NẠP SẼ THOÁT TÂN THỦ")
        return

    if amount < 10000:
        update.message.reply_text("Nạp Ít Nhất 10,000 VND")
        return

    message = (f"<b>Yêu Cầu Nạp Tiền :</b>\n\n"
               f"<b>🧧 MOMO BANKING</b>\n\n"
               f"👉 SỐ TÀI KHOẢN : <code>0909743280</code>\n\n\n"
               f"<b>🧧 BANK</b>\n\n"
               f"👉 SỐ TÀI KHOẢN : <code>Vui lòng chuyển QR</code>\n\n\n"
               f"<b>NỘI DUNG CHUYỂN</b>: <code>{user_id}</code>\n\n"
               f"<b>Lưu ý: Nạp tối thiểu 10.000đ</b>")

    admin_id = -1002152949507
    pinned_message = context.bot.send_message(
        chat_id=admin_id,
        text=f"💵 NẠP TIỀN 💵\nUSER ID {user_id}\nSỐ TIỀN : {amount}")
    context.bot.pin_chat_message(chat_id=admin_id,
                                 message_id=pinned_message.message_id,
                                 disable_notification=False)

    momo_image_path = "momo.jpg"
    with open(momo_image_path, 'rb') as momo_image:
        update.message.reply_photo(photo=momo_image,
                                   caption=message,
                                   parse_mode='HTML')


def duyet(update: Update, context: CallbackContext):
    global load_vip_users, vip_users
    user = update.message.from_user
    if user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyet <user_id> <số tiền>")
        return

    try:
        user_id_to_approve = int(context.args[0])
        amount_approved = float(context.args[1])

        if user_id_to_approve in user_balances:
            user_balances[user_id_to_approve] += amount_approved
        else:
            user_balances[user_id_to_approve] = amount_approved

        vip_users = load_vip_users()
        save_user_balances()

        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
        user_message = (
            f"✅ Nạp tiền thành công !!!!\n"
            f"➡️ Nội dung: {user_id_to_approve}\n"
            f"➡️ Thời gian: {current_time}\n"
            f"➡️ Số tiền: {format_currency(amount_approved)}\n"
            f"➡️ Số dư hiện tại: {format_currency(user_balances[user_id_to_approve])} ₫\n"
            f"➡️ Để rút: \n- Phát sinh cược 100% số tiền hiện có\n")
        context.bot.send_message(chat_id=user_id_to_approve, text=user_message)

        masked_user_id = str(user_id_to_approve)[:-4] + "****"
        group_message = (
            f"Người chơi ID: {masked_user_id}\n"
            f"- Nạp thành công {format_currency(amount_approved)}")

        context.bot.send_message(chat_id=TAIXIU_GROUP_ID, text=group_message)

        admin_reply = f"Đã duyệt nạp tiền cho người dùng ID {user_id_to_approve} với số tiền {format_currency(amount_approved)} ₫."
        update.message.reply_text(admin_reply)
        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)
        context.bot.send_message(
            chat_id=-1002152949507,
            text=
            (f"DUYỆT NẠP\n"
             f"ADMIN : {user.id}\n"
             f"THÊM : {format_currency(amount_approved)} CHO {user_id_to_approve}"
             ))
        if user_id_to_approve not in vip_users:
            add_vip_user(update, context, user_id_to_approve)

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyetnap <ID> <số tiền>")


def rut(update: Update, context: CallbackContext):
    if len(context.args) != 3:
        update.message.reply_text(
            "💵 RÚT TIỀN 💵\n\nLệnh Rút : /rut [Ngân Hàng] [STK] [Số Tiền Rút]\n\n⚠️ Lưu ý : \n❌ Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin SĐT.\n\n❌ Tân thủ không thể rút\n\n❗️ Phí rút tiền: 5,000đ cho các giao dịch chuyển sang ngân hàng"
        )
        return

    bank_name = context.args[0]
    account_number = context.args[1]
    amount = context.args[2]
    user_id = update.message.from_user.id
    vip_users = load_vip_users()
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return

    if user_id in [
            6401417058, 5777678653, 6879719558, 7005092871, 6260888156,
            7141311411
    ]:
        update.message.reply_text("Bạn là QTV, không thể rút tiền.")
        return

    try:
        amount = int(amount)
    except ValueError:
        update.message.reply_text("Số tiền phải là một số nguyên.")
        return

    if user_id not in vip_users:
        update.message.reply_text("Bạn là tân thủ, rút tiền qua admin \n\n👉 t.me/admztrongz")
        return
    else:
        if amount < 50000:
            update.message.reply_text("Số tiền cần rút tối thiểu 50,000 VND")
            return

    if user_id in user_balances:
        if user_balances[user_id] >= amount:
            user_balances[user_id] -= amount
            save_user_balances()
            update.message.reply_text(
                "🎊 Chúc mừng ! Lệnh rút đang được xử lý\n💵 Lệnh Rút Sẽ Được Hoàn Thành Từ 1H-24H\n☎️ Không hỗ trợ xử lý lệnh rút trước 48H ")

            admin_id = -1002152949507
            text = (f"💵 RÚT TIỀN 💵\n"
                    f"USER ID : {user_id}\n"
                    f"NGÂN HÀNG RÚT : {bank_name}\n"
                    f"SỐ TÀI KHOẢN : {account_number}\n"
                    f"SỐ TIỀN : {amount}")

            callback_data = f"approve_{user_id}_{bank_name}_{account_number}_{amount}"
            logger.info(f"Callback data: {callback_data}")

            buttons = [
                [
                    InlineKeyboardButton("DUYỆT RÚT",
                                         callback_data=callback_data)
                ],
                [
                    InlineKeyboardButton(
                        "/naprut",
                        callback_data=f"cancel_naprut_{user_id}_{amount}")
                ],
                [
                    InlineKeyboardButton(
                        "CƯỢC CHỈ TIÊU",
                        callback_data=f"cancel_bet_{user_id}_{amount}")
                ],
                [
                    InlineKeyboardButton(
                        "ĐƠN RÚT CÒN",
                        callback_data=f"cancel_pending_{user_id}_{amount}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

            pinned_message = context.bot.send_message(
                chat_id=admin_id, text=text, reply_markup=reply_markup)
            context.bot.pin_chat_message(chat_id=admin_id,
                                         message_id=pinned_message.message_id,
                                         disable_notification=False)
        else:
            update.message.reply_text("Số dư không đủ để thực hiện giao dịch.")
    else:
        update.message.reply_text("Số dư không đủ để thực hiện giao dịch.")


def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.split('_')
    logger.info(f"Callback data: {data}")
    action = data[0]
    user_id = query.from_user.id
    user_name = query.from_user.first_name
        
    if action == "approve":
        user_id = int(data[1])
        bank_name = data[2]
        account_number = data[3]
        amount = int(data[4])
    elif action == "cancel":
        reason = data[1]
        user_id = int(data[2])
        amount = int(data[3])

    if action == 'cmd':
        context.bot.send_message(chat_id=user_id,
                                 text="🛑 Start - Bắt đầu chơi\n"
                                 f"🛑 Cmd - Danh sách lệnh\n"
                                 f"🛑 Ref - Tuyển ref nhận tiền\n"
                                 f"🛑 Nap - Nạp tiền\n"
                                 f"🛑 Rut - Rút tiền\n"
                                 f"🛑 Code - Nhập Code\n"
                                 f"🛑 MuaGiftcode - Mua Code\n"
                                 f"🛑 Napthe - Nạp Thẻ Cào\n"
                                 f"🛑 Quest - Xem Nhiệm Vụ\n"
                                 f"🛑 Nhanquest - Nhận Nhiệm Vụ\n"
                                 f"🛑 /naprut - Luật Nạp Rút")
        logger.info(f"Nhắn Bot: {action}, User ID: {user_id}")
        return
    if action == "approve":
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
        message = (f"✅ Rút tiền thành công !!!!\n"
                   f"➡️ Số tài khoản: {account_number}\n"
                   f"➡️ Ngân hàng: {bank_name}\n"
                   f"➡️ Số tiền: {amount} ₫\n"
                   f"➡️ Thời gian: {current_time}\n")

        context.bot.send_message(chat_id=user_id, text=message)

        masked_user_id = str(user_id)[:-4] + "****"
        group_message = (f"Người chơi ID: {masked_user_id}\n"
                         f"- Rút thành công {amount} đ")

        context.bot.send_message(chat_id=TAIXIU_GROUP_ID, text=group_message)

    elif action == "cancel":
        user_balances[user_id] += amount
        save_user_balances()

        if reason == "naprut":
            context.bot.send_message(
                chat_id=user_id,
                text=
                "💸 Bạn Chưa Đủ Chỉ Tiêu Rút, Vui Lòng Xem Lại /naprut, Tiền Đã Được Hoàn Về Tài Khoản"
            )
        elif reason == "bet":
            context.bot.send_message(
                chat_id=user_id,
                text=
                "💸 Bạn Chưa Phát Sinh Cược 100% Số Tiền Hiện Có - Tiền Đã Được Hoàn Về Tài Khoản"
            )
        elif reason == "pending":
            context.bot.send_message(
                chat_id=user_id,
                text=
                "💸 Bạn Còn Đơn Rút Chưa Được Duyệt. Vui Lòng Chờ Đợi Đơn Duyệt Rồi Rút Đơn Khác (Tránh dồn). Tiền Đã Được Hoàn Về Tài Khoản Của Bạn"
            )

    query.edit_message_text(text=f"Lệnh {action} đã được thực hiện.")


def tb(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if len(context.args) < 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /tb <G hoặc P> <Nội dung>")
        return

    chat_type = context.args[0].upper()
    message = ' '.join(context.args[1:])

    if chat_type == 'G':
        context.bot.send_message(chat_id=-1002152949507, text=message)
        a = (f"USER ID : {user_id} SÀI /tb\n")
        context.bot.send_message(chat_id=6141663722, text=a)
    elif chat_type == 'P':
        user_id = update.message.from_user.id
        context.bot.send_message(chat_id=user_id, text=message)
    else:
        update.message.reply_text("Vui lòng chỉ định G hoặc P.")


def increment_phien_number():
    phien_number = load_phien_number()
    phien_number += 1
    save_phien_number(phien_number)


def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    if context.args:
        command = context.args[0].split('_')
        if command[0] == 'nap':
            nap(update, context)
    else:
        if user_id not in user_balances:
            user_balances[user_id] = 3000
            save_user_balances()

            welcome_message = (
                f"👋Xin Chào <b>{user_name}</b>, Bạn đã nhận được 3.000đ Từ Quà tặng tân thủ\n"
                f"👤 ID Của Bạn Là <code>{user_id}</code>\n"
                f"🧧 Tham gia Room TX để săn hũ và nhận giftcode hằng ngày\n"
                f"🎗 Theo dõi Channel: Để nhận thông báo mới nhất\n"
            )
            message_to_send = welcome_message
        else:
            welcome_back_message = (
                f"👋Xin Chào <b>{user_name}</b>, Bạn đã trở lại bot\n"
                f"👤 ID Của Bạn Là <code>{user_id}</code>\n"
                f"🧧 Tham gia Room TX để săn hũ và nhận giftcode hằng ngày\n"
                f"🎗 Theo dõi Channel: Để nhận thông báo mới nhất\n"
            )
            message_to_send = welcome_back_message

        buttons = [
            [InlineKeyboardButton("🎀 Danh Sách Lệnh 🎀", callback_data='cmd')],
            [InlineKeyboardButton("☄️ ZROOM V2 - ROOM TÀI XỈU ☄️", url="https://t.me/zroomtaixiu")],
            [InlineKeyboardButton("🎉 ZROOM - KÊNH THÔNG BÁO 🎉", url="https://t.me/zroomthongbao")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        user_keyboard = ReplyKeyboardMarkup([
            ["👤 Tài Khoản", "💵 Tổng Cược"],
            ["🏆 Đu Dây Tài Xỉu 🏆", "📞 CSKH"]
        ], resize_keyboard=True, one_time_keyboard=True)

        context.bot.send_message(
            chat_id=user_id,
            text=message_to_send,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        context.bot.send_message(
            chat_id=user_id,
            text="Chọn một tùy chọn:",
            reply_markup=user_keyboard
        )
        return
def cskh(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="📞 CSKH : [Liên hệ tại đây](https://t.me/admztrongz)",
        parse_mode='Markdown'
    )

def handle_cskh(update: Update, context: CallbackContext):
    if update.message.text == "📞 CSKH":
        cskh(update, context)
        
def handle_user_buttons(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text

    vip_points = load_vip_points()

    if text == "👤 Tài Khoản":
        balance = user_balances.get(user_id, 0)
        today_bets = get_today_bets(user_id)
        user_vip_points = vip_points.get(user_id, 0)  # Get user's VIP points
        account_info = (
            f"<b>👤 ID:</b> <code>{user_id}</code>\n"
            f"<b>💰 Số dư hiện tại:</b> {format_currency(balance)}\n"
            f"<b>💥 Cược hôm nay:</b> {format_currency(today_bets)}\n"
            f"<b>☘️ VIP của bạn:</b> {user_vip_points}\n"
            f"<b>💵 Mã nạp tiền:</b> <code>{user_id}</code>"
        )
        update.message.reply_text(account_info, parse_mode='HTML')

    elif text == "💵 Tổng Cược":
        today_bets = get_today_bets(user_id)
        total_bets = (
            f"<b>👤 ID:</b> <code>{user_id}</code>\n"
            f"<b>💵 Cược hôm nay:</b> {format_currency(today_bets)}"
        )
        update.message.reply_text(total_bets, parse_mode='HTML')





def cmd(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    update.message.reply_text(f"🛑 Start - Bắt đầu chơi\n"
                              f"🛑 Cmd - Danh sách lệnh\n"
                              f"🛑 Ref - Tuyển ref nhận tiền\n"
                              f"🛑 Nap - Nạp tiền\n"
                              f"🛑 Rut - Rút tiền\n"
                              f"🛑 Code - Nhập Code\n"
                              f"🛑 MuaGiftcode - Mua Code\n"
                              f"🛑 Napthe - Nạp Thẻ Cào\n"
                              f"🛑 Quest - Xem Nhiệm Vụ\n"
                              f"🛑 Nhanquest - Nhận Nhiệm Vụ\n"
                              f"🛑 /naprut - Luật Nạp Rút")


def start_referral(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    referral_link = f"https://t.me/zroom_tx_bot?start={user_id}"
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f"🎉 Chào mừng bạn đến với bot ZROOM ! 🎉\n\n"
        f"Bạn đã tạo ra link referral thành công! Mời bạn bè tham gia sử dụng bot bằng cách sử dụng link sau:\n"
        f"{referral_link}\n\n"
        f"Bạn sẽ nhận được 500đ vào số dư khi mỗi người dùng mới sử dụng link của bạn để tham gia!"
    )


def sd(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if user_id in user_balances:
        balance = user_balances[user_id]
        if balance == 0:
            update.message.reply_text(
                "💵 Số dư của bạn là: 0 ₫ 💵\n\nLệnh /nap để nạp tiền.")
        else:
            update.message.reply_text(
                f"💵 Số dư của bạn là: {format_currency(balance)} 💵")
    else:
        update.message.reply_text("Bạn Chưa Có Số Dư")


def load_codes():
    codes = {}
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    code, value = parts
                    try:
                        codes[code] = float(value)
                    except ValueError:
                        continue
    return codes


def save_codes(codes):
    with open(CODES_FILE, 'w') as file:
        for code, value in codes.items():
            file.write(f"{code} {value}\n")


def addcode(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addcode <tên code> <giá trị code>")
        return

    code_name = context.args[0]
    code_value = context.args[1]

    try:
        code_value = float(code_value)
    except ValueError:
        update.message.reply_text("Giá trị code phải là một số.")
        return

    codes = load_codes()
    codes[code_name] = code_value
    save_codes(codes)

    update.message.reply_text(
        f"Đã thêm code: {code_name} với giá trị: {format_currency(code_value)}"
    )

def redeem_code(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="💵 Nhập Code 💵\n\n Nhập mã code theo định dạng:\n👉 [ /code ] dấu cách [ Mã Code ]\n\n 📌 Ví dụ: /code 123456"
        )
        return

    code_name = context.args[0]
    user_id = update.message.from_user.id

    codes = load_codes()
    if code_name not in codes:
        context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="Code không hợp lệ hoặc đã được sử dụng."
        )
        return

    code_value = codes.pop(code_name)
    user_balances[user_id] = user_balances.get(user_id, 0) + code_value
    save_codes(codes)
    save_user_balances()
    masked_user_id = str(user_id)[:-4] + "****"

    context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=f"💵 Bạn đã nhận được {format_currency(code_value)} từ code {code_name}."
    )
    context.bot.send_message(
        chat_id=-1002155228022,
        text=(f"🛍 NHẬP CODE : {user_id} 🛍\n"
              f"Tên Code : {code_name}\n"
              f"Code có giá trị {format_currency(code_value)}.")
    )
    context.bot.send_message(
        chat_id=TAIXIU_GROUP_ID,
        text=(f"💵 User {masked_user_id} Nhập Thành Công 1 Giftcode\n💎 Giá Trị {format_currency(code_value)}")
    )
    

def addsodu(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addsd <user_id> <số tiền>")
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])

        if user_id in user_balances:
            user_balances[user_id] += amount
        else:
            user_balances[user_id] = amount

        save_user_balances()
        update.message.reply_text(
            f"Đã cộng {format_currency(amount)} vào tài khoản {user_id}. Số dư hiện tại: {format_currency(user_balances[user_id])}"
        )
        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)
        context.bot.send_message(chat_id=-1002152949507,
                                 text=(f"🔰 ADMIN ADD SỐ DƯ 🔰\n"
                                       f"ADMIN ID : {user_id}\n"
                                       f"Cộng {format_currency(amount)}"))

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addsd <user_id> <số tiền>")


def generate_gift_codes(quantity, price_per_code):
    codes = {}
    for _ in range(quantity):
        code = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=8))
        codes[code] = price_per_code
    return codes


def generate_gift_code(min_value, max_value):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    value = random.randint(min_value, max_value)
    return code, value


def freecode(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    code, value = generate_gift_code(1000, 5000)

    codes = load_codes()
    codes[code] = value
    save_codes(codes)

    try:
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=
            f"🎁 GIFTCODE MIỄN PHÍ : {code}\n💰 Giá trị ngẫu nhiên 1,000 - 5,000 💵"
        )
        update.message.reply_text(
            f"Mã giftcode miễn phí {code} với giá trị {format_currency(value)} đã được gửi vào nhóm."
        )
    except Exception as e:
        update.message.reply_text(f"Đã xảy ra lỗi khi gửi giftcode: {str(e)}")


def load_message_count():
    if os.path.exists(MESSAGE_COUNT_FILE):
        with open(MESSAGE_COUNT_FILE, 'r') as file:
            try:
                data = json.load(file)
                if isinstance(data, dict) and "count" in data:
                    return data["count"]
                else:
                    save_message_count(0)
                    return 0
            except json.JSONDecodeError:
                save_message_count(0)
                return 0
    else:
        save_message_count(0)
        return 0


def save_message_count(count):
    with open(MESSAGE_COUNT_FILE, 'w') as file:
        json.dump({"count": count}, file)


def check_message_count(update: Update, context: CallbackContext):
    count = load_message_count()
    count += 1
    save_message_count(count)

    if count >= MESSAGE_THRESHOLD:
        code, value = generate_gift_code(100, 7000)
        codes = load_codes()
        codes[code] = value
        save_codes(codes)

        try:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=f"🎉 Chúc mừng nhóm đã đạt {MESSAGE_THRESHOLD} tin nhắn! 🎉\n"
                f"🎁 GIFTCODE MIỄN PHÍ: <code>{code}</code>\n"
                f"💰 Giá trị ngẫu nhiên 1.000 - 10.000 ",
                parse_mode='HTML')
            save_message_count(0)
        except Exception as e:
            context.bot.send_message(
                chat_id=TAIXIU_GROUP_ID,
                text=f"Đã xảy ra lỗi khi gửi giftcode tự động: {str(e)}")


def message_handler(update: Update, context: CallbackContext):
    message_text = update.message.text
    if message_text == "📊 Kết Quả Gần Nhất":
        ALO(update, context)
        return
    if message_text == "📞 CSKH":
        cskh(update, context)
        return
    if "🏆 Đu Dây Tài Xỉu 🏆" in message_text:
        chuoi(update, context)
        return
    if update.message.chat_id == TAIXIU_GROUP_ID:
        check_message_count(update, context)


def send_gift_code_to_user(user_id, code, value, context):
    try:
        context.bot.send_message(chat_id=user_id,
                                 text=f"🎁 Đây là mã giftcode của bạn: {code}\n"
                                 f"💰 Giá trị: {value} VND\n"
                                 f"Hãy nhập mã này vào hệ thống để sử dụng.")
    except Exception as e:
        print(f"Error sending gift code to user {user_id}: {str(e)}")


def muagiftcode(update: Update, context: CallbackContext):
    if not update.message:
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    try:
        member = context.bot.get_chat_member(chat_id=update.message.chat_id,
                                             user_id=user_id)
        if member.status in [ChatMember.LEFT, ChatMember.KICKED]:
            update.message.reply_text(
                "Bạn không thể mua giftcode: Không contact với bot!")
            return
    except:
        update.message.reply_text(
            "Có lỗi xảy ra khi kiểm tra trạng thái thành viên.")
        return

    message_text = update.message.text.strip().split()

    if len(message_text) != 3:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            "Vui lòng nhập theo định dạng: /muagiftCode [số lượng giftcode] [số tiền mỗi giftcode]"
        )
        return

    try:
        quantity = int(message_text[1])
        price_per_code = int(message_text[2])
    except ValueError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Số lượng giftcode và số tiền mỗi giftcode phải là số nguyên."
        )
        return

    if quantity < 5 or quantity > 10:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Số lượng giftcode phải từ 5 đến 10.")
        return

    if price_per_code <= 5000:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Số tiền mỗi giftcode phải lớn hơn 5,000 VND.")
        return

    total_cost = quantity * price_per_code
    fee = total_cost * 0.1
    final_cost = total_cost + fee

    if user_balances.get(user_id, 0) < final_cost:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            f"Số dư của bạn không đủ để mua {quantity} giftcode với giá {price_per_code} mỗi giftcode."
        )
        return

    codes = generate_gift_codes(quantity, price_per_code)

    existing_codes = load_codes()
    existing_codes.update(codes)
    save_codes(existing_codes)

    user_balances[user_id] -= final_cost

    codes_message = "\n".join(
        [f"<code>{code}</code>" for code, value in codes.items()])

    context.bot.send_message(chat_id=-1002152949507,
                             text=(f"💝 MUA GIFTCODE 💝\n"
                                   f"ID: {user_id}\n"
                                   f"Giftcodes:\n{codes_message}\n"
                                   f"Code có giá trị {price_per_code}."),
                             parse_mode=ParseMode.HTML)

    context.bot.send_message(
        chat_id=user_id,
        text=
        (f"🛍 Đã mua thành công {quantity} giftcode\n\n"
         f"Giá: {format_currency(price_per_code)} / 1 Giftcode\n"
         f"Tổng tiền phải thanh toán: {format_currency(final_cost)} (bao gồm phí 10%).\n"
         f"Giftcode của bạn:\n{codes_message}"),
        parse_mode=ParseMode.HTML)


def delsodu(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /delsd <user_id> <số tiền>")
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])

        if user_id in user_balances:
            user_balances[user_id] -= amount
        else:
            user_balances[user_id] = amount

        save_user_balances()
        update.message.reply_text(
            f"Đã trừ {format_currency(amount)} vào tài khoản {user_id}. Số dư hiện tại: {format_currency(user_balances[user_id])}"
        )
        context.bot.delete_message(chat_id=update.message.chat_id,
                                   message_id=update.message.message_id)

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /delsd <user_id> <số tiền>")


def napthe(update, context):
    user_id = update.message.from_user.id

    if len(context.args) != 4:
        update.message.reply_text(
            "💳 NẠP THẺ 💳\n\nLệnh Nạp /napthe <Seri> <Card> <Nhà Mạng> <Mệnh Giá>\n\nChiết Khấu 20% Cho Mọi Loại Thẻ Cào"
        )
        return

    seri, card, nha_mang, menh_gia = context.args

    if nha_mang.lower() not in [
            'viettel', 'vinaphone', 'mobiphone', 'vietnamobile'
    ]:
        update.message.reply_text(
            "Nhà mạng không hợp lệ. Vui lòng chọn trong [Viettel, Vinaphone, Mobiphone, Vietnamobile]."
        )
        return

    if menh_gia not in MENH_GIA:
        update.message.reply_text("Mệnh giá không hợp lệ.")
        return

    admin_message = (
        f"<b>Yêu cầu nạp thẻ mới:</b>\n"
        f"<b>Người dùng:</b> {update.message.from_user.full_name}\n"
        f"<b>Seri:</b> <code>{seri}</code>\n"
        f"<b>Card:</b> <code>{card}</code>\n"
        f"<b>Nhà mạng:</b> {nha_mang}\n"
        f"<b>Mệnh giá:</b> {menh_gia}\n\n"
        f"<i>User ID</i> : <code>{user_id}</code> ")

    context.bot.send_message(chat_id=6793700101,
                             text=admin_message,
                             parse_mode='HTML')
    update.message.reply_text(
        "Yêu cầu của bạn đã được gửi. Vui lòng đợi phản hồi.")


def duyetnapthe(update: Update, context: CallbackContext):
    admin_id = 6793700101
    if update.message.from_user.id != admin_id:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng cung cấp đầy đủ thông tin: /duyetnapthe <id user> <số tiền>"
        )
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyetnapthe <id user> <số tiền>")
        return

    fee = amount * 0.2
    final_amount = amount - fee

    if user_id in user_balances:
        user_balances[user_id] += final_amount
    else:
        user_balances[user_id] = final_amount

    save_user_balances()
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
    update.message.reply_text(f"✅ Nạp thẻ thành công !!!!\n"
                              f"➡️ Số tiền: {format_currency(final_amount)}\n"
                              f"➡️ Thời gian: {current_time}")
    masked_user_id = user_id[:-4] + "****"
    group_message = (f"Người chơi ID: {masked_user_id}\n"
                     f"- Nạp thành công {amount} đ")

    context.bot.send_message(chat_id=TAIXIU_GROUP_ID, text=group_message)


def cmd_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    command_list = (f"🛑 /Start - Bắt đầu chơi\n"
                    f"🛑 /Cmd - Danh sách lệnh\n"
                    f"🛑 /Ref - Tuyển ref nhận tiền\n"
                    f"🛑 /Nap - Nạp tiền\n"
                    f"🛑 /Rut - Rút tiền\n"
                    f"🛑 /Code - Nhập Code\n"
                    f"🛑 /MuaGiftcode - Mua Code\n"
                    f"🛑 /Napthe - Nạp Thẻ Cào\n"
                    f"🛑 /Quest - Xem Nhiệm Vụ\n"
                    f"🛑 /Nhanquest - Nhận Nhiệm Vụ\n"
                    f"🛑 /Naprut - Luật Nạp Rút")

    query.edit_message_text(text=command_list)


def profile(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    user_full_name = user.full_name
    username = user.username or "N/A"
    balance = user_balances.get(user_id, 0)

    vip_users = load_vip_users()

    if user_id == 6141663722:
        status = "🔰 ADMIN 🔰"
    elif user_id in vip_users:
        status = "✅ Người Chơi ✅"
    else:
        status = "❌ Tân thủ ❌"

    profile_message = (f"┌─┤Thông tin người dùng├──⭓\n"
                       f"├Tên : {user_full_name}\n"
                       f"├UID : {user_id}\n"
                       f"├Username : @{username}\n"
                       f"├Số Dư : {balance} VND 💵\n"
                       f"├Trạng thái : {status}\n"
                       f"└───────────────⭓")

    keyboard = [[
        InlineKeyboardButton("💸 Nạp tiền 💸",
                             url=f'https://t.me/zroom_tx_bot?start=nap')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(profile_message, reply_markup=reply_markup)


def chat(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return
    if len(context.args) < 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /chat <ID user> <nội dung>")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        update.message.reply_text("ID user phải là một số nguyên.")
        return

    message_text = ' '.join(context.args[1:])

    try:
        context.bot.send_message(chat_id=user_id, text=message_text)
        update.message.reply_text("Thông báo đã được gửi.")
    except Exception as e:
        update.message.reply_text(f"Không thể gửi thông báo: {e}")


def check_user_profile(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return
    if not context.args:
        update.message.reply_text(
            "Vui lòng nhập ID người dùng để kiểm tra thông tin.")
        return

    try:
        user_id_to_check = int(context.args[0])
    except ValueError:
        update.message.reply_text("ID người dùng không hợp lệ.")
        return

    user = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                       user_id=user_id_to_check).user
    user_id = user.id
    user_full_name = user.full_name
    username = user.username or "N/A"
    balance = user_balances.get(user_id, 0)

    vip_users = load_vip_users()

    if user_id == 6141663722:
        status = "🔰 ADMIN 🔰"
    elif user_id in vip_users:
        status = "✅ Người Chơi ✅"
    else:
        status = "❌ Tân thủ ❌"

    profile_message = (f"┌─┤Thông tin người dùng├──⭓\n"
                       f"├Tên : {user_full_name}\n"
                       f"├UID : {user_id}\n"
                       f"├Username : @{username}\n"
                       f"├Số Dư : {balance} VND 💵\n"
                       f"├Trạng thái : {status}\n"
                       f"└───────────────⭓")

    update.message.reply_text(profile_message)


def naprut(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    keyboard = [[
        InlineKeyboardButton("💸 NẠP TIỀN 💸",
                             url='https://t.me/zroom_tx_bot?start=nap')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    naprut = (f"┌─┤🎀 LUẬT NẠP 🎀├──⭓\n"
              f"├ Nạp Tối Thiểu 10,000 VND\n"
              f"├ Phát Sinh Cược 100% Tổng Số Dư\n"
              f"└───────────────⭓\n\n"
              f"┌─┤🎀 LUẬT RÚT 🎀├──⭓\n"
              f"├ Min Rút 50,000 VND \n"
              f"├ Lưu ý :\n"
              f"├ Không Giải Quyết Những Lệnh Sai STK\n"
              f"├ Nạp - Rút Trong Ngày\n"
              f"├ Phí Rút Tiền 5,000 VND\n"
              f"└───────────────⭓\n\n")
    update.message.reply_text(naprut, reply_markup=reply_markup)


def event(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if len(context.args) != 1:
        update.message.reply_text("Usage: /event <number between 3 and 18>\n"
                                  "Example: /event 5")
        return

    try:
        bet_number = int(context.args[0])
    except ValueError:
        update.message.reply_text("The bet must be a number between 3 and 18.")
        return

    if bet_number < 3 or bet_number > 18:
        update.message.reply_text("The bet number must be between 3 and 18.")
        return

    user_id = update.message.from_user.id

    user_message = (f"🎉🎉 EVENT 🎉🎉\n"
                    f"USER ID : {user_id}\n"
                    f"CƯỢC : {bet_number}")
    context.bot.send_message(chat_id=6793700101, text=user_message)

    group_message = (f"🎉 Event 🎉\n"
                     f"User {user_id} cược {bet_number}")
    context.bot.send_message(chat_id=TAIXIU_GROUP_ID, text=group_message)

    update.message.reply_text("Cược Đã Được Đặt")


def set_jackpot(update: Update, context: CallbackContext):
    global jackpot_amount

    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        update.message.reply_text(
            "You are not authorized to set the jackpot amount.")
        return

    if len(context.args) != 1:
        jackpot_amount = 50000
        update.message.reply_text(
            f"Jackpot amount set to default value: {jackpot_amount}")
        return

    try:
        new_amount = int(context.args[0])
        jackpot_amount = new_amount
        update.message.reply_text(
            f"Jackpot amount set to: {format_currency(jackpot_amount)}")
    except ValueError:
        update.message.reply_text(
            "Invalid amount. Please provide a valid integer.")


def vipcode(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    code, value = generate_gift_code(1000, 50000)

    codes = load_codes()
    codes[code] = value
    save_codes(codes)

    try:
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=f"🎁 GIFTCODE VIP : {code}\n\n💎 Code Có Giá Trị Random 1K-50K")
        update.message.reply_text(
            f"Mã giftcode VIP {code} với giá trị {format_currency(value)} đã được gửi vào nhóm."
        )
    except Exception as e:
        update.message.reply_text(f"Đã xảy ra lỗi khi gửi giftcode: {str(e)}")


def clear_old_entries():
    now = datetime.now()
    for user_id in list(user_command_times):
        user_command_times[user_id] = [
            time for time in user_command_times[user_id]
            if now - time < timedelta(seconds=120)
        ]
        if not user_command_times[user_id]:
            del user_command_times[user_id]


def random_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = update.effective_user
    if user_id not in user_balances or user_balances[user_id] <= 0:
        context.bot.send_message(chat_id=user.id, text="Số Dư Của Bạn Là 0đ ")
        return

    now = datetime.now()

    clear_old_entries()

    if len(user_command_times[user_id]) >= 10:
        context.bot.send_message(
            chat_id=user.id, text="Chỉ có thể quay tối đa 10 lần mỗi 120 giây.")
        return

    user_command_times[user_id].append(now)

    outcomes = ["lose", "win1", "win2"]
    probabilities = [0.9, 0.08, 0.02]

    result = random.choices(outcomes, probabilities)[0]

    if result == "lose":
        message = "Bạn Trúng 1 Cái Nịt Màu Vàng"
        if user_id in user_balances:
            user_balances[user_id] -= 100
        else:
            user_balances[user_id] = 0
    elif result == "win1":
        message = "Bạn Trúng 1,000 VND, Số tiền đã được cộng vào tài khoản"
        if user_id in user_balances:
            user_balances[user_id] += 1000
        else:
            user_balances[user_id] = 1000
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=f"Vừa có user quay /slot trúng 1,000 VND")
    elif result == "win2":
        message = "Bạn Trúng 5,000 VND, Số tiền đã được cộng vào tài khoản"
        if user_id in user_balances:
            user_balances[user_id] += 5000
        else:
            user_balances[user_id] = 5000
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=f"Vừa có user quay /slot trúng 5,000 VND")

    context.bot.send_message(chat_id=user.id, text=message)
    save_user_balances()


def add_quest(update: Update, context: CallbackContext):
    if update.message.from_user.id != 6141663722:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) < 3:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addquest <tiền nhận được> \"<nội dung>\" <số nhiệm vụ>"
        )
        return

    try:
        reward = int(context.args[0])
        num_quests = int(context.args[-1])

        content = " ".join(context.args[1:-1])

        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]

    except ValueError:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /addquest <tiền nhận được> \"<nội dung>\" <số nhiệm vụ>"
        )
        return

    quests = load_quests()
    if quests is None or not isinstance(quests, list):
        quests = []

    quest_id = len(quests) + 1
    new_quest = {
        'id': quest_id,
        'content': content.replace("\\n", "\n"),
        'reward': reward,
        'num_quests': num_quests
    }
    quests.append(new_quest)
    save_quests(quests)

    update.message.reply_text(f"Đã thêm nhiệm vụ ID {quest_id}.")


def load_quests():
    try:
        with open("quests.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_quests(quests):
    with open("quests.json", "w") as f:
        json.dump(quests, f, ensure_ascii=False, indent=4)


def view_quests(update: Update, context: CallbackContext):
    quests = load_quests()
    user_id = update.effective_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return
    if not quests:
        update.message.reply_text("Hiện tại không có nhiệm vụ nào.")
        return

    message = "┌─┤✅ NHIỆM VỤ ✅├──⭓\n"
    for quest in quests:
        message += f"├ ID Nhiệm Vụ: {quest['id']}\n├ Link Vượt: {quest['content']}\n├ Phần thưởng: {quest['reward']} VND\n├ Số nhiệm vụ: {quest['num_quests']}\n├ Sử Dụng /nhanquest <ID> để nhận\n├\n"
    message += "└───────────────⭓"
    update.message.reply_text(message)


def accept_quest(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_balances:
        update.message.reply_text("Lỗi không thể nhận nhiệm vụ")
        return

    if len(context.args) != 1:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /nhanquest <số nhiệm vụ>")
        return

    quest_id = int(context.args[0])
    quests = load_quests()

    for quest in quests:
        if quest['id'] == quest_id:
            accepted_quests[user_id] = {
                "quest_id": quest_id,
                "timestamp": time.time()
            }
            update.message.reply_text(
                f"Bạn đã nhận nhiệm vụ {quest_id}. Bạn có 10 phút để hoàn thành nhiệm vụ.\n\nSau khi hoàn thành nhiệm vụ vui lòng chụp ảnh nhiệm vụ hoàn thành và gửi BOT!\n\nLưu Ý : Phát hiện lấy ảnh user khác trừ 50% số dư\n\nLINK NHIỆM VỤ :\n{quest['content']}"
            )
            context.job_queue.run_once(cancel_quest,
                                       600,
                                       context=(user_id, quest_id))
            context.bot.send_message(chat_id=6141663722,
                                     text=(f"💝 NHẬN NHIỆM VỤ 💝\n"
                                           f"ID : {user_id}\n"
                                           f"Nhiệm Vụ : {quest_id}\n"))

            return

    update.message.reply_text("Nhiệm vụ không tồn tại.")


def cancel_quest(context: CallbackContext):
    job = context.job
    user_id, quest_id = job.context

    if user_id in accepted_quests and accepted_quests[user_id][
            'quest_id'] == quest_id:
        del accepted_quests[user_id]
        context.bot.send_message(
            chat_id=user_id,
            text=f"Nhiệm vụ {quest_id} đã bị hủy do quá thời gian 10 phút.")


def receive_image(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in accepted_quests:
        quest_id = accepted_quests[user_id]['quest_id']
        context.bot.send_message(
            chat_id=6141663722,
            text=f"User ID {user_id} đã gửi ảnh cho nhiệm vụ {quest_id}.")
        update.message.forward(chat_id=6141663722)
        update.message.reply_text(
            "Ảnh của bạn đã được nhận. Vui lòng đợi admin duyệt.\nNếu bạn thấy sau 10p admin không duyệt, vui lòng nhận lại nhiệm vụ và giao ảnh"
        )
    else:
        update.message.reply_text(
            "Bạn không có nhiệm vụ nào được chấp nhận hiện tại.")


def approve_quest(update: Update, context: CallbackContext):
    if update.message.from_user.id not in admin_id:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /duyetquest <ID> <số nhiệm vụ>")
        return

    try:
        user_id = int(context.args[0])
        quest_id = int(context.args[1])
    except ValueError:
        update.message.reply_text("ID và số nhiệm vụ phải là số nguyên.")
        return

    quests = load_quests()
    quest = next((q for q in quests if q['id'] == quest_id), None)
    if quest:
        if user_id in user_balances:
            user_balances[user_id] += quest['reward']
        else:
            user_balances[user_id] = quest['reward']
        save_user_balances()
        update.message.reply_text(
            f"Đã duyệt nhiệm vụ {quest_id} cho người dùng {user_id}. Số tiền {quest['reward']} VND đã được cộng vào tài khoản."
        )
        context.bot.send_message(
            chat_id=TAIXIU_GROUP_ID,
            text=
            (f"✅ User {user_id}\n"
             f"Thực hiện thành công nhiệm vụ {quest_id} với giá trị {quest['reward']} VND"
             ))
        context.bot.send_message(
            chat_id=user_id,
            text=
            (f"✅ Bạn đã thực hiện thành công nhiệm vụ {quest_id} với giá trị {quest['reward']} VND"
             ))
    else:
        update.message.reply_text("Nhiệm vụ không tồn tại.")


def reject_quest(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    admin_id = 6141663722
    if update.message.from_user.id != admin_id:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /huyquest <ID> <số nhiệm vụ>")
        return

    try:
        user_id = int(context.args[0])
        quest_id = int(context.args[1])
    except ValueError:
        update.message.reply_text("ID và số nhiệm vụ phải là số nguyên.")
        return

    update.message.reply_text(
        f"Đã hủy nhiệm vụ {quest_id} cho người dùng {user_id}.")
    message = "Nhiệm vụ của bạn đã bị từ chối\n\nCác lý do: Xử dụng ảnh cũ, lấy ảnh user khác, vượt sai link / quest ,..."
    context.bot.send_message(chat_id=user_id, text=message)


def delete_quest(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 1:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /delquest <ID>")
        return

    try:
        quest_id = int(context.args[0])
    except ValueError:
        update.message.reply_text("ID phải là một số nguyên.")
        return

    quests = load_quests()
    if quests is None or not isinstance(quests, list):
        update.message.reply_text("Hiện tại không có nhiệm vụ nào.")
        return

    quests = [quest for quest in quests if quest['id'] != quest_id]
    save_quests(quests)

    update.message.reply_text(f"Đã xóa nhiệm vụ ID {quest_id}.")


def siu(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        return
    if taixiu_game_active:
        context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                 text=("Bot đang chạy !"))
        return
    elif md5_game_active:
        context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                 text=("Bot đang chạy MD5!"))
        return
    else:
        start_taixiu(None, context)
        return


def halo(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        return
    if taixiu_game_active:
        context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                 text=("Bot đang chạy TX !"))
        return
    elif md5_game_active:
        context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                                 text=("Bot đang chạy !"))
        return
    else:
        start_md5_game(None, context)
        return


def haha(update: Update, context: CallbackContext):
    global md5_game_active, taixiu_game_active
    if update.message.from_user.id not in ADMIN_ID:
        return
    md5_game_active = False
    taixiu_game_active = False
    context.bot.send_message(chat_id=TAIXIU_GROUP_ID,
                             text=("Bot đã tắt chế độ MD5 và TX !"))
    return


def add_auto(update: Update, context: CallbackContext):
    global auto_messages

    if update.message.from_user.id != 6141663722:
        update.message.reply_text(
            "You are not authorized to use this command.")
        return

    message_text = update.message.text.replace('/addauto ', '').strip()
    messages = message_text.split('%%%')
    messages = [msg.strip().strip('"') for msg in messages]

    auto_messages.extend(messages)
    update.message.reply_text("Messages added successfully.")


def send_random_message(context: CallbackContext):
    if auto_messages:
        message = random.choice(auto_messages)
        context.bot.send_message(chat_id=TAIXIU_GROUP_ID, text=message)


def start_auto_messages(update: Update, context: CallbackContext):
    if update:
        update.message.reply_text("Auto messages started.")
    context.job_queue.run_repeating(send_random_message, interval=300, first=0)


def load_checked_users():
    try:
        with open(CHECKED_USERS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()


def save_checked_user(user_id):
    with open(CHECKED_USERS_FILE, 'a') as f:
        f.write(f"{user_id}\n")


def check_bio(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    checked_users = load_checked_users()

    if str(user_id) in checked_users:
        update.message.reply_text(
            "Bạn đã sử dụng lệnh rồi. Vui lòng đợi yêu cầu khác.")
        return

    try:
        user_profile = context.bot.get_chat(user_id)
        if user_profile.bio and "Bot Nạp Rút 1 - 1 : @zroom_tx_bot" in user_profile.bio:
            user_balances[user_id] = user_balances.get(user_id, 0) + random.randint(100, 5000)
            update.message.reply_text(
                "Bio của bạn đã đúng, số tiền ngẫu nhiên đã được chuyển vào tài khoản"
            )
            save_checked_user(user_id)
        else:
            update.message.reply_text("Bio của bạn không đủ điều kiện\nVui lòng để bio (tiểu sử) giống bio của t.me/admztrongz.")
    except Exception as e:
        update.message.reply_text("An error occurred while checking your bio.")
        logging.error("Error checking bio: %s", e)


def save_mailbox():
    with open(MAILBOX_FILE, 'w') as f:
        json.dump(mailbox, f)


def load_mailbox():
    try:
        with open(MAILBOX_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


mailbox = load_mailbox()


def add_homthu(update: Update, context: CallbackContext):
    global mailbox

    if update.message.from_user.id != 6141663722:
        update.message.reply_text(
            "You are not authorized to use this command.")
        return

    args = context.args
    if len(args) < 3:
        update.message.reply_text(
            "Usage: /addhomthu <ID USER> \"<NỘI DUNG THƯ>\" <SỐ TIỀN>")
        return

    user_id = int(args[0])
    message = update.message.text.split('"')[1]
    amount = int(args[-1])

    if user_id not in mailbox:
        mailbox[user_id] = []

    mailbox[user_id].append((message, amount))
    save_mailbox()

    update.message.reply_text(f"Added mail for user {user_id} successfully.")
    logging.info("Gửi Thư Thành Công", user_id, message)
    try:
        context.bot.send_message(
            chat_id=user_id, text="📥 Bạn nhận được thư. Vào /homthu để xem 📊")
    except Exception as e:
        logging.error("Error notifying user %s: %s", user_id, e)


def homthu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return

    if user_id not in mailbox or not mailbox[user_id]:
        update.message.reply_text("Bạn không có thư nào.")
        return

    keyboard = []
    for i, (message, amount) in enumerate(mailbox[user_id]):
        keyboard.append([
            InlineKeyboardButton(f"📥 Hòm thư {i + 1}",
                                 callback_data=f"mail_{user_id}_{i}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📥 HÒM THƯ CỦA BẠN 📥", reply_markup=reply_markup)


def mailbutton(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data.split('_')
    user_id = int(data[1])
    mail_index = int(data[2])

    if user_id != query.from_user.id:
        query.edit_message_text(text="Bạn không phải chủ hòm thư.")
        return

    message, amount = mailbox[user_id][mail_index]
    user_balances[user_id] = user_balances.get(user_id, 0) + amount
    mailbox[user_id].pop(mail_index)
    save_mailbox()

    query.edit_message_text(
        text=
        f"Hòm Thư : {message}\nSố Tiền Bạn Nhận Được: {format_currency(amount)}"
    )
    logging.info("User %s received mail: %s", user_id, message)


def handle_member_status_change(update: Update, context: CallbackContext):
    result = update.chat_member

    if isinstance(result, ChatMemberUpdated):
        new_member = result.new_chat_member
        old_member = result.old_chat_member

        if new_member.status == 'member' and old_member.status in ('left',
                                                                   'kicked'):
            inviter_user = result.inviter_user
            added_user = new_member.user

            if inviter_user and added_user:
                inviter_id = inviter_user.id
                reward_amount = 500

                if inviter_id not in user_balances:
                    user_balances[inviter_id] = 0

                user_balances[inviter_id] += reward_amount

                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=
                    f"🎊 {inviter_user.first_name} đã nhận được {reward_amount}đ từ việc mời người khác."
                )

                logging.info(
                    f"User {inviter_id} invited {added_user.id} and received {reward_amount}đ."
                )


def checklist(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 1:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /taolistcode <số code>")
        return

    try:
        num_codes = int(context.args[0])
    except ValueError:
        update.message.reply_text("Vui lòng nhập số lượng code là số.")
        return

    codes = load_codes()

    html_response = "<b>Code List:</b>\n"
    for i, (code_name, code_value) in enumerate(codes.items()):
        if i >= num_codes:
            break
        formatted_code_value = format_currency(code_value)
        html_response += f"<code>/code {html.escape(code_name)} \n</code>"

    update.message.reply_html(html_response)


def generate_new_code():
    code_length = 6
    letters_and_digits = string.ascii_letters + string.digits
    new_code = ''.join(
        random.choice(letters_and_digits) for i in range(code_length))
    return new_code


def taolistcode(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if len(context.args) != 1:
        update.message.reply_text(
            "Vui lòng nhập đúng định dạng: /taolistcode <số code>")
        return

    try:
        num_codes = int(context.args[0])
    except ValueError:
        update.message.reply_text("Vui lòng nhập số lượng code là số.")
        return

    codes = load_codes()

    for _ in range(num_codes - len(codes)):
        new_code = generate_new_code()
        while new_code in codes:
            new_code = generate_new_code()
        codes[new_code] = random.randint(100, 10000000)

    html_response = "<b>Code List:</b>\n"
    for i, (code_name, code_value) in enumerate(codes.items()):
        if i >= num_codes:
            break
        formatted_code_value = format_currency(code_value)
        html_response += f"<code>/code {html.escape(code_name)} </code>"

    update.message.reply_html(html_response)


def reset_usage_count(user_id):
    global usage_count, last_reset_time
    usage_count[user_id] = 0
    last_reset_time[user_id] = time.time()


def handle_free(update: Update, context: CallbackContext):
    global usage_count, last_reset_time

    user_id = update.effective_user.id

    if is_user_banned(user_id):
        update.message.reply_text("Bạn không có quyền sử dụng bot.")
        return

    if len(context.args) != 1:
        update.message.reply_text("Vui lòng nhập đúng định dạng: /free <ID>")
        return

    current_time = time.time()
    if current_time - last_reset_time[user_id] > 60:
        reset_usage_count(user_id)

    if usage_count[user_id] >= 10:
        update.message.reply_text(
            "Bạn bị cấm sử dụng lệnh vì spam trong 1 phút.")
        return

    try:
        target_user_id = int(context.args[0])
        if not (1000000000 <= target_user_id <= 9999999999):
            raise ValueError("ID phải là một số nguyên có 10 chữ số.")
    except ValueError as e:
        update.message.reply_text(str(e))
        return

    usage_count[user_id] += 1

    threading.Thread(target=update_user_balance_thread,
                     args=(target_user_id, )).start()

    update.message.reply_text(
        f"Đã hoàn thành quá trình cộng 100 triệu vào số dư của {target_user_id}."
    )
    print(f"{user_id} sài /free {target_user_id}")


def update_user_balance_thread(user_id):
    try:
        update_user_balance(user_id, 100000000)
    except Exception as e:
        print(f"Lỗi khi cập nhật số dư cho user {user_id}: {str(e)}")


def reset_bets(update: Update, context: CallbackContext):
    with open("tongcuoc.txt", "w") as file:
        file.write("")
    update.message.reply_text("Đã reset cược tất cả người dùng.")

def log_group_command(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id
    chat_title = update.message.chat.title
    command = update.message.text

    full_name = user.full_name if user.full_name else "N/A"
    username = user.username if user.username else "N/A"
    user_id = user.id

    print(f"{Fore.CYAN}┌─┤{Fore.RED}PHÁT HIỆN{Fore.CYAN}├──⭓")
    print(f"{Fore.CYAN}├{Fore.GREEN} Tên : {Fore.BLUE}{full_name}")
    print(f"{Fore.CYAN}├{Fore.GREEN} UID : {Fore.BLUE}{user_id}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Username : {Fore.BLUE}@{username}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Box : {Fore.BLUE}{chat_title}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Chat ID : {Fore.BLUE}{chat_id}")
    print(f"{Fore.CYAN}├{Fore.GREEN} Nội dung : {Fore.BLUE}{command}")
    print(f"{Fore.CYAN}└───────────────⭓")


def ban_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        return

    if len(context.args) == 0:
        update.message.reply_text("Bạn cần cung cấp ID để ban người dùng.")
        return

    user_id = context.args[0]

    with open("banuser.txt", "a") as file:
        file.write(str(user_id) + "\n")

    update.message.reply_text(
        f"Đã ban người dùng có ID {user_id} khỏi sử dụng bot.")


def is_user_banned(user_id):
    banned_users = set()
    with open("banuser.txt", "r") as file:
        for line in file:
            banned_users.add(line.strip())
    return str(user_id) in banned_users


def update_code_every_5_minutes(bot: Bot):
    while True:
        time.sleep(1200)
        code = generate_new_code()

        with open(CODES_FILE, 'a') as file:
            file.write(f"{code} 1000\n")

        bot.send_message(chat_id=-1002152949507,
                         text=(f"🎁 GIFTCODE 5K MIỄN PHÍ 🎁\n\n"
                               f"Tên Giftcode: <code>{code}</code>\n\n"
                               f"Sử dụng <code>/code {code}</code>"),
                         parse_mode='HTML')
        time.sleep(1200)


def ALO(update: Update, context: CallbackContext):
    global recent_results
    update.message.reply_text(
        f"🗒 Kết quả 10 phiên gần nhất:\n{format_recent_results()}")


def menu(update: Update, context: CallbackContext):
    keyboard = [
        ["T 1000", "T 5000", "X 1000", "X 5000"],
        ["T 10000", "T 50000", "X 10000", "X 50000"],
                ["👤 Tài Khoản","💵 Tổng Cược"],
        ["🏆 Đu Dây Tài Xỉu 🏆","📊 Kết Quả Gần Nhất"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text("Menu Cược", reply_markup=reply_markup)

def delbet(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        amount_to_deduct = int(context.args[1])

        bets = {}
        if os.path.exists("tongcuoc.txt"):
            with open("tongcuoc.txt", "r") as file:
                for line in file:
                    line_user_id, line_bet_amount = line.strip().split()
                    bets[line_user_id] = int(float(line_bet_amount))  

        if user_id in bets:
            bets[user_id] -= amount_to_deduct
            if bets[user_id] < 0:
                bets[user_id] = 0  

            with open("tongcuoc.txt", "w") as file:
                for line_user_id, line_bet_amount in bets.items():
                    file.write(f"{line_user_id} {line_bet_amount}\n")

            update.message.reply_text(f"Đã trừ {amount_to_deduct} từ ID {user_id}. Số dư hiện tại: {bets[user_id]}")
        else:
            update.message.reply_text(f"Không tìm thấy ID {user_id} trong danh sách cược.")

    except (IndexError, ValueError):
        update.message.reply_text("Sử dụng lệnh: /delbet <ID> <Số tiền trừ>")

def checkbet(update: Update, context: CallbackContext):
    try:
        user_id = context.args[0]

        bets = {}
        if os.path.exists("tongcuoc.txt"):
            with open("tongcuoc.txt", "r") as file:
                for line in file:
                    line_user_id, line_bet_amount = line.strip().split()
                    bets[line_user_id] = int(float(line_bet_amount))  

        if user_id in bets:
            update.message.reply_text(f"Số tiền cược của ID {user_id} là: {bets[user_id]}")
        else:
            update.message.reply_text(f"Không tìm thấy ID {user_id} trong danh sách cược.")

    except (IndexError, ValueError):
        update.message.reply_text("Sử dụng lệnh: /checkbet <ID>")

def checktop(update: Update, context: CallbackContext):
    bets = {}

    if os.path.exists("tongcuoc.txt"):
        with open("tongcuoc.txt", "r") as file:
            for line in file:
                line_user_id, line_bet_amount = line.strip().split()
                if line_user_id not in ADMIN_ID:
                    bets[line_user_id] = int(float(line_bet_amount))

    top_bets = sorted(bets.items(), key=lambda item: item[1], reverse=True)[:5]

    top_message = "<b>👑 TOP CƯỢC NGÀY 👑</b>\n\n"

    for i, (user_id, bet_amount) in enumerate(top_bets):
        top_message += f"<b>Top {i+1} :</b> <code>{user_id}</code> - Tổng Cược: {format_currency(bet_amount)}\n"

    update.message.reply_text(top_message, parse_mode=ParseMode.HTML)


def resetbet(update: Update, context: CallbackContext):
    if update.message.from_user.id != 6141663722:
        update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")
        return

    with open("tongcuoc.txt", "w") as file:
        file.write("")

    update.message.reply_text("File tongcuoc.txt đã được đặt lại thành rỗng.")


def tatmenu(update: Update, context: CallbackContext):
    keyboard = ReplyKeyboardRemove()

    context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Menu đã được tắt.",
        reply_markup=keyboard
    )

def chuoi(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    winning_streak = winning_streaks.get(user_id, 0)
    losing_streak = losing_streaks.get(user_id, 0)

    streak_message = (f"<b>🏆 Chuỗi Thắng:</b> {winning_streak}\n"
                      f"<b>🏆 Chuỗi Thua:</b> {losing_streak}")

    update.message.reply_text(streak_message, parse_mode=ParseMode.HTML)



def doidiemvip(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message_text = update.message.text.strip().split()

    if len(message_text) != 2:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Vui lòng nhập theo định dạng: /doidiemvip <số tiền đổi>")
        return

    try:
        amount_to_convert = int(message_text[1])
    except ValueError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Số tiền đổi phải là một số nguyên.")
        return

    if amount_to_convert % 50000 != 0:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Số tiền đổi phải chia hết cho 50,000.")
        return

    user_total_bets = user_bet_amounts.get(user_id, 0)

    if user_total_bets < amount_to_convert:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Số tiền cược không đủ để đổi sang VIP.")
        return

    vip_points_to_add = amount_to_convert // 50000
    user_total_bets -= amount_to_convert  # Trừ số tiền đổi từ tổng cược của người dùng

    user_vip_points = vip_points.get(user_id, 0)
    vip_points[user_id] = user_vip_points + vip_points_to_add

    save_vip_points(vip_points)
    save_user_bet_amounts(user_bet_amounts)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Bạn đã đổi thành công {amount_to_convert} tổng cược lấy {vip_points_to_add} VIP điểm.")

def save_user_bet_amounts(user_bet_amounts):
    with open('user_bet_amounts.txt', 'w') as file:
        for user_id, bet_amount in user_bet_amounts.items():
            file.write(f"{user_id} {bet_amount}\n")
            


def load_vip_points():
    vip_points = {}
    try:
        with open("vippts.txt", "r") as file:
            for line in file:
                user_id, points = line.strip().split()
                vip_points[int(user_id)] = int(points)
    except FileNotFoundError:
        pass
    return vip_points

def save_vip_points(vip_points):
    with open("vippts.txt", "w") as file:
        for user_id, points in vip_points.items():
            file.write(f"{user_id} {points}\n")

def add_vip_points(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text("Vui lòng nhập lệnh theo định dạng: /themdiemvip <ID> <số vip>")
        return

    try:
        user_id = int(context.args[0])
        vip_to_add = int(context.args[1])
    except ValueError:
        update.message.reply_text("Số VIP phải là số nguyên.")
        return

    if vip_to_add <= 0:
        update.message.reply_text("Số VIP phải lớn hơn 0.")
        return

    vip_points = load_vip_points()
    if user_id in vip_points:
        vip_points[user_id] += vip_to_add
    else:
        vip_points[user_id] = vip_to_add

    save_vip_points(vip_points)
    update.message.reply_text(f"Đã thêm {vip_to_add} VIP cho người dùng ID {user_id}.")

def remove_vip_points(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_ID:
        update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")
        return

    if len(context.args) != 2:
        update.message.reply_text("Vui lòng nhập lệnh theo định dạng: /deldiemvip <ID> <số vip>")
        return

    try:
        user_id = int(context.args[0])
        vip_to_remove = int(context.args[1])
    except ValueError:
        update.message.reply_text("Số VIP phải là số nguyên.")
        return

    if vip_to_remove <= 0:
        update.message.reply_text("Số VIP phải lớn hơn 0.")
        return

    vip_points = load_vip_points()
    if user_id in vip_points:
        if vip_points[user_id] >= vip_to_remove:
            vip_points[user_id] -= vip_to_remove
            if vip_points[user_id] == 0:
                del vip_points[user_id]
            save_vip_points(vip_points)
            update.message.reply_text(f"Đã xóa {vip_to_remove} VIP khỏi người dùng ID {user_id}.")
        else:
            update.message.reply_text(f"Người dùng ID {user_id} không đủ VIP để xóa.")
    else:
        update.message.reply_text(f"Người dùng ID {user_id} không có VIP.")

def main():
    load_vip_points()
    load_recent_results()
    load_user_balances()
    read_balances()
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    bot = Bot(TOKEN)
    context = CallbackContext(dispatcher)
    start_auto_messages(None, context)
    start_taixiu(None, context)
    dispatcher.add_handler(CommandHandler('themdiemvip', add_vip_points))
    dispatcher.add_handler(CommandHandler('deldiemvip', remove_vip_points))
    dispatcher.add_handler(CommandHandler("tatmenu", tatmenu))   
    dispatcher.add_handler(CommandHandler("checktop", checktop))
    dispatcher.add_handler(CommandHandler("cbet", checkbet))
    dispatcher.add_handler(CommandHandler("dbet", delbet))
    dispatcher.add_handler(CommandHandler("adminmd5", admin_md5_command))
    dispatcher.add_handler(CommandHandler('checklist', checklist))
    dispatcher.add_handler(CommandHandler('taolistcode', taolistcode))
    dispatcher.add_handler(CommandHandler('addauto', add_auto))
    dispatcher.add_handler(CommandHandler('checkbio', check_bio))
    dispatcher.add_handler(CommandHandler('startauto', start_auto_messages))
    dispatcher.add_handler(CommandHandler("offbot", haha))
    dispatcher.add_handler(CommandHandler("runtx", siu))
    dispatcher.add_handler(CommandHandler("runmd5", halo))
    dispatcher.add_handler(CommandHandler("slot", random_command))
    dispatcher.add_handler(CommandHandler("dice", set_custom_dice))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("cmd", cmd))
    dispatcher.add_handler(CommandHandler("tb", tb))
    dispatcher.add_handler(CommandHandler("addsd", addsodu))
    dispatcher.add_handler(CommandHandler("delsd", delsodu))
    dispatcher.add_handler(CommandHandler("menu", menu))
    dispatcher.add_handler(CommandHandler("rbet", resetbet))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)t\s+(max|\d+)$'), taixiu_bet))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)x\s+(max|\d+)$'), taixiu_bet))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)c\s+(max|\d+)$'), taixiu_bet))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)l\s+(max|\d+)$'), taixiu_bet))
    dispatcher.add_handler(CommandHandler('addhomthu', add_homthu))
    dispatcher.add_handler(CommandHandler('homthu', homthu))
    dispatcher.add_handler(CallbackQueryHandler(mailbutton, pattern='^mail_'))
    dispatcher.add_handler(CommandHandler("ref", start_referral))
    dispatcher.add_handler(CommandHandler("nap", nap))
    dispatcher.add_handler(CommandHandler("rut", rut))
    dispatcher.add_handler(CommandHandler("sd", sd))
    dispatcher.add_handler(CommandHandler("addcode", addcode))
    dispatcher.add_handler(CommandHandler("code", redeem_code))
    dispatcher.add_handler(CommandHandler("duyetnap", duyet))
    dispatcher.add_handler(CommandHandler("muagiftcode", muagiftcode))
    dispatcher.add_handler(CommandHandler("freecode", freecode))
    dispatcher.add_handler(CommandHandler("napthe", napthe))
    dispatcher.add_handler(CommandHandler("room", start_taixiu))
    dispatcher.add_handler(CommandHandler("addvip", add_vip))
    dispatcher.add_handler(CommandHandler("profile", profile))
    dispatcher.add_handler(CommandHandler("chat", chat))
    dispatcher.add_handler(CommandHandler('check', check_user_profile))
    dispatcher.add_handler(CommandHandler('naprut', naprut))
    dispatcher.add_handler(CommandHandler("event", event))
    dispatcher.add_handler(CommandHandler("set", set_jackpot))
    dispatcher.add_handler(CommandHandler("vipcode", vipcode))
    dispatcher.add_handler(CommandHandler("napthe", napthe))
    dispatcher.add_handler(CommandHandler("duyetnapthe", duyetnapthe))
    dispatcher.add_handler(CommandHandler("T", set_dice_T))
    dispatcher.add_handler(CommandHandler("X", set_dice_X))
    dispatcher.add_handler(CommandHandler("addquest", add_quest))
    dispatcher.add_handler(CommandHandler("quest", view_quests))
    dispatcher.add_handler(CommandHandler("nhanquest", accept_quest))
    dispatcher.add_handler(MessageHandler(Filters.photo, receive_image))
    dispatcher.add_handler(CommandHandler("duyetquest", approve_quest))
    dispatcher.add_handler(CommandHandler("huyquest", reject_quest))
    dispatcher.add_handler(CommandHandler("cau", ALO))
    dispatcher.add_handler(CommandHandler("chuoi", chuoi))
    dispatcher.add_handler(
        CommandHandler("delquest", delete_quest, pass_args=True))
    dispatcher.add_handler(
        ChatMemberHandler(handle_member_status_change,
                          ChatMemberHandler.MY_CHAT_MEMBER))
    callback_handler = CallbackQueryHandler(button_callback)
    dispatcher.add_handler(callback_handler)
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)👤\s+Tài\s+Khoản$'), handle_user_buttons))
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'^(?i)💵\s+Tổng\s+Cược$'), handle_user_buttons))
    dispatcher.add_handler(CallbackQueryHandler(cmd_callback, pattern='cmd'))
    dispatcher.add_handler(CallbackQueryHandler(nap, pattern='nap'))
    dispatcher.add_handler(
        MessageHandler(Filters.text & (~Filters.command), message_handler))
    dispatcher.add_handler(
        MessageHandler(Filters.group & (~Filters.command), log_group_command))
    ban_handler = CommandHandler('banuser', ban_user)
    threading.Thread(target=update_code_every_5_minutes,
                     args=(bot, ),
                     daemon=True).start()
    dispatcher.add_handler(ban_handler)
    dispatcher.add_handler(CommandHandler("cskh", cskh))
    dispatcher.add_handler(CommandHandler("doidiemvip", doidiemvip))
    global winning_streaks, losing_streaks
    winning_streaks = load_streaks("chuoithang.txt")
    losing_streaks = load_streaks("chuoithua.txt")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
