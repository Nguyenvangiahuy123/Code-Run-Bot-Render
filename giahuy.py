import telebot
from telebot import types
import os
import json
from datetime import datetime
import hashlib
import requests
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time
import random
from keep_alive import keep_alive

api_kiemtien = "8019157808:AAEkKK4FXSIcZoVElmMswho8fkUpUO8f8jc"
bot = telebot.TeleBot(api_kiemtien)
ADMIN_IDS = [7719131045]

dilink = types.InlineKeyboardMarkup()
btn1 = types.InlineKeyboardButton("Dilink", callback_data="dilink")
dilink.add(btn1)

yeumoney = types.InlineKeyboardMarkup()
btn2 = types.InlineKeyboardButton("Yeumoney", callback_data="yeumoney")
yeumoney.add(btn2)
btn3 = types.InlineKeyboardButton("Link4m", callback_data="link4m")
yeumoney.add(btn3)
user_data = 'user_data.json'
# Kết hợp các nút từ dilink và yeumoney vào một InlineKeyboardMarkup
gopbutton = types.InlineKeyboardMarkup()
gopbutton.add(btn1, btn2, btn3)

sotien_muonrut = 100000


keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Tài Khoản"), KeyboardButton("Admin"))
keyboard.add(KeyboardButton("Rút Gọn Link"), KeyboardButton("Rút Tiền"))
keyboard.add(KeyboardButton("Hoa Hồng Các Link")),


def TimeStamp():
    now = datetime.now().strftime('%d-%m-%Y')
    return now


# Đường dẫn đến file lưu trữ dữ liệu người dùng
USER_DATA_FILE = 'user_data.json'
USED_KEYS_FILE = 'used_key.json'
used_keys = {}
def read_used_keys():
    global used_keys
    if os.path.exists(USED_KEYS_FILE):
        with open(USED_KEYS_FILE, 'r') as f:
            try:
                used_keys = json.load(f)
            except json.JSONDecodeError:
                used_keys = {}
    else:
        used_keys = {}
# Biến toàn cục để lưu trữ dữ liệu người dùng
user_data = {}
used_keys = {}
# Hàm đọc dữ liệu từ file
def read_user_data():
    global user_data
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            try:
                user_data = json.load(f)
            except json.JSONDecodeError:
                user_data = {}
    else:
        user_data = {}

# Hàm lưu dữ liệu vào file
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Hàm cập nhật số dư người dùng
def update_user_balance(user_id, amount):
    global user_data
    # Kiểm tra và đảm bảo user_data là từ điển
    if not isinstance(user_data, dict):
        user_data = {}

    if str(user_id) in user_data:
        user_data[str(user_id)]['balance'] += amount
    else:
        user_data[str(user_id)] = {'balance': amount}

    # Sau khi cập nhật, lưu lại dữ liệu
    save_user_data(user_data)

# Đọc dữ liệu từ file khi khởi động chương trình
read_user_data()
def save_used_keys(data):
    with open(USED_KEYS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Đọc dữ liệu khi khởi động bot
read_user_data()
read_used_keys()
# Các phần khác của code bot...

def get_balance(user_id):
    global user_data
    return user_data.get(str(user_id), {}).get('balance', 0)

# Đọc dữ liệu từ file khi khởi động chương trình
read_user_data()

@bot.message_handler(commands=["start"])
def start_commands(message):
    bot.reply_to(message, f"Xin Chào Đây Là Bot Kiếm Tiền Thông Qua Link Rút Gọn\nSelect 1 Trong 2 Link Ở Dưới Để Rút Gọn", reply_markup=keyboard)
    
@bot.message_handler(func=lambda message: message.text == "Rút Gọn Link")
def kiemtien_text(message):
    bot.reply_to(message, f"Các Link Rút Gọn Để Kiếm Tiềnn\nAll Link Rút Gọn Ở Dưới", reply_markup=gopbutton)







# Biến toàn cục để lưu key
key_ghe = ''

@bot.callback_query_handler(func=lambda call: call.data == "yeumoney")
def callback_query(call):
    global key_ghe  # Sử dụng global để có thể thay đổi giá trị của biến key_ghe
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Vui Lòng Đợi Trong Giây Lát!')

    username = call.from_user.username
    abcxyz = "qwertyuiopasdfghjklzxcvbnm1234567890"

    # Tạo key từ username, thời gian hiện tại và một phần ngẫu nhiên
    current_time = str(int(time.time()))  # Lấy thời gian hiện tại và chuyển đổi thành chuỗi
    random_part = ''.join(random.choices(abcxyz, k=8))  # Chuỗi ngẫu nhiên
    string = f'yeumoney-{username}+{current_time}+{random_part}'
    
    # Tạo key từ chuỗi string
    hash_object = hashlib.md5(string.encode())
    key_ghe = str(hash_object.hexdigest())
    print(key_ghe)

    url_api = "yeumoney.com"
    token_api = "eee97ade0e7401a23d12ce61158be94906f9f098c9b7f9c2599e50bb6a7ef5c3"
    
    # Thực hiện yêu cầu GET tới API và kiểm tra phản hồi
    response = requests.get(f'https://yeumoney.com/QL_api.php?token=eee97ade0e7401a23d12ce61158be94906f9f098c9b7f9c2599e50bb6a7ef5c3&format=json&url=http://www.lequangminh591.id.vn/web_key.html?key!{key_ghe}')
    
    if response.status_code == 200:
        try:
            response_json = response.json()
            url_key = response_json.get('shortenedUrl', 'Không thể lấy link')
        except requests.exceptions.JSONDecodeError:
            url_key = f'Không thể lấy link - phản hồi không phải là JSON hợp lệ\nPhản hồi thô: {response.text}'
    else:
        url_key = 'Không thể lấy link'

    # Link đến file GIF
    gif_url = 'https://media.giphy.com/media/1X7hWk9WWs64EvZgdK/giphy.gif'

    # Tạo nội dung văn bản cho phản hồi với GIF
    text = f'''
<pre>• Link Rút Gọn Của Bạn Là : <code>{url_key}</code>
• Vượt Link Xong Sử Dụng Lệnh
• /yeumoney + [ Mã Code ]
• Nhập Đúng Sẽ Được Cộng 100Đ</pre>
'''

    # Gửi phản hồi văn bản và GIF
    bot.send_animation(chat_id=call.message.chat.id, animation=gif_url, caption=text, parse_mode='HTML')

@bot.message_handler(commands=['yeumoney'])
def handle_yeumoney_command(message):
    key = message.text.split(' ')[1].strip()  # Lấy phần key từ lệnh
    
    if key in used_keys:
        bot.reply_to(message, 'Mã code này đã được sử dụng. Vui lòng thử lại với mã khác.')
    elif key == key_ghe: # Thay YOUR_CORRECT_KEY_HERE bằng key chính xác
        update_user_balance(message.from_user.id, 100)  # Cộng 200Đ vào tài khoản người dùng
        used_keys[key] = True  # Đánh dấu mã đã được sử dụng
        save_used_keys(used_keys)
        bot.reply_to(message, 'Bạn đã nhập đúng mã code! Đã được cộng 100Đ vào tài khoản.')
    else:
        bot.reply_to(message, 'Mã code không hợp lệ. Vui lòng thử lại.')

   
   
   
key_ghe = ''

@bot.callback_query_handler(func=lambda call: call.data == "dilink")
def callback_query(call):
    global key_gh # Sử dụng global để có thể thay đổi giá trị của biến key_ghe
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Vui Lòng Đợi Trong Giây Lát!')

    username = call.from_user.username
    abcxyz = "qwertyuiopasdfghjklzxcvbnm1234567890"

    # Tạo key từ username, thời gian hiện tại và một phần ngẫu nhiên
    current_time = str(int(time.time()))  # Lấy thời gian hiện tại và chuyển đổi thành chuỗi
    random_part = ''.join(random.choices(abcxyz, k=12))  # Chuỗi ngẫu nhiên
    string = f'dilink-{username}+{current_time}+{random_part}'
    
    # Tạo key từ chuỗi string
    hash_object = hashlib.md5(string.encode())
    key_gh = str(hash_object.hexdigest())
    print(key_gh)

    url_api = "dilink.com"
    token_api = "bdd938a7fec4c39b2bb1bb56196e6f8eaa8ea322b89350352f625df900f6aa08"
    
    # Thực hiện yêu cầu GET tới API và kiểm tra phản hồi
    link = f'https://dilink.net/QL_api.php?token={token_api}&url=https://abcxyzok.blogspot.com/p/click-vao-o-ben-duoi-se-tu-ong-sao-chep.html?key={key_gh}'
    url_key = requests.get(f'https://tinyurl.com/api-create.php?url={link}').text
    # Link đến file GIF
    gif_url = 'https://media.giphy.com/media/1X7hWk9WWs64EvZgdK/giphy.gif'

    # Tạo nội dung văn bản cho phản hồi với GIF
    text = f'''
<pre>• Link Rút Gọn Của Bạn Là : {url_key}
• Vượt Link Xong Sử Dụng Lệnh
• /dilink + [ Mã Code ]
• Nhập Đúng Sẽ Được Cộng 100Đ</pre>
'''

    # Gửi phản hồi văn bản và GIF
    bot.send_animation(chat_id=call.message.chat.id, animation=gif_url, caption=text, parse_mode='HTML')




@bot.message_handler(commands=['dilink'])
def handle_yeumoney_command(message):
    key = message.text.split(' ')[1].strip()  # Lấy phần key từ lệnh
    
    if key in used_keys:
        bot.reply_to(message, 'Mã code này đã được sử dụng. Vui lòng thử lại với mã khác.')
    elif key == key_gh:  # Thay YOUR_CORRECT_KEY_HERE bằng key chính xác
        update_user_balance(message.from_user.id, 0)  # Cộng 200Đ vào tài khoản người dùng
        used_keys[key] = True  # Đánh dấu mã đã được sử dụng
        save_used_keys(used_keys)
        bot.reply_to(message, 'Bạn đã nhập đúng mã code! Đã được cộng 100Đ vào tài khoản.')
    else:
        bot.reply_to(message, 'Mã code không hợp lệ. Vui lòng thử lại.')

key_ghe = ''

@bot.callback_query_handler(func=lambda call: call.data == "link4m")
def callback_query(call):
    global key_g # Sử dụng global để có thể thay đổi giá trị của biến key_ghe
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Vui Lòng Đợi Trong Giây Lát!')

    username = call.from_user.username
    abcxyz = "qwertyuiopasdfghjklzxcvbnm1234567890"

    # Tạo key từ username, thời gian hiện tại và một phần ngẫu nhiên
    current_time = str(int(time.time()))  # Lấy thời gian hiện tại và chuyển đổi thành chuỗi
    random_part = ''.join(random.choices(abcxyz, k=15))  # Chuỗi ngẫu nhiên
    string = f'dilink-{username}+{current_time}+{random_part}'
    
    # Tạo key từ chuỗi string
    hash_object = hashlib.md5(string.encode())
    key_g = str(hash_object.hexdigest())
    print(key_g)

    
    url_key = requests.get(f'https://link4m.co/api-shorten/v2?api=65cba570f740c02fb53b81c6&url=https://abcxyzok.blogspot.com/p/click-vao-o-ben-duoi-se-tu-ong-sao-chep.html?key={key_g}').json()['shortenedUrl']
  
    # Link đến file GIF
    gif_url = 'https://media.giphy.com/media/1X7hWk9WWs64EvZgdK/giphy.gif'

    # Tạo nội dung văn bản cho phản hồi với GIF
    text = f'''
<pre>• Link Rút Gọn Của Bạn Là : {url_key}
• Vượt Link Xong Sử Dụng Lệnh
• /link4m + [ Mã Code ]
• Nhập Đúng Sẽ Được Cộng 100Đ</pre>
'''

    # Gửi phản hồi văn bản và GIF
    bot.send_animation(chat_id=call.message.chat.id, animation=gif_url, caption=text, parse_mode='HTML')




@bot.message_handler(commands=['link4m'])
def handle_yeumoney_command(message):
    key = message.text.split(' ')[1].strip()  # Lấy phần key từ lệnh
    
    if key in used_keys:
        bot.reply_to(message, 'Mã code này đã được sử dụng. Vui lòng thử lại với mã khác.')
    elif key == key_g:  # Thay YOUR_CORRECT_KEY_HERE bằng key chính xác
        update_user_balance(message.from_user.id, 100)  # Cộng 200Đ vào tài khoản người dùng
        used_keys[key] = True  # Đánh dấu mã đã được sử dụng
        save_used_keys(used_keys)
        bot.reply_to(message, 'Bạn đã nhập đúng mã code! Đã được cộng 100Đ vào tài khoản.')
    else:
        bot.reply_to(message, 'Mã code không hợp lệ. Vui lòng thử lại.')

@bot.message_handler(func=lambda message: message.text == "Hoa Hồng Các Link")
def checktien_link(message):
    link_text = '''
    Mỗi Lần Rút Gọn Của Các Link'
    • Link4m | 300 Đồng
    • Yeumoney | 200 Đồng
    • Dilink | 0 Đồng
    '''
    bot.reply_to(message, link_text)
     
        
        
        
@bot.message_handler(func=lambda message: message.text == "Tài Khoản")
def handle_account_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    balance = get_balance(user_id)
    balance = "{:,}".format(balance)  # Định dạng số dư với dấu chấm
    text = f"""
<pre>
📄 Profile For Username: @{message.from_user.username}
• Username: {message.from_user.username}
• User_id: {user_id}
• Số Coin: {balance} Coin
</pre>
"""
    gif_url = 'https://media4.giphy.com/media/l9ToNngqfgDrpry0H3/giphy.gif?cid=6c09b9523bxy8fgoy9q1t2xwan2okmraitrwecuyeiy5wxpn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=g'  # URL của GIF bạn muốn gửi
    bot.send_animation(message.chat.id, gif_url, caption=text, parse_mode='HTML')
    
    

@bot.message_handler(commands=['addcoin'])
def handle_addcoin_command(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "Bạn không có quyền thực hiện lệnh này.")
        return

    try:
        # Lấy user_id và số tiền từ tin nhắn
        details = message.text.split()
        target_user_id = int(details[1])
        amount = int(details[2])
        
        update_user_balance(target_user_id, amount)
        bot.reply_to(message, f'Đã cộng {amount} coins cho user {target_user_id}. Số dư hiện tại: {get_balance(target_user_id)} coins')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Vui lòng nhập theo cú pháp /addcoin [user_id] [số tiền]')

# Lệnh trừ coin từ tài khoản
@bot.message_handler(commands=['trucoin'])
def handle_trucoin_command(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "Bạn không có quyền thực hiện lệnh này.")
        return

    try:
        # Lấy user_id và số tiền từ tin nhắn
        details = message.text.split()
        target_user_id = int(details[1])
        amount = int(details[2])
        
        update_user_balance(target_user_id, -amount)
        bot.reply_to(message, f'Đã trừ {amount} coins của user {target_user_id}. Số dư hiện tại: {get_balance(target_user_id)} coins')
    except (IndexError, ValueError):
        bot.reply_to(message, 'Vui lòng nhập theo cú pháp /trucoin [user_id] [số tiền]')

@bot.message_handler(func=lambda message: message.text == "Rút Tiền")
def handle_withdraw(message):
    user_id = message.from_user.id
    if str(user_id) in user_data and user_data[str(user_id)]['balance'] >= 100000:
        gif_url = 'https://media.giphy.com/media/1X7hWk9WWs64EvZgdK/giphy.gif'
        text = '''
<pre>🛡<b>Nhập theo mẫu để rút tiền:</b>
/rut [số tài khoản] [tên ngân hàng] [tên thật] [số tiền]

<b>Ví dụ:</b> /rut 0123456789 MBBANK NGUYEN VAN A 100000

<b>Số tiền rút tối thiểu:</b> 100000Đ

• Thời gian rút tiền được duyệt trong vòng 24 giờ
⛔️ Chỉ gửi lệnh rút 1 lần [không spam rút]</pre>
'''
        bot.send_animation(message.chat.id, gif_url, caption=text, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "Bạn cần có số dư ít nhất 100000 đồng để thực hiện lệnh rút tiền.")

# Định nghĩa danh sách các admin IDs
 # Thay với danh sách các admin IDs thực tế

@bot.message_handler(commands=['rut'])
def handle_withdraw_request(message):
    user_id = message.from_user.id
    if str(user_id) in user_data:
        current_balance = user_data[str(user_id)]['balance']
        details = message.text.split()
        if len(details) == 5:
            account_number = details[1]
            bank_name = details[2]
            real_name = details[3]
            amount = int(details[4])
            if amount >= 100000:
                if current_balance >= amount:
                    # Trừ số tiền rút từ số dư của người dùng
                    user_data[str(user_id)]['balance'] -= amount
                    save_user_data(user_data)  # Lưu lại dữ liệu sau khi cập nhật số dư

                    # Gửi yêu cầu rút tiền cho admin
                    for admin_id in ADMIN_IDS:
                        keyboard = types.InlineKeyboardMarkup()
                        keyboard.add(types.InlineKeyboardButton("Duyệt", callback_data=f"approve_{user_id}_{amount}"))
                        keyboard.add(types.InlineKeyboardButton("Hủy", callback_data=f"decline_{user_id}"))
                        bot.send_message(admin_id, f"Yêu cầu rút tiền từ user {message.from_user.username} (ID: {user_id}):\nSố tài khoản: {account_number}\nNgân hàng: {bank_name}\nTên thật: {real_name}\nSố tiền: {amount} đồng", reply_markup=keyboard)
                    
                    gif_url = 'https://media.giphy.com/media/1X7hWk9WWs64EvZgdK/giphy.gif'
                    text = f'''
<pre>🛡Yêu cầu rút tiền của bạn đã được gửi đi. Vui lòng chờ duyệt.
Ví dụ:
<code>/rut 0123456789 MBBANK NGUYEN VAN A 100000</code>
Số tiền rút tối thiểu: 100000Đ
⛔️Chỉ gửi lệnh rút 1 lần [không spam rút]</pre>
'''
                    bot.send_animation(message.chat.id, gif_url, caption=text, parse_mode='HTML')
                else:
                    bot.send_message(message.chat.id, "Số dư của bạn không đủ để thực hiện giao dịch.")
            else:
                bot.send_message(message.chat.id, "Số tiền rút tối thiểu là 100000 đồng.")
        else:
            bot.send_message(message.chat.id, "Sai cú pháp. Vui lòng nhập theo mẫu: /rut [số tài khoản] [tên ngân hàng] [tên thật] [số tiền]")
    else:
        bot.send_message(message.chat.id, "Bạn cần có số dư ít nhất 100000 đồng để thực hiện lệnh rút tiền.")

# Xử lý khi admin nhận callback từ nút Duyệt hoặc Hủy
@bot.callback_query_handler(func=lambda call: True)
def handle_approval(call):
    try:
        action, user_id, amount = call.data.split('_')
        if action == "approve":
            # Xử lý duyệt yêu cầu rút tiền
            bot.send_message(user_id, f"Bạn đã rút tiền thành công số tiền {amount} Đ")
        elif action == "decline":
            # Xử lý hủy yêu cầu rút tiền
            bot.send_message(user_id, "Yêu cầu rút tiền của bạn đã bị hủy. Vui lòng liên hệ admin để biết thêm chi tiết.")
    except ValueError:
        bot.send_message(call.message.chat.id, "Đã xảy ra lỗi khi xử lý yêu cầu. Vui lòng thử lại sau.")

@bot.message_handler(func=lambda message: message.text == "Admin")
def handle_admin_info(message):
    # Link đến file GIF
    gif_url = 'https://media.giphy.com/media/1X7hWk9WWs64EvZgdK/giphy.gif'

    # Nội dung tin nhắn
    text = '''
<pre>
Infomation
Telegram : @None
Zalo : @None
Facebook : @None
</pre>
    '''

    # Gửi tin nhắn kèm GIF
    bot.send_animation(message.chat.id, gif_url, caption=text, parse_mode='HTML')
keep_alive()
bot.polling()



