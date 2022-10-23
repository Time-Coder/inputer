import click
import os
import ctypes

class Inputer:
	def __init__(self, history_filename = None):
		self.__current_bytes = []
		self.__current_cursor = 0

		# Ctrl + H, Ctrl + I, Ctrl + M is not supported
		self.__ctrl_list = [b"\x01", b"\x02", b"\x03", b"\x04", b"\x05", b"\x06", b"\x07", b"\x0A", b"\x0B", b"\x0C", b"\x0E", b"\x0F", b"\x10", b"\x11", b"\x12", b"\x13", b"\x14", b"\x15", b"\x16", b"\x17", b"\x18", b"\x19", b"\x1A"]

		if history_filename is None:
			self.__history_file = None
			self.__history_cmds = []
			self.__history_index = len(self.__history_cmds)
		else:
			self.use_history(history_filename)
		self.__not_exe_cmd = ""
		self.__illegal_ch = "/\\:*<>?\"|"
		self.__is_block = False
		self.__is_hidden = False
		self.__prompt = ""
		self.__sent_ctrl_mode = "none"
		self.__new_line = False
		self.__appended_endl = False

	def __del__(self):
		if not self.__history_file is None:
			self.__history_file.close()

	def __count_bytes(self, bytes_array, for_del=False):
		result = 0
		for token in bytes_array:
			n = len(token)
			if n == 3:
				if for_del:
					n = 1
				else:
					n = 2
			result += n

		return result

	def __decode(self, bytes_array, decode_indent=False):
		result = ""
		for token in bytes_array:
			if token == '    ':
				if not decode_indent:
					result += token
				else:
					result += '\t'
			else:
				result += str(token, encoding="utf-8")
		return result

	def __encode(self, content):
		result = []
		for ch in content:
			if ch == '\t':
				result.append('    ')
			else:
				result.append(ch.encode("utf-8"))
		return result

	@property
	def current_str(self):
		return self.__decode(self.__count_bytes, True)

	@property
	def current_cursor(self):
		return self.__current_cursor

	def use_history(self, filename):
		if not os.path.isdir(os.path.dirname(os.path.abspath(filename))):
			os.makedirs(os.path.dirname(os.path.abspath(filename)))

		if os.path.isfile(filename):
			self.__history_cmds = open(filename).read().split("\n")
			self.__history_cmds = [self.__encode(cmd) for cmd in self.__history_cmds if cmd != ""]
		else:
			self.__history_cmds = []

		self.__history_index = len(self.__history_cmds)
		self.__history_file = open(filename, "a")

	def backspace(self, n = 1):
		n = min(n, self.__current_cursor)
		if n <= 0:
			return

		N = self.__count_bytes(self.__current_bytes[self.__current_cursor-n : self.__current_cursor])
		tail_str = self.__decode(self.__current_bytes[self.__current_cursor:]) + " "*N
		N_back = self.__count_bytes(self.__current_bytes[self.__current_cursor:]) + N
		self.__current_bytes = self.__current_bytes[:self.__current_cursor-n] + self.__current_bytes[self.__current_cursor:]
		self.__current_cursor -= n

		if not self.__is_hidden:
			print("\b"*N + tail_str + "\b"*N_back, end="", flush=True)

	def delete(self, n = 1):
		n = min(n, len(self.__current_bytes)-self.__current_cursor)
		if n <= 0:
			return

		N = self.__count_bytes(self.__current_bytes[self.__current_cursor : self.__current_cursor+n])
		tail_str = self.__decode(self.__current_bytes[self.__current_cursor+n:]) + " "*N
		N_back = self.__count_bytes(self.__current_bytes[self.__current_cursor+n:]) + N
		self.__current_bytes = self.__current_bytes[:self.__current_cursor] + self.__current_bytes[self.__current_cursor+n:]

		if not self.__is_hidden:
			print(tail_str + "\b"*N_back, end="", flush=True)

	def left(self, n = 1):
		n = min(n, self.__current_cursor)
		if n <= 0:
			return

		N = self.__count_bytes(self.__current_bytes[self.__current_cursor-n : self.__current_cursor])
		if not self.__is_hidden:
			print("\b"*N, end="", flush=True)

		self.__current_cursor -= n

	def right(self, n = 1):
		n = min(n, len(self.__current_bytes)-self.__current_cursor)
		if n <= 0:
			return

		if not self.__is_hidden:
			print(self.__decode(self.__current_bytes[self.__current_cursor:self.__current_cursor+n]), end="", flush=True)

		self.__current_cursor += n

	def up(self):
		if self.__history_index == 0:
			return

		if self.__history_index == len(self.__history_cmds):
			self.__not_exe_cmd = self.__current_bytes

		self.__history_index -= 1

		self.clear()
		self.insert(self.__decode(self.__history_cmds[self.__history_index], True))

	def down(self):
		if self.__history_index == len(self.__history_cmds):
			return

		self.__history_index += 1

		self.clear()
		if self.__history_index == len(self.__history_cmds):
			self.insert(self.__decode(self.__not_exe_cmd, True))
		else:
			self.insert(self.__decode(self.__history_cmds[self.__history_index], True))

	def insert(self, content):
		tail_str = self.__decode(self.__current_bytes[self.__current_cursor:])
		N_back = self.__count_bytes(self.__current_bytes[self.__current_cursor:])
		self.__current_bytes = self.__current_bytes[:self.__current_cursor] + self.__encode(content) + self.__current_bytes[self.__current_cursor:]
		if not self.__is_hidden:
			print(content.replace("\t", "    ") + tail_str + '\b'*N_back, end="", flush=True)
		self.__current_cursor += len(content)

	def clear(self):
		self.left(self.__current_cursor)
		self.delete(len(self.__current_bytes))

	def block(self):
		self.__is_block = True

	def unblock(self):
		self.__is_block = False

	def hide(self):
		if self.__is_hidden:
			return

		print("\033[G\033[K", end="", flush=True)
		self.__is_hidden = True

	def eprint_before(self, *args, **kwargs):
		kwargs["file"] = sys.stderr
		self.print_before(*args, **kwargs)

	def print_before(self, *args, **kwargs):
		if self.__is_hidden:
			print(*args, **kwargs)
			return

		if "end" not in kwargs:
			kwargs["end"] = "\n"
		if "sep" not in kwargs:
			kwargs["sep"] = " "

		result_str = ""
		for i in range(len(args)):
			result_str += str(args[i])
			if i != len(args)-1:
				result_str += kwargs["sep"]
		result_str += kwargs["end"]

		prefix = ""
		if self.__new_line:
			prefix = "\033[G\033[K"
			if self.__appended_endl:
				prefix += '\033[F'

			if self.__new_line and (len(result_str) == 0 or result_str[-1] != '\n'):
				result_str += "\n"
				self.__appended_endl = True
			else:
				self.__appended_endl = False
		else:
			N = self.__count_bytes(self.__current_bytes[self.__current_cursor:])
			N_back = self.__count_bytes(self.__encode(self.__prompt)) + self.__count_bytes(self.__current_bytes)

			prefix = " " * N + "\b" * N_back + " " * N_back + "\b" * N_back
			self.__appended_endl = False

		del kwargs["end"]
		del kwargs["sep"]
		print(prefix + \
			  result_str + \
			  self.__prompt + \
			  self.__decode(self.__current_bytes) + \
			  "\b"*(self.__count_bytes(self.__current_bytes[self.__current_cursor:])), \
			  end="", flush=True, **kwargs)

	def unhide(self):
		if self.__sent_ctrl_mode == "in_unhide":
			self.__sent_ctrl_mode = "in_hide"

		if not self.__is_hidden:
			return

		N_back = self.__count_bytes(self.__current_bytes[self.__current_cursor:])
		print(self.__prompt + self.__decode(self.__current_bytes) + "\b"*N_back, end="", flush=True)
		self.__is_hidden = False

	def input(self, __prompt = ""):
		self.__prompt = __prompt

		if self.__sent_ctrl_mode == "in_unhide":
			self.unhide()
		elif not self.__is_hidden:
			N_back = self.__count_bytes(self.__current_bytes[self.__current_cursor:])
			print(self.__prompt + self.__decode(self.__current_bytes) + "\b"*N_back, end="", flush=True)
			
		if self.__history_file is None:
			for ch in self.__illegal_ch:
				__prompt = __prompt.replace(ch, "_")
			self.use_history(os.path.dirname(os.path.abspath(__file__)) + "/history/$" + __prompt)
		
		while True:
			try:
				ch = click.getchar()
				raw = ch.encode("utf-8")
				self.__sent_ctrl_mode = "none"
				if raw in self.__ctrl_list:
					if self.__is_hidden:
						self.__sent_ctrl_mode = "in_hide"
					else:
						self.hide()
						self.__sent_ctrl_mode = "in_unhide"

					print("[ sent Ctrl + " + chr(ord('A')+int.from_bytes(raw, byteorder="little")-1) + " ]", flush=True)
					return raw

				if self.__is_block:
					continue
			except:
				continue

			if not (ch.isprintable() or ch in "\r\n\t\b"):
				continue

			if ch in "\n\r":
				print("", flush=True)
				result = self.__decode(self.__current_bytes, True)
				if result.replace(" ", "").replace("\t", "") != "":
					self.__history_cmds.append(self.__current_bytes)
					self.__history_file.write(result+"\n")
					self.__history_file.flush()
				self.__history_index = len(self.__history_cmds)
				self.__current_bytes = []
				self.__current_cursor = 0
				self.__prompt = ""
				return result
			elif ch == "\b":
				self.backspace()
			elif raw in [b"\xc3\xa0S", b"\x00S"]:
				self.delete()
			elif raw in [b"\xc3\xa0K", b"\x00K"]:
				self.left()
			elif raw in [b"\xc3\xa0M", b"\x00M"]:
				self.right()
			elif raw in [b"\xc3\xa0H", b"\x00H"]:
				self.up()
			elif raw in [b"\xc3\xa0P", b"\x00P"]:
				self.down()
			else:
				self.insert(ch)