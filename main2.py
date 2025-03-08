import cv2
import numpy as np
import pyautogui
import telebot
import time
import os
import random
from dotenv import load_dotenv
from threading import Event, Thread
from pynput.keyboard import Controller, Key
from pynput.mouse import Button, Controller as MouseController
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk  # Pillow kütüphanesi arka plan resmi için kullanılacak

# Load environment variables from .env file
load_dotenv()

# Telegram bot bilgilerinin güvenli bir şekilde alınması
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Check if the environment variables are set
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")
if TELEGRAM_CHAT_ID is None:
    raise ValueError("TELEGRAM_CHAT_ID environment variable is not set.")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Stop event for controlling the image search and key presses
stop_event = Event()
is_bot_running = False

# Keyboard and Mouse controllers for pressing keys and clicking
keyboard = Controller()
mouse = MouseController()

# OpenCV ile ekrandaki resmi ara ve koordinatlarını al
def find_image_on_screen(image_path, threshold=0.8):
    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    
    # Dosyanın var olup olmadığını kontrol et
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    template = cv2.imread(image_path, cv2.IMREAD_COLOR)
    
    if template is None:
        raise ValueError(f"Failed to read image file: {image_path}")
    
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        return True, max_loc
    else:
        return False, None

# Ekrandaki belirli bir görsele tıkla
def click_on_image(image_path, threshold=0.8):
    found, location = find_image_on_screen(image_path, threshold)
    if found:
        mouse.position = location
        time.sleep(0.1)  # Kısa bir süre bekle
        mouse.click(Button.left, 1)
        return True
    return False

# Telegram bildirimi gönder
def send_telegram_message(message):
    bot.send_message(TELEGRAM_CHAT_ID, message)

# Resim arama işlemini kontrol eden fonksiyon
def image_search_loop():
    image_path = r"C:\RulokatMain\RulosHand\Referances\bef.bmp"  # Kontrol edilecek resim dosyasının yolu
    spawn_image_path = r"C:\RulokatMain\RulosHand\Referances\spawn.bmp"  # Yeni eklenen resim dosyasının yolu
    
    while not stop_event.is_set():
        try:
            found = find_image_on_screen(image_path)[0]
            if not found:
                print("Görsel bulunamadı.")
                send_telegram_message("Envanter doldu")
            
            # Yeni eklenen görseli kontrol et ve tıkla
            if spawn_click_var.get() and click_on_image(spawn_image_path):
                print("Spawn görseline tıklandı.")
                send_telegram_message("Spawn görseline tıklandı.")
            
            time.sleep(10)  # 10 saniyede bir kontrol et
        except Exception as e:
            print(f"Hata: {e}")
            send_telegram_message(f"Hata: {e}")
            time.sleep(60)  # Bir dakika bekle

# Tuş basma işlemini gerçekleştiren fonksiyon (pynput kullanarak)
def press_key(key):
    keyboard.press(key)
    time.sleep(0.05)
    keyboard.release(key)

# Belirli tuşlara tıklama işlemini kontrol eden fonksiyon
def key_press_function(key, delay):
    while not stop_event.is_set():
        time.sleep(delay)
        if not stop_event.is_set():
            press_key(key)

# Z tuşuna basma işlemini kontrol eden fonksiyon
def z_key_press_loop():
    key = 'z'  # 'Z' tuşu
    while not stop_event.is_set():
        press_key(key)
        delay = random.uniform(0.05, 0.08)  # 50ms ile 80ms arasında rastgele bir süre
        time.sleep(delay)

# GUI işlevselliği
def start_bot():
    global is_bot_running
    if not is_bot_running:
        stop_event.clear()
        status_label.config(bg="green")  # Durum göstergesini yeşil yap
        Thread(target=delayed_start).start()  # 5 saniye gecikmeli başlatma
    else:
        send_telegram_message("Bot zaten çalışıyor.")

def delayed_start():
    time.sleep(5)  # 5 saniye bekle
    if not stop_event.is_set():  # Eğer hala durdurulmadıysa
        search_thread = Thread(target=image_search_loop)
        search_thread.start()

        keys = ['1', '2', '3', '4', Key.f1, Key.f2, Key.f3, Key.f4]
        for key in keys:
            entry = key_entries[key]
            delay_str = entry.get()
            if delay_str:
                try:
                    delay = float(delay_str)
                    key_press_thread = Thread(target=key_press_function, args=(key, delay))
                    key_press_thread.start()
                except ValueError:
                    print(f"Geçersiz giriş: {delay_str}")

        if z_key_var.get():
            z_key_press_thread = Thread(target=z_key_press_loop)
            z_key_press_thread.start()

        global is_bot_running
        is_bot_running = True
        send_telegram_message("Bot başlatıldı.")

def stop_bot():
    global is_bot_running
    if is_bot_running:
        stop_event.set()
        status_label.config(bg="red")  # Durum göstergesini kırmızı yap
        is_bot_running = False
        send_telegram_message("Bot durduruldu.")
    else:
        send_telegram_message("Bot zaten durdurulmuş.")

def on_closing():
    stop_bot()
    root.destroy()

# Z tuşu işaretleme kutusunun durumunu güncelleyen fonksiyon
def update_z_key_checkbutton():
    if z_key_var.get():
        z_key_checkbutton.config(fg="green")
    else:
        z_key_checkbutton.config(fg="white")

# Spawn görseli tıklama kutusunun durumunu güncelleyen fonksiyon
def update_spawn_click_checkbutton():
    if spawn_click_var.get():
        spawn_click_checkbutton.config(fg="green")
    else:
        spawn_click_checkbutton.config(fg="white")

# Main function to run the GUI
def main():
    global status_label, root, key_entries, z_key_var, z_key_checkbutton, spawn_click_var, spawn_click_checkbutton

    key_entries = {}

    # Create the main window
    root = tk.Tk()
    root.title("Rulokat's Hand")
    root.geometry("1024x576")  # Pencere boyutunu 1024x576 piksel olarak ayarla
    root.configure(bg="black")  # Arayüz çerçevesini siyah yap

    # Pencere ikonunu değiştir
    icon_path = r"C:\RulokatMain\RulosHand\Referances\icon.ico"
    root.iconbitmap(icon_path)

    # Arka plan resmi ekle
    bg_image_path = r"C:\RulokatMain\RulosHand\Referances\clientwp.jpg"
    bg_image = Image.open(bg_image_path)
    bg_image = bg_image.resize((1024, 576), Image.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)

    canvas = tk.Canvas(root, width=1024, height=576, bg="black")
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")

    font_style = font.Font(family="Helvetica", size=14, weight="bold")  # Başlıklar için daha büyük font
    button_font_style = font.Font(family="Helvetica", size=14, weight="bold")  # Butonlar için daha büyük font
    entry_font_style = font.Font(family="Helvetica", size=10, weight="bold")  # Diğer elemanlar için eski font

    # Create status label
    status_label = tk.Label(canvas, text="Durum", bg="red", width=20, height=2, font=entry_font_style)
    status_label.place(x=50, y=50)

    # Create start and stop buttons
    button_frame = tk.Frame(canvas, bg="black")
    button_frame.place(x=50, y=100)
    start_button = tk.Button(button_frame, text="Başlat", font=button_font_style, command=start_bot, width=12)
    start_button.pack(side=tk.LEFT, padx=5)
    stop_button = tk.Button(button_frame, text="Durdur", font=button_font_style, command=stop_bot, width=12)
    stop_button.pack(side=tk.LEFT, padx=5)

    # Beceriler başlığı
    beceriler_label = tk.Label(canvas, text="Beceriler", font=font_style, bg="black", fg="white")
    beceriler_label.place(x=50, y=200)

    # Beceriler tuşları
    beceriler_frame = tk.Frame(canvas, bg="black")
    beceriler_frame.place(x=50, y=240)
    for key in ['1', '2', '3', '4']:
        frame = tk.Frame(beceriler_frame, bg="black")
        frame.pack(side=tk.LEFT, padx=5)
        label = tk.Label(frame, text=f"{key} için süre (sn):", font=entry_font_style, bg="black", fg="white")
        label.pack(side=tk.TOP)
        entry = tk.Entry(frame, font=entry_font_style)
        entry.pack(side=tk.TOP)
        key_entries[key] = entry

    # İksirler başlığı
    iksirler_label = tk.Label(canvas, text="İksirler", font=font_style, bg="black", fg="white")
    iksirler_label.place(x=50, y=320)

    # İksirler tuşları
    iksirler_frame = tk.Frame(canvas, bg="black")
    iksirler_frame.place(x=50, y=360)
    for key in [Key.f1, Key.f2, Key.f3, Key.f4]:
        frame = tk.Frame(iksirler_frame, bg="black")
        frame.pack(side=tk.LEFT, padx=5)
        key_str = key.name
        label = tk.Label(frame, text=f"{key_str} için süre (sn):", font=entry_font_style, bg="black", fg="white")
        label.pack(side=tk.TOP)
        entry = tk.Entry(frame, font=entry_font_style)
        entry.pack(side=tk.TOP)
        key_entries[key] = entry

    # Z tuşu işaretleme kutusu
    z_key_var = tk.BooleanVar()
    z_key_checkbutton = tk.Checkbutton(canvas, text="Üçüncü El", variable=z_key_var, font=entry_font_style, bg="black", fg="white", command=update_z_key_checkbutton)
    z_key_checkbutton.place(x=50, y=450)

    # Spawn görseli tıklama kutusu
    spawn_click_var = tk.BooleanVar()
    spawn_click_checkbutton = tk.Checkbutton(canvas, text="Auto Respawn", variable=spawn_click_var, font=entry_font_style, bg="black", fg="white", command=update_spawn_click_checkbutton)
    spawn_click_checkbutton.place(x=200, y=450)

    # Telif hakkı metni
    copyright_label = tk.Label(canvas, text="© 2025 Rulokat. Tüm hakları saklıdır.", bg="black", fg="white", font=("Helvetica", 8))
    copyright_label.place(x=10, y=550)

    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()