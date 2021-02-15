import telebot
import sqlite3
import time
from random import randint, choice, shuffle

bot = telebot.TeleBot("1116430701:AAFPkyp0vv9XEJcDJvIHo7eTUDHOR2nZiAU")

dates = open("dates.txt", "r+", encoding="utf-8").readlines()
for index in range(len(dates)): dates[index] = dates[index].replace("\n", "").split(" - ")

default_questions = 10


class Database:
	def __init__(self):
		try:
			self.connection = sqlite3.connect("users.db", check_same_thread=False)
			self.cursor = self.connection.cursor()
			self.cursor.execute("""create table if not exists users(user_id integer primary key, 
								questions integer,
								right_answers integer,
								done_tests integer,
								state text,
								counter integer,
								right_date text, 
								done_questions integer,
								to_delete text, 
								local_right_answers integer)""") # добавить количество пройдённых ответов
			self.connection.commit()
		except Exception as exception:
			print(f"ERROR raised at __init__(): {exception}")

	def add_user(self, user_id, questions, right_answers, done_tests, counter, right_date, done_questions, to_delete, local_right_answers):
		try:
			self.connection = sqlite3.connect("users.db", check_same_thread=False)
			self.cursor = self.connection.cursor()
			self.cursor.execute("insert into users values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (user_id, questions, right_answers, done_tests, "menu", counter, right_date, done_questions, to_delete, local_right_answers))
			self.connection.commit()
		except Exception as exception:
			print(f"ERROR raised at add_user(): {exception}")

	def update_user(self, user_id, parent, value):
		try:
			self.connection = sqlite3.connect("users.db", check_same_thread=False)
			self.cursor = self.connection.cursor()
			self.cursor.execute(f"update users set {parent}=? where user_id = ?;", (value, user_id))
			self.connection.commit()
		except Exception as exception:
			print(f"ERROR raised at update_user(): {exception}")

	def get_user(self, user_id):
		try:
			self.connection = sqlite3.connect("users.db", check_same_thread=False)
			self.cursor = self.connection.cursor()
			self.cursor.execute(f"select * from users where {user_id}")
			self.connection.commit()
			to_return = self.cursor.fetchall()[0]
			return {"user_id": to_return[0], "questions": to_return[1], "right_answers": to_return[2], "done_tests": to_return[3], "state": to_return[4], "counter": to_return[5], "right_date": to_return[6], "done_questions": to_return[7], "to_delete": to_return[8], "local_right_answers": to_return[9]}
		except Exception as exception:
			print(f"ERROR raised at get_user(): {exception}")

	def get_all_users(self):
		try:
			self.connection = sqlite3.connect("users.db", check_same_thread=False)
			self.cursor = self.connection.cursor()
			self.cursor.execute('select user_id from users;')
			self.connection.commit()
			return [i[0] for i in self.cursor.fetchall()]
		except Exception as exception:
			print(f"ERROR raised at get_all_users(): {exception}")


db = Database()


def inline_keyboard(buttons_text, callback_data):
	keyboard = telebot.types.InlineKeyboardMarkup()
	for text in buttons_text:
		keyboard.add(telebot.types.InlineKeyboardButton(text=text, callback_data=callback_data[buttons_text.index(text)]))
	return keyboard


def inline_exam(date_list, right_date):
	used_dates = [right_date]
	while len(used_dates) < 4:
		random_date = choice(date_list)
		if random_date[0] not in used_dates:
			used_dates.append(random_date[0])
		else:
			continue
	shuffle(used_dates)
	buttons = ["exam_wrong", "exam_wrong", "exam_wrong", "exam_wrong"]
	buttons[used_dates.index(right_date)] = "exam_right"
	return inline_keyboard(used_dates, buttons)


def exam_easy(chat_id):
	db.update_user(chat_id, "state", "exam_easy")
	number = randint(0, len(dates) - 1)
	date = dates[number][0]
	db.update_user(chat_id, "right_date", dates[number][0])
	bot.send_message(chat_id, f"{dates[number][1]}?", reply_markup=inline_exam(dates, date))


@bot.message_handler(commands=["start"])
def start_message(message):
	if isinstance(message, telebot.types.Message):
		chat_id = message.chat.id
	else:
		chat_id = message.id

	bot.send_message(chat_id, "Привет, это бот для подготовки к истории!", reply_markup=inline_keyboard(["Тестирование", "Пользователь", "Настройки"], ["exam", "user", "settings"]))
	if not db.get_all_users():
		db.add_user(chat_id, default_questions, 0, 0, 0, "0000", 0, "", 0)
	if chat_id not in db.get_all_users():
		db.add_user(chat_id, default_questions, 0, 0, 0, "0000", 0, "", 0)
	db.update_user(chat_id, "state", "menu")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
	try:
		chat_id = call.message.chat.id

		bot.answer_callback_query(callback_query_id=call.id, text='')
		bot.delete_message(chat_id, call.message.message_id)

		if db.get_user(chat_id)["state"] == "settings_set_questions":
			db.update_user(chat_id, "questions", int(call.data))
			start_message(call.from_user)

		if call.data == "exam_right":
			db.update_user(chat_id, "right_answers", db.get_user(chat_id)["right_answers"] + 1)
			db.update_user(chat_id, "local_right_answers", db.get_user(chat_id)["local_right_answers"] + 1)
			db.update_user(chat_id, "done_questions", db.get_user(chat_id)["done_questions"] + 1)
			db.update_user(chat_id, "to_delete", db.get_user(chat_id)["to_delete"] + str(bot.send_message(chat_id, f"{choice(['Верно', 'Правильно', 'Отлично'])}!").message_id) + ",")
		# На удаление

		elif call.data == "exam_wrong":
			db.update_user(chat_id, "to_delete", db.get_user(chat_id)["to_delete"] + str(bot.send_message(chat_id, f"{choice(['Неверно', 'Ошибка', 'Неправильно'])}!\nПравильная дата: {db.get_user(chat_id)['right_date']} г.").message_id) + ",")
			db.update_user(chat_id, "done_questions", db.get_user(chat_id)["done_questions"] + 1)
		# На удаление

		if db.get_user(chat_id)["state"] == "exam_easy":
			db.update_user(chat_id, "counter", db.get_user(chat_id)["counter"] + 1)
			if db.get_user(chat_id)["counter"] < db.get_user(chat_id)["questions"]:
				exam_easy(chat_id)
			else:
				db.update_user(chat_id, "done_tests", db.get_user(chat_id)["done_tests"] + 1)
				db.update_user(chat_id, "counter", 0)
				bot.send_message(chat_id, f"Результат: {db.get_user(chat_id)['local_right_answers']}/{db.get_user(chat_id)['questions']}") # \nВы бы получили оценку: {}")
				start_message(call.from_user)
				db.update_user(chat_id, "local_right_answers", 0)
				for message in db.get_user(chat_id)["to_delete"].split(",")[slice(0, -1)]:
					bot.delete_message(chat_id, int(message))
				db.update_user(chat_id, "to_delete", "")

		if call.data == "exam":
			db.update_user(chat_id, "state", "exam_main")
			db.update_user(chat_id, "counter", 0)
			bot.send_message(chat_id, "Выберите сложность:", reply_markup=inline_keyboard(["Просто", "Сложно", "Повторение", "Назад"], ["exam_easy", "exam_hard", "picture", "return"]))

		elif call.data == "picture":
			image = open("images/dates.png", "rb")
			db.update_user(chat_id, "to_delete", db.get_user(chat_id)["to_delete"] + str(bot.send_photo(call.message.chat.id, photo=image).message_id) + ",")
			image.close()
			start_message(call.from_user)

		elif call.data == "exam_hard":
			pass

		elif call.data == "exam_easy":
			for message in db.get_user(chat_id)["to_delete"].split(",")[slice(0, -1)]:
				bot.delete_message(chat_id, int(message))
			db.update_user(chat_id, "to_delete", "")
			exam_easy(chat_id)

		elif call.data == "user":
			db.update_user(chat_id, "state", "user_info")
			bot.send_message(chat_id, f"{call.from_user.first_name} {call.from_user.last_name if not not call.from_user.last_name else ''} ({call.from_user.username.title()})\nПройдено тестов: {db.get_user(chat_id)['done_tests']}\nПравильных ответов: {db.get_user(chat_id)['right_answers']}/{db.get_user(chat_id)['done_questions']}", reply_markup=inline_keyboard(["Назад"], ["return"]))

		elif call.data == "settings":
			db.update_user(chat_id, "state", "settings_main")
			bot.send_message(chat_id, f"Настройки:\nКоличество вопросов: {db.get_user(chat_id)['questions']}", reply_markup=inline_keyboard(["Установить количество вопросов в тестах", "Вернуть стандартные значения", "Назад"], ["settings_set_questions", "settings_set_default", "return"]))

		elif call.data == "settings_set_default":
			db.update_user(chat_id, "state", "settings_set_default")
			db.update_user(chat_id, "questions", default_questions)
			start_message(call.from_user)

		elif call.data == "settings_set_questions":
			db.update_user(chat_id, "state", "settings_set_questions")
			bot.send_message(chat_id, "Выберите количество вопросов в тесте:", reply_markup=inline_keyboard(["5", "10", "15"], [5, 10, 15]))

		elif call.data == "return":
			start_message(call.from_user)

	except Exception as exception:
		print(f"ERROR raised at get_all_users(): {exception}")


if __name__ == "__main__":
	bot.polling()