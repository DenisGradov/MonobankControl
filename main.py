import telebot, monobank, sqlite3,  time,threading
from telebot import types
from config import BotToken, AdminId

ApiToken=''#Передача ласт токена в другие функции
TokenList={}#Передача словаря токенов без лишних запросов, для избежания false ответов при запросах из-за лимита запросов (1 запрос в 60 секунд)
TokenAct=''#Актуальный токен для подробной информации о картах
IdAct=''#Актуальный ид карты
BalanceAct={}#Балансы всех карт и банок для отслеживания пополнений
currency=''#Актуальный курс
bot=telebot.TeleBot(BotToken)

connect=sqlite3.connect('tokens.db')
cursor=connect.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS tokens(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    token TEXT,
    activate INTEGER,
    notif INTEGER
)""")




@bot.message_handler()
def ms(message):
    if message.chat.id==AdminId: 
        if message.text=='/start':
            connect  = sqlite3.connect('tokens.db')
            cursor = connect.cursor()
            cursor.execute(f'SELECT COUNT (id) FROM tokens')
            connect.commit()
            if cursor.fetchall()[0][0] == 0:
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='➕Добавить токен'
                klava.add(button1)
                bot.send_message(message.chat.id,'Ты еще не добавил токен(ы) в бота!',reply_markup=klava)
            else:
                menu(message)
        elif message.text=='➕Добавить токен':
            klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1='🧐 Где его взять?'
            button2='🏚Меню'
            klava.add(button1,button2)
            InputToken=bot.send_message(message.chat.id,'Введи свой API токен:',reply_markup=klava)
            bot.register_next_step_handler(InputToken,InputToken_def)
        elif message.text=='➖Удалить  токен':
            klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1='🏚Меню'
            klava.add(button1)
            InputTokenForDel=bot.send_message(message.chat.id,'Введи Id токена:',reply_markup=klava)
            bot.register_next_step_handler(InputTokenForDel,InputTokenForDel_def)
        elif message.text=='🗒Список токенов':
            connect  = sqlite3.connect('tokens.db')
            cursor = connect.cursor()
            cursor.execute(f'SELECT COUNT (id) FROM tokens')
            connect.commit()
            maxTokens=cursor.fetchall()[0][0]
            if maxTokens == 0:
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='➕Добавить токен'
                klava.add(button1)
                bot.send_message(message.chat.id,'Ты еще не добавил токен(ы) в бота!',reply_markup=klava)
            else:
                text=''
                IsAnyActivate=False#Для  проверки активных токенов. Мб все удалены
                for i in  range(maxTokens):
                    connect  = sqlite3.connect('tokens.db')
                    cursor = connect.cursor()
                    cursor.execute(f'SELECT token FROM tokens WHERE id=?',(i+1,))
                    token=cursor.fetchall()[0][0]
                    cursor.execute(f'SELECT name FROM tokens WHERE id=?',(i+1,))
                    name=cursor.fetchall()[0][0]
                    cursor.execute(f'SELECT activate FROM tokens WHERE id=?',(i+1,))
                    activate=cursor.fetchall()[0][0]
                    cursor.execute(f'SELECT notif FROM tokens WHERE id=?',(i+1,))
                    notif=cursor.fetchall()[0][0]
                    if activate==1:
                        connect.commit()
                        IsAnyActivate=True
                        if name=='None':
                            name=''
                        else:
                            name=f'\nИмя: `{name}`'
                        if notif==0:
                            notif='🔴Уведомления выключены'
                        else:
                            notif='🟢Уведомления включены'
                        text=text+f'Id: `{i+1}`\nToken: `{token}`{name}\n{notif}\n\n'
                    if (maxTokens-i)==1:
                        break
                if IsAnyActivate:
                    klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                    button1='🏚Меню'
                    klava.add(button1)
                    bot.send_message(message.chat.id,text,parse_mode='Markdown')
                    choiceToken=bot.send_message(message.chat.id,'Для работы с токеном - введи его Id в чат. Для возврата в меню используй кнопку',reply_markup=klava)
                    bot.register_next_step_handler(choiceToken,choiceToken_def)
                else:
                    bot.send_message(message.chat.id,'У тебя нет токенов')
        elif message.text=='🏚Меню':
            menu(message)
        elif message.text=='💲Курс':
            global currency
            if currency=='':
                bot.send_message(message.chat.id,'Попробуй через минуту')
            else:
                text='Курс покупки/продажи\n\n'
                for i in currency:
                    if i['currencyCodeA']==840 and i['currencyCodeB']==980:
                        text=f"{text}*$(Доллар)* `{i['rateBuy']}`/`{i['rateSell']}`\n"
                    elif i['currencyCodeA']==978 and i['currencyCodeB']==980:
                        text=f"{text}*€(Евро)* `{i['rateBuy']}`/`{i['rateSell']}`\n"
                bot.send_message(message.chat.id,text,parse_mode='Markdown')
            menu(message)
                    
def InputTokenForDel_def(message):
    if message.text=='🏚Меню':
        menu(message)
    elif (message.text).isnumeric():
        connect = sqlite3.connect('tokens.db')
        cursor= connect.cursor()
        cursor.execute(f'SELECT token FROM tokens WHERE id=?',(message.text,))
        token=cursor.fetchone() 
        connect.commit()
        if token is None:
            klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1='🏚Меню'
            klava.add(button1)
            InputTokenForDel=bot.send_message(message.chat.id,'⚠️Такого токена нет в базе!\nВведи Id токена:',reply_markup=klava)
            bot.register_next_step_handler(InputTokenForDel,InputTokenForDel_def)
        else:
            connect  = sqlite3.connect('tokens.db')
            cursor = connect.cursor()
            cursor.execute("UPDATE tokens SET activate = (?) WHERE id = (?)",(0,message.text,))
            connect.commit()
            bot.send_message(message.chat.id,'Токен был удален из базы!')
            menu(message)
    else:
        klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1='🏚Меню'
        klava.add(button1)
        InputTokenForDel=bot.send_message(message.chat.id,'⚠️Айди - число\nВведи Id токена:',reply_markup=klava)
        bot.register_next_step_handler(InputTokenForDel,InputTokenForDel_def)

                    
def choiceToken_def(message):
    global TokenList
    if message.text=='🏚Меню':
        menu(message)
    elif (message.text).isnumeric():
        connect = sqlite3.connect('tokens.db')
        cursor= connect.cursor()
        cursor.execute(f'SELECT token FROM tokens WHERE id=?',(message.text,))
        token=cursor.fetchone() 
        connect.commit()
        if token is None:
            klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1='🏚Меню'
            klava.add(button1)
            choiceToken=bot.send_message(message.chat.id,'⚠️Токена с таким Id не существует!\nДля работы с токеном - введи его Id в чат. Для возврата в меню используй кнопку',reply_markup=klava)
            bot.register_next_step_handler(choiceToken,choiceToken_def)
        else:
            global TokenAct,IdAct
            TokenAct=token[0]
            try:
                user_info=TokenList[f'{token[0]}']
                connect  = sqlite3.connect('tokens.db')
                cursor = connect.cursor()
                cursor.execute(f'SELECT notif FROM tokens WHERE token=?',(TokenAct,))
                notif=cursor.fetchall()[0][0]
                connect.commit()
                if notif==0:
                    notifText='🔴Уведомления выключены'
                else:
                    notifText='🟢Уведомления включены'
                bot.send_message(message.chat.id, f"Владелец токена: `{user_info['name']}`\n{notifText}",parse_mode='Markdown')
                text='💳Карты:\n\n'
                for i in user_info['accounts']:
                    balance=float(i['balance'])/100
                    if i['currencyCode']==840:
                        val='$'
                    elif i['currencyCode']==980:
                        val='₴'
                    elif i['currencyCode']==978:
                        val='€'
                    else:
                        val=''
                    text=f"{text}Карта: `{i['maskedPan'][0]}`\nБаланс: `{balance}{val}`\nId: `{i['id']}`\n\n"
                bot.send_message(message.chat.id, text,parse_mode='Markdown')
                text='🫙Банки:\n\n'
                try:
                    for i in user_info['jars']:
                        balance=float(i['balance'])/100
                        text=f"{text}Банка: `{i['title']}`\nБаланс: `{balance}`\nId: `{i['id']}`\n\n"
                    bot.send_message(message.chat.id, text,parse_mode='Markdown')
                except:
                    bot.send_message(message.chat.id, f'{text}У вас нет банок',parse_mode='Markdown')
                    
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='🏚Меню'
                if notif==0:
                    button2='✅Включить уведомления'
                else:
                    button2='❌Выключить уведомления'
                    
                global IdAct
                IdAct=message.text
                klava.add(button1,button2)
                coiceCard=bot.send_message(message.chat.id,'Для получения более детальной информации - введи Id карты/банки',reply_markup=klava)
                bot.register_next_step_handler(coiceCard,choiceCard_def)
            except:
                bot.send_message(message.chat.id, 'Попробуй через минуту',parse_mode='Markdown')
                menu(message)
    else:
        klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1='🏚Меню'
        klava.add(button1)
        choiceToken=bot.send_message(message.chat.id,'⚠️Для работы с токеном - введи его Id в чат. Для возврата в меню используй кнопку',reply_markup=klava)
        bot.register_next_step_handler(choiceToken,choiceToken_def)

def choiceCard_def(message):
    global IdAct, TokenAct
    if message.text=='🏚Меню':
        menu(message)
    elif message.text=='✅Включить уведомления':#TokenAct
        connect  = sqlite3.connect('tokens.db')
        cursor = connect.cursor()
        cursor.execute("UPDATE tokens SET notif = (?) WHERE token = (?)",(1,TokenAct,))
        connect.commit()
        bot.send_message(message.chat.id,f'✅Уведомления для токена `{TokenAct}` были успешно включены!', parse_mode='Markdown')
        message.text=IdAct
        choiceToken_def(message)
    elif message.text=='❌Выключить уведомления':#TokenAct
        connect  = sqlite3.connect('tokens.db')
        cursor = connect.cursor()
        cursor.execute("UPDATE tokens SET notif = (?) WHERE token = (?)",(0,TokenAct,))
        connect.commit()
        bot.send_message(message.chat.id,f'❌Уведомления для токена `{TokenAct}` были успешно выключены!', parse_mode='Markdown')
        message.text=IdAct
        choiceToken_def(message)
    else:
        user_info=TokenList[f'{TokenAct}']
        try:
            state=False
            for i in user_info['accounts']:
                if str(message.text)==str(i['id']):
                    balance=float(i['balance'])/100
                    text=f"💳Карта: `{i['maskedPan'][0]}`\nБаланс: `{balance}`\nId: `{i['id']}`\nCreditLimit: `{i['creditLimit']}`\nType: `{i['type']}`\nIban: `{i['iban']}`\nCashbakType: `{i['cashbackType']}`\nSendId: `{i['sendId']}`\nCurrencyCode: `{i['currencyCode']}`"
                    state=True
                    break
            if state:
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='🏚Меню'
                klava.add(button1)
            else:
                for i in user_info['jars']:
                    if str(message.text)==str(i['id']):
                        balance=float(i['balance'])/100
                        text=f"🫙Банка: `{i['title']}`\nОписание: `{i['description']}`\nБаланс: `{balance}`\nId: `{i['id']}`\nSendId: `{i['sendId']}`\nCurrencyCode: `{i['currencyCode']}`\nGoal: `{i['goal']}`"
                        state=True
                        break
            if state:
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='🏚Меню'
                klava.add(button1)
                bot.send_message(message.chat.id,text,reply_markup=klava,parse_mode='Markdown')
            else:
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='🏚Меню'
                klava.add(button1)
                coiceCard=bot.send_message(message.chat.id,'⚠️Id не найден!\nДля получения более детальной информации или для настроек уведомлений - введи Id карты/банки',reply_markup=klava)
                bot.register_next_step_handler(coiceCard,choiceCard_def)
                
        except:
            klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1='🏚Меню'
            klava.add(button1)
            coiceCard=bot.send_message(message.chat.id,'⚠️Id не найден, либо произошла какая-то ошибка!\nДля получения более детальной информации или для настроек уведомлений - введи Id карты/банки',reply_markup=klava)
            bot.register_next_step_handler(coiceCard,choiceCard_def)
       
def InputToken_def(message):
    if message.text=='🧐 Где его взять?':
        bot.send_photo(message.chat.id,'https://i.imgur.com/0RxBVof.png','Получить API токен можно тут - https://api.monobank.ua')
        klava=types.ReplyKeyboardRemove()
        InputToken=bot.send_message(message.chat.id,'Введи свой API токен:',reply_markup=klava)
        bot.register_next_step_handler(InputToken,InputToken_def)
    elif message.text=='🏚Меню':
        menu(message)
    else:
        try:
            mono = monobank.Client(message.text)
            user_info = mono.get_client_info()
            TokenList[f'{message.text}']=user_info
            print(user_info)
            connect = sqlite3.connect('tokens.db')
            cursor= connect.cursor()
            cursor.execute(f'SELECT id FROM tokens WHERE token=?',(message.text,))
            token=cursor.fetchone() 
            cursor.execute(f'SELECT activate FROM tokens WHERE token=?',(message.text,))#Сделано для проверки на активность токена. При удалении из дб - просто статус активности меняется на другой. При написании кода это был самый простой способ удалить токен из бд без гемора
            activate=cursor.fetchone() 
            print(message.text)
            print(token)
            print(activate)
            if (token is None or activate[0] != 1):
                info=[message.text, 1, 0]
                cursor.execute('INSERT INTO tokens(token, activate, notif) VALUES (?, ?, ?);', info)
                connect.commit()
                klava=types.ReplyKeyboardMarkup(True)
                button1='🏁Пропустить'
                klava.add(button1)
                setName=bot.send_message(message.chat.id,'Токен валидный и успешно добавлен в бота. Хочешь выдать токену название? Если да - отправь название в чат. В противном случае жми на кнопку',reply_markup=klava)
                global ApiToken
                ApiToken=message.text
                bot.register_next_step_handler(setName,setName_def)
            else:
                bot.send_message(message.chat.id,'Токен валидный, но уже находится в боте')
                
                klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1='🏚Меню'
                klava.add(button1)
                InputToken=bot.send_message(message.chat.id,'Введи свой API токен:',reply_markup=klava)
                bot.register_next_step_handler(InputToken,InputToken_def)
        except:
            bot.send_message(message.chat.id,'Токен невалидный, либо ты делаешь слишком много попыток (лимит - 1 раз в минуту)')
            klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1='🏚Меню'
            klava.add(button1)
            InputToken=bot.send_message(message.chat.id,'Введи свой API токен:',reply_markup=klava)
            bot.register_next_step_handler(InputToken,InputToken_def)

def setName_def(message):
    global ApiToken
    if message.text=='🏁Пропустить':
        name='None'
        klava=types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id,f'Токен: `{ApiToken}` активирован',reply_markup=klava,parse_mode='Markdown')
        menu(message)
    else:
        name=message.text
        bot.send_message(message.chat.id,f'Токен: `{ApiToken}` с именем `{name}` активирован',parse_mode='Markdown')
        menu(message)
    connect  = sqlite3.connect('tokens.db')
    cursor = connect.cursor()
    cursor.execute("UPDATE tokens SET name = (?) WHERE token = (?)",(name,ApiToken,))
    connect.commit()

def menu(message):
    klava=types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1='➕Добавить токен'
    button2='🗒Список токенов'
    button3='➖Удалить  токен'
    button4='💲Курс'
    klava.add(button1,button2,button3,button4)
    bot.send_message(message.chat.id,f'{message.from_user.first_name}, ты находишься в меню:',reply_markup=klava)

def starter():
    while True:
        connect  = sqlite3.connect('tokens.db')
        cursor = connect.cursor()
        cursor.execute(f'SELECT COUNT (id) FROM tokens')
        connect.commit()
        maxTokens=cursor.fetchall()[0][0]
        
        global TokenList,BalanceAct,currency
        BalanceActNew={}#НовыйБалансАкт
        time.sleep(90)
        for i in  range(maxTokens):
            try:
                connect  = sqlite3.connect('tokens.db')
                cursor = connect.cursor()
                cursor.execute(f'SELECT activate FROM tokens WHERE id=?',(i+1,))
                activate=cursor.fetchall()[0][0]
                connect.commit()
                if activate==1:
                    connect  = sqlite3.connect('tokens.db')
                    cursor = connect.cursor()
                    cursor.execute(f'SELECT token FROM tokens WHERE id=?',(i+1,))
                    token=cursor.fetchall()[0][0]
                    cursor.execute(f'SELECT notif FROM tokens WHERE id=?',(i+1,))
                    notif=cursor.fetchall()[0][0]
                    connect.commit()
                    
                    mono = monobank.Client(token)
                    user_info = mono.get_client_info()
                    TokenList[f'{token}']=user_info
                    #BalanceAct
                    if notif==1:
                        for i2 in user_info['accounts']:
                            balance=float(i2['balance'])/100
                            BalanceActNew[f"{i2['id']}"]=[i2['maskedPan'][0],balance,'карте']
                        try:
                            for i2 in user_info['jars']:
                                balance=float(i2['balance'])/100
                                BalanceActNew[f"{i2['title']}"]=[i2['maskedPan'][0],balance,'банке']
                        except:
                            pass
                        
                        if len(BalanceAct)==0:
                            BalanceAct=BalanceActNew
                        else:
                            for i3 in BalanceActNew:
                                print(BalanceActNew[i3][1])
                                if BalanceActNew[i3][1]>BalanceAct[i3][1]:
                                    bot.send_message(AdminId,f'На {BalanceActNew[i3][2]} `{BalanceActNew[i3][0]}` *+{round(float(BalanceActNew[i3][1])-float(BalanceAct[i3][1]),2)} грн.*!',parse_mode='Markdown')
                                print('Не было пополнений')
                        BalanceAct=BalanceActNew
                    currency=mono.get_currency()
            except:
                print('oshibka yopta')

            if (maxTokens-i)==1:
                break

if __name__ == '__main__':
    t2 = threading.Thread(target=starter)
    t2.start()
    bot.polling(none_stop=True)
