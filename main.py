from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from dotenv import dotenv_values
from chars import CharacterTeam, CharacterTeamRecord
from imageGenerator import ImageGenerator
from persistenceManager import PersistenceManager

env = {
    **dotenv_values(".env"),
   # **dotenv_values(".env.dev"),  # override
}

API_TOKEN = env["BOT_API_TOKEN"]
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
storage = PersistenceManager(db=env["DB"])

first_level = [
    InlineKeyboardButton("Контрпаки", callback_data="show")
]
second_level = [
    InlineKeyboardButton("Добавить контрпак", callback_data="add"),
    InlineKeyboardButton("Удалить контрпак", callback_data="delete")
]
inline_keyboard_first = InlineKeyboardMarkup(row_width=1)
inline_keyboard_first.add(*first_level)
inline_keyboard_second = InlineKeyboardMarkup(row_width=1)
inline_keyboard_second.add(*second_level)

class UserState:
    currentTeam = {}
    waitingForCounterPack = False
    waitingForPackToDelete = False
    editor = False

    def __init__(self, currentTeam = {}):
        self.currentTeam = currentTeam


userStates = {}
storageEntity = storage.getStorageEntity()

# Command handler

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply("Откройте меню чтобы начать работать с ботом")

@dp.message_handler(commands=['team'])
async def team_cmd(message: types.Message):
    if message.from_user.username is None:
        username = f'id@{message.from_user.id}'
    else:
        username = message.from_user.username

    if username not in userStates:
        userStates[username] = UserState()

    userStates[username].waitingForPackToDelete = False
    userStates[username].waitingForCounterPack = False

    try:
        await processTextRequest(message)   
    except Exception as ex:
        await message.reply(ex)

# Command handler
@dp.message_handler(commands=['team_list'])
async def team_cmd(message: types.Message):
    global storageEntity
    if message.from_user.username is None:
        username = f'id@{message.from_user.id}'
    else:
        username = message.from_user.username

    if username not in userStates:
        userStates[username] = UserState()

    try:
        if len(storageEntity.teams) > 0:
            teams = []
            anyTeamExists = False
            counter = 1
            if len(storageEntity.teams) > 1:
                sortedTeams = sorted(storageEntity.teams, key=lambda y: y.team.members[0], reverse=False)
            else:
                sortedTeams = storageEntity.teams
            for idx, x in enumerate(range(len(sortedTeams))):
                if len(sortedTeams[x].counterTeams) > 0:
                    teams.append(f'{counter}. '+', '.join(sortedTeams[x].team.members) + f'; ({len(sortedTeams[x].counterTeams)})')
                    counter += 1
                    anyTeamExists = True
            if anyTeamExists:
                await message.reply('\n'.join(teams))
            else:
                await message.reply("В базе нет записей")
        else:
            await message.reply("В базе нет записей")
    except Exception as ex:
        await message.reply(ex)


@dp.message_handler(commands=['toggle_edit_mode'])
async def toggle_edit_mode_cmd(message: types.Message):
    if message.from_user.username is None:
        username = f'id@{message.from_user.id}'
    else:
        username = message.from_user.username

    if username not in userStates:
        userStates[username] = UserState()

    if userStates[username].editor:
        userStates[username].editor = False
        await message.reply("Режим редактирования отключен")
    else:
        userStates[username].editor = True
        await message.reply("Режим редактирования активирован")

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.reply("""Бот выдает контрпаки по запросу, к примеру используйте команду /team и перечислите список персонажей через запятую, либо отделяя пробелом (имена в два слова в этом случае пишите слитно). Для каждого персонажа есть сокращения для удобного ввода.

Например:

/team найя, аза, локхир, чжу бацзе, рой

/team укун жар-птица чжубацзе рок цуна

В режиме редактирования после запроса на добавление контрпака надо перечислить команду так же как при первом шаге, но без команды /team""")


# Message handler for all other messages
@dp.message_handler()
async def echo_msg(message: types.Message):
    if message.from_user.username is None:
        username = f'id@{message.from_user.id}'
    else:
        username = message.from_user.username

    if username not in userStates:
        userStates[username] = UserState()

    if userStates[username].waitingForCounterPack:
        await processAddCounterPackRequest(message, username)
    elif userStates[username].waitingForPackToDelete:
        await processDeleteCounterPackRequest(message, username)

async def processAddCounterPackRequest(message: types.Message, username):
    global storageEntity
    counter = CharacterTeam.characterTeamFromText(storageEntity, message.text)
    targetTeam = userStates[username].currentTeam
    recordToAdjust = next((x for x in storageEntity.teams if x.team == targetTeam), None)
    
    if counter is not None and recordToAdjust is not None:
        userStates[username].waitingForCounterPack = False

        if counter not in recordToAdjust.counterTeams:
            saveSuccess = storage.addCounterTeamForRecord(counter, recordToAdjust)
            if saveSuccess:
                recordToAdjust.counterTeams.append(counter)
                storageEntity = storage.updateStorageEntity(storageEntity)
                resultImg = ImageGenerator.generateImageForCharacterTeamRecord(storageEntity, recordToAdjust, username)
                await bot.delete_message(message.chat.id, message.message_id)
                if userStates[username].editor:
                    await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
                else:
                    await bot.send_photo(chat_id=message.chat.id, photo=resultImg)
            else:
                await message.reply("Ошибка ввода, попробуйте еще раз")
        else:
            resultImg = ImageGenerator.generateImageForCharacterTeamRecord(storageEntity, recordToAdjust, username)
            await bot.delete_message(message.chat.id, message.message_id)
            if userStates[username].editor:
                await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
            else:
                await bot.send_photo(chat_id=message.chat.id, photo=resultImg)
    else:
        await message.reply("Ошибка ввода, попробуйте еще раз")


async def processDeleteCounterPackRequest(message: types.Message, username):
    global storageEntity
    targetTeam = userStates[username].currentTeam
    recordToAdjust = next((x for x in storageEntity.teams if x.team == targetTeam), None)
    try:
        teamNumberToDelete = int(message.text)
        if len(recordToAdjust.counterTeams) >= teamNumberToDelete:
            if recordToAdjust != None:
                userStates[username].waitingForPackToDelete = False
                success = storage.deleteCounterTeamForRecord(recordToAdjust.counterTeams[teamNumberToDelete-1], recordToAdjust)
                if success:
                    del recordToAdjust.counterTeams[teamNumberToDelete-1]
                    storageEntity = storage.updateStorageEntity(storageEntity)
                    resultImg = ImageGenerator.generateImageForCharacterTeamRecord(storageEntity, recordToAdjust, username)
                    await bot.delete_message(message.chat.id, message.message_id)
                    if userStates[username].editor:
                        await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
                    else:
                        await bot.send_photo(chat_id=message.chat.id, photo=resultImg)
                else:
                    await message.reply("Произощла ошибка, попробуйте еще раз")
            else:
                await message.reply("Несуществующий порядковый номер, попробуйте еще раз")
        else:
            await message.reply("Несуществующий порядковый номер, попробуйте еще раз")
    except Exception as ex:
        await message.reply("Несуществующий порядковый номер, попробуйте еще раз")


@dp.callback_query_handler(lambda c: c.data == 'show' or c.data == 'add' or c.data == 'delete')
async def process_callback_button(callback_query: types.CallbackQuery):
    if callback_query.from_user.username is None:
        username = f'id@{callback_query.from_user.id}'
    else:
        username = callback_query.from_user.username

    await bot.send_chat_action(chat_id=callback_query.message.chat.id, action="typing")

    if callback_query.data == "add":
        if userStates[username].editor:
            if userStates[username].currentTeam != None:
                userStates[username].waitingForPackToDelete = False
                userStates[username].waitingForCounterPack = True
                await callback_query.message.reply("Какой контрпак добавить?")
            else:
                logging.error(f'skipped callback touch')
        else:
            await callback_query.message.reply("Режим редактирования отключен")

    elif callback_query.data == "delete":
        if userStates[username].editor:
            if userStates[username].currentTeam is not None:
                userStates[username].waitingForCounterPack = False
                userStates[username].waitingForPackToDelete = True
                await callback_query.message.reply("Какой контрпак удалить? (порядковый номер)")
            else:
                logging.error(f'skipped callback touch')
        else:
            await callback_query.message.reply("Режим редактирования отключен")

    elif callback_query.data == "show":
        await showCharacterTeamForCurrentRequest(callback_query.message, username)


async def showCharacterTeamForCurrentRequest(message, username):
    global storageEntity
    try:
        if userStates[username].currentTeam is not None:
            recordToShow = next((x for x in storageEntity.teams if x.team == userStates[username].currentTeam), None)
            if recordToShow is None:
                recordToShow = CharacterTeamRecord(userStates[username].currentTeam)
                saveSuccess = storage.addCharacterTeam(userStates[username].currentTeam)
                if saveSuccess:
                    storageEntity = storage.updateStorageEntity(storageEntity)
                    resultImg = ImageGenerator.generateImageForCharacterTeamRecord(storageEntity, recordToShow,
                                                                                   username)
                    await bot.delete_message(message.chat.id, message.message_id)
                    if userStates[username].editor:
                        await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
                    else:
                        await bot.send_photo(chat_id=message.chat.id, photo=resultImg)
                else:
                    await message.reply("Произошла ошибка")
            else:
                resultImg = ImageGenerator.generateImageForCharacterTeamRecord(storageEntity, recordToShow,
                                                                               username)
                await bot.delete_message(message.chat.id, message.message_id)
                if userStates[username].editor:
                    await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
                else:
                    await bot.send_photo(chat_id=message.chat.id, photo=resultImg)
        else:
            await message.reply("Произошла ошибка")
    except Exception as ex:
        logging.error(f'showCharacterTeamForCurrentRequest: {ex}')
        await message.reply("Произошла ошибка")


async def processTextRequest(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    if message.from_user.username is None:
        username = f'id@{message.from_user.id}'
    else:
        username = message.from_user.username

    request = message.get_args()
    if "," in request:
        trimmed = request.replace(' ', '').replace(',', ' ')
        charKeys = " ".join(trimmed.split()).split(' ')
    else:
        charKeys = " ".join(request.split()).split(' ')

    charsList = []

    for charKey in charKeys:
        char = storageEntity.charByKey(charKey)
        if char is not None:
            charsList.append(char.name)

    if len(charsList) == 5:
        res = ImageGenerator.generateTeamImage(storageEntity.charsFromKeys(charsList), username, sendToChat=True)
        userStates[username].currentTeam = CharacterTeam(charsList)
        await bot.send_photo(chat_id=message.chat.id, photo=res, reply_markup=inline_keyboard_first)
    else:
        await message.reply("Неверный формат команды, укажите имена персонажей, например: /team найя аза рой дрейк локхир")



@dp.errors_handler(exception=exceptions.RetryAfter)
async def exception_handler(update: types.Update, exception: exceptions.RetryAfter):
    logging.info(f'Raised exception: {exception}')
    return True


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)