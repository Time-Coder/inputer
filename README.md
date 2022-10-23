# inputer: Print before input

If you want to print something before Python default function input() prompt, you can use this package **inputer**. To achieve this, **inputer** give you a object to control input like this:

```python
import inputer
import threading
import time

input_handle = inputer.Inputer()

def always_print(input_handle):
    while True:
        input_handle.print_before("I am here!")
        time.sleep(1)

th = threading.Thread(target=always_print, args=(input_handle,), daemon=True)
th.start()

while True:
	text = input_handle.input("> ")
	if text == "exit":
		break
```

In addition, you can use following methods of `Inputer` to control input:
* `Inputer.input(prompt='')`: Just like Python default function `input`;
* `Inputer.print_before(*args, **kwargs)`: Just like Python default function `print` but print before input prompt;
* `Inputer.eprint_before(*args, **kwargs)`: Print before input prompt to stdandar error;
* `Inputer.left(n=1)`: Move current cursor back `n` position, just like press `left` key on keybord;
* `Inputer.right(n=1)`: Move current cursor forward `n` position, just like press `right` key on keybord;
* `Inputer.up(n=1)`: Change current input buffer to last input text, just like press `up` key on keybord;
* `Inputer.down(n=1)`: Change current input buffer to next input text, just like press `down` key on keybord;
* `Inputer.backspace(n=1)`: Left delete `n` characters, just like press `backspace` key on keybord;
* `Inputer.delete(n=1)`: Right delete `n` characters, just like press `del` key on keybord;
* `Inputer.current_str`: Get current input buffer text;
* `Inputer.current_cursor`: Get current cursor position;
* `Inputer.insert(text)`: Insert `text` at current cursor position;
* `Inputer.hide()`: Hide prompt text and user input text;
* `Inputer.unhide()`: Show prompt text and user input text again;
* `Inputer.block()`: Forbidden user input;
* `Inputer.unblock()`: Allow user input again;
* `Inputer.use_history(history_filename)`: All history input is saved in a history file even if you don't call this method. This method allow you to specify a history file to save history input in;