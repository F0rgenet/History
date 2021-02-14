import telebot
import time
from random import randint

bot = telebot.TeleBot("1116430701:AAFPkyp0vv9XEJcDJvIHo7eTUDHOR2nZiAU")

dates = open("dates.txt", "r+", encoding="utf-8").readlines()
for date in dates: dates[dates.index(date)] = date.replace("\n", "").split(" - ")

# Тест хахахахахая

global right_date
global right_answers
global counter
global messages
global is_hard_test


def generate_question(date_list, right_position, date_needed):
	return generate_keyboard(
		[*[date_list[randint(0, len(date_list) - 1)][0] for _ in range(right_position - 1)], str(date_needed), *[date_list[randint(0, len(date_list) - 1)][0] for _ in range(4 - right_position)]],
		[*["wrong" for _ in range(right_position - 1)], "right", *["wrong" for _ in range(4 - right_position)]])


def generate_keyboard(rows, callback_data):
	keyboard = telebot.types.InlineKeyboardMarkup()
	for row in rows:
		keyboard.add(telebot.types.InlineKeyboardButton(text=row, callback_data=callback_data[rows.index(row)]))
	return keyboard


def easy_test(call):
	global right_date
	global counter
	counter += 1
	index = randint(0, len(dates) - 1)
	right_date = dates[index][0]
	bot.send_message(call.message.chat.id, dates[index][1] + "?", reply_markup=generate_question(dates, randint(1, 4), right_date))


def hard_test(chat_id):
	global is_hard_test
	global right_date
	global counter
	is_hard_test = True
	counter += 1
	index = randint(0, len(dates))
	bot.send_message(chat_id, dates[index][1] + "?")
	right_date = dates[index][0]


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
	try:
		global right_answers
		global right_date
		global messages
		bot.answer_callback_query(callback_query_id=call.id, text='')
		bot.delete_message(call.message.chat.id, call.message.message_id)
		if call.data == "ready":
			bot.send_message(call.message.chat.id, "Выберите сложность теста:", reply_markup=generate_keyboard(["Просто", "Cложно"], ["test_easy", "test_hard"]))
		elif call.data == "not_ready":
			image = open("images/dates.png", "rb")
			bot.send_photo(call.message.chat.id, photo=image)
			image.close()
			start_message(call.message)
		elif call.data == "test_easy":
			# bot.send_message(call.message.chat.id, "Выберите количество вопросов:", reply_markup=generate_keyboard(["5", "10", "15"], [5, 10, 15]))
			easy_test(call)
		# index = randint(0, len(dates) - 1)
		# bot.send_message(call.message.chat.id, dates[index][1] + "?", reply_markup=generate_question(dates, randint(1, 4), dates[index][0]))
		elif call.data == "test_hard":
			hard_test(call.message.chat.id)
		# elif type(call.data) == "int":
		# 	questions = call.data
		elif call.data in ["right", "wrong"]:
			if call.data == "right":
				messages.append(bot.send_message(call.message.chat.id, "Верно!").message_id)
				right_answers += 1
			else:
				messages.append(bot.send_message(call.message.chat.id, f"Неверно!\nПравильный ответ: {right_date}").message_id)
			if counter < 10:
				easy_test(call)
			else:
				bot.send_message(call.message.chat.id, f"Ваш результат: {right_answers}/10")
				for message in messages:
					bot.delete_message(call.message.chat.id, message)
				start_message(call.message)
	except Exception as error:
		print(error)
		time.sleep(1)


@bot.message_handler(commands=['start', 'старт'])
def start_message(message):
	global is_hard_test
	global counter
	global right_answers
	global messages
	messages = []
	counter = 0
	right_answers = 0
	bot.send_message(message.chat.id, "Вы готовы проверить свои знания?", reply_markup=generate_keyboard(["Да", "Нет"], ["ready", "not_ready"]))


@bot.message_handler(func=lambda message: True)
def check_answer(message):
	try:
		global messages
		global right_date
		global right_answers
		global is_hard_test
		if is_hard_test:
			if message.text.lower() == right_date.lower():
				messages.append(bot.send_message(message.chat.id, "Верно!").message_id)
				right_answers += 1
			else:
				messages.append(bot.send_message(message.chat.id, f"Неверно!\nПравильный ответ:{right_date}").message_id)
			if counter < 10:
				hard_test(message.chat.id)
			else:
				is_hard_test = False
				bot.send_message(message.chat.id, f"Ваш результат: {right_answers}/10")
				for msg in messages:
					bot.delete_message(message.chat.id, msg)
				start_message(message)
	except Exception as Z:
		print(Z)


if __name__ == "__main__":
	try:
		bot.polling()
	except Exception as E:
		print(E)
		time.sleep(1)
