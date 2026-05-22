# undertale spam helper

small personal script for undertale encounter farming.

made for self-use because i’m too lazy to manually spam up/down keys.

## setup

```bash
sudo apt update
sudo apt install python3.12-venv python3-pip python3-xlib xdotool

python3 -m venv undertale-env
source undertale-env/bin/activate
pip install pynput
````

## run

```bash
source undertale-env/bin/activate
python3 undertale_spam.py
```

## controls

| key   | action              |
| ----- | ------------------- |
| `f8`  | toggle up/down spam |
| `f6`  | faster              |
| `f7`  | slower              |
| `f10` | quit                |

## notes

focus undertale first, then press `f8`.

after that, you can alt-tab and it should keep spamming in undertale.

don’t forget to press `f8` again to stop.

```
