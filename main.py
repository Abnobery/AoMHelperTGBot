from aiogram import Bot, Dispatcher, executor, types, exceptions
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from dotenv import dotenv_values
from chars import CharProvider, CharacterTeam, CharacterTeamRecord
from imageGenerator import ImageGenerator

env = {
    **dotenv_values(".env"),
   # **dotenv_values(".env.dev"),  # override
}

API_TOKEN = env["BOT_API_TOKEN"]
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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

    def __init__(self, currentTeam = {}):
        self.currentTeam = currentTeam


class StorageEntity:
    teams: list[CharacterTeamRecord] = []

    def __init__(self, teams = []):
        self.teams = teams


userStates = {}
storageEntity = StorageEntity()

# Command handler
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
            for idx, x in enumerate(range(len(storageEntity.teams))):
                teams.append(f'{idx+1}. '+', '.join(storageEntity.teams[x].team.members) + f'; ({len(storageEntity.teams[x].counterTeams)})')
            await message.reply('\n'.join(teams))
        else:
            await message.reply("В базе нет записей")
    except Exception as ex:
        await message.reply(ex)


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
    counter = CharacterTeam.characterTeamFromText(message.text)
    targetTeam = userStates[username].currentTeam
    recordToAdjust = next((x for x in storageEntity.teams if x.team == targetTeam), None)
    
    if counter is not None and recordToAdjust is not None:
        userStates[username].waitingForCounterPack = False

        if counter not in recordToAdjust.counterTeams:
            recordToAdjust.counterTeams.append(counter)

        resultImg = ImageGenerator.generateImageForCharacterTeamRecord(recordToAdjust, username)
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
    else:
        await message.reply("Ошибка ввода, попробуйте еще раз")


async def processDeleteCounterPackRequest(message: types.Message, username):
    targetTeam = userStates[username].currentTeam
    recordToAdjust = next((x for x in storageEntity.teams if x.team == targetTeam), None)

    try:
        teamNumberToDelete = int(message.text)
        if len(recordToAdjust.counterTeams) >= teamNumberToDelete:
            if recordToAdjust != None:
                userStates[username].waitingForPackToDelete = False
                del recordToAdjust.counterTeams[teamNumberToDelete-1]
                resultImg = ImageGenerator.generateImageForCharacterTeamRecord(recordToAdjust, username)
                await bot.delete_message(message.chat.id, message.message_id)
                await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
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
        if userStates[username].currentTeam != None:
            userStates[username].waitingForPackToDelete = False
            userStates[username].waitingForCounterPack = True
            await callback_query.message.reply("Какой контрпак добавить?")
        else:
            logging.info(f'skipped callback touch')

    elif callback_query.data == "delete":
        if userStates[username].currentTeam is not None:
            userStates[username].waitingForCounterPack = False
            userStates[username].waitingForPackToDelete = True
            await callback_query.message.reply("Какой контрпак удалить? (порядковый номер)")

    elif callback_query.data == "show":
        await showCharacterTeamForCurrentRequest(callback_query.message, username)


async def showCharacterTeamForCurrentRequest(message, username):
    try:
        if userStates[username].currentTeam is not None:
            recordToShow = next((x for x in storageEntity.teams if x.team == userStates[username].currentTeam), None)
            if recordToShow is None:
                recordToShow = CharacterTeamRecord(userStates[username].currentTeam)
                storageEntity.teams.append(recordToShow)
                
            resultImg = ImageGenerator.generateImageForCharacterTeamRecord(recordToShow, username)
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.send_photo(chat_id=message.chat.id, photo=resultImg, reply_markup=inline_keyboard_second)
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
    trimmed = request.replace(',', ' ')
    charKeys = " ".join(trimmed.split()).split(' ')

    charsList = []
    for charKey in charKeys:
        char = CharProvider.charByKey(charKey)
        if char is not None:
            charsList.append(char.name)

    if len(charsList) == 5:
        res = ImageGenerator.generateTeamImage(charsList, username, sendToChat = True)
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