import tkinter as tk
import random
import math

class ValentineApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("💌 for shey 💌")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#fff0f5")
        self.root.eval('tk::PlaceWindow . center')

        self.no_clicks = 0
        self.no_btn = None
        self.yes_btn = None
        self.floating_labels = []
        self.heart_angle = 0

        self.no_texts = [
            "nope!! 🙈",
            "wrong button babe 💅",
            "that's not an option!! 🌸",
            "did you mean YES? 🤭",
            "hehe nice try!! 💕",
            "i said what i said 😤",
            "sheyyyy... 🥺",
            "babe ur so silly omg 🎀",
            "the answer is yes btw 💋",
            "okay fine... YES!! 💖",
        ]

        self.show_envelope_screen()
        self.animate_bg_hearts()
        self.root.mainloop()

    # ── tiny floating heart emitters ──────────────────────────────────────────
    def animate_bg_hearts(self):
        if random.random() < 0.4:
            x = random.randint(20, 480)
            lbl = tk.Label(self.root, text=random.choice(["💗","💓","💖","🌸","✨"]),
                           font=("Helvetica", random.randint(10,18)),
                           bg="#fff0f5", fg="#ffb6c1")
            lbl.place(x=x, y=460)
            self.floating_labels.append([lbl, x, 460, random.uniform(-0.5,0.5)])

        still_alive = []
        for item in self.floating_labels:
            lbl, x, y, drift = item
            y -= 2
            x += drift
            if y < -20:
                try: lbl.destroy()
                except: pass
            else:
                try:
                    lbl.place(x=int(x), y=int(y))
                    item[1] = x; item[2] = y
                    still_alive.append(item)
                except: pass
        self.floating_labels = still_alive
        self.root.after(60, self.animate_bg_hearts)

    # ── screen 1: envelope ────────────────────────────────────────────────────
    def show_envelope_screen(self):
        self.clear()

        tk.Label(self.root, text="✨ 💌 ✨", font=("Helvetica", 28),
                 bg="#fff0f5", fg="#ff85a1").pack(pady=(60, 8))

        tk.Label(self.root, text="shey,\nyou have a letter 🎀",
                 font=("Georgia", 18, "italic"), bg="#fff0f5",
                 fg="#c0567a", justify="center").pack(pady=6)

        tk.Label(self.root, text="( it's very important!! )",
                 font=("Helvetica", 11), bg="#fff0f5",
                 fg="#ffadc7").pack(pady=2)

        btn = tk.Button(self.root, text="  💌  open me  💌  ",
                        font=("Georgia", 15, "bold"),
                        bg="#ff85a1", fg="white",
                        activebackground="#ff5c8a",
                        activeforeground="white",
                        relief="flat", cursor="heart",
                        padx=20, pady=10,
                        command=self.show_message_screen)
        btn.pack(pady=40)

        # pulse the button
        self._pulse(btn, True)

    def _pulse(self, btn, grow):
        try:
            size = 16 if grow else 14
            btn.config(font=("Georgia", size, "bold"))
            self.root.after(600, lambda: self._pulse(btn, not grow))
        except: pass

    # ── screen 2: sweet message ───────────────────────────────────────────────
    def show_message_screen(self):
        self.clear()

        tk.Label(self.root, text="💖", font=("Helvetica", 36),
                 bg="#fff0f5", fg="#ff85a1").pack(pady=(40, 4))

        msg = (
            "hey shey 🌸\n\n"
            "of all the people in the world,\n"
            "i'm so glad it's you i get to love. 💕\n\n"
            "you make my heart go\n"
            "\"butterflies, butterflies, butterflies!!\"\n\n"
            "so i made you this tiny program\n"
            "just to say...\n\n"
            "i really, really love you. 🥹✨"
        )

        tk.Label(self.root, text=msg,
                 font=("Georgia", 13, "italic"),
                 bg="#fff0f5", fg="#c0567a",
                 justify="center", wraplength=420).pack(pady=4)

        btn = tk.Button(self.root, text="  keep reading 💌  ",
                        font=("Georgia", 13, "bold"),
                        bg="#ff85a1", fg="white",
                        activebackground="#ff5c8a",
                        activeforeground="white",
                        relief="flat", cursor="heart",
                        padx=18, pady=8,
                        command=self.show_question_screen)
        btn.pack(pady=20)

    # ── screen 3: the question ────────────────────────────────────────────────
    def show_question_screen(self):
        self.clear()
        self.no_clicks = 0

        tk.Label(self.root, text="🌸 💗 🌸", font=("Helvetica", 22),
                 bg="#fff0f5", fg="#ff85a1").pack(pady=(32, 4))

        tk.Label(self.root, text="will you be my valentine,",
                 font=("Georgia", 20, "italic"),
                 bg="#fff0f5", fg="#c0567a").pack()

        tk.Label(self.root, text="shey? 🥺💕",
                 font=("Georgia", 24, "bold"),
                 bg="#fff0f5", fg="#ff5c8a").pack(pady=(2, 4))

        tk.Label(self.root, text="i love you 💖",
                 font=("Georgia", 16, "italic"),
                 bg="#fff0f5", fg="#d46a8a").pack(pady=(0, 28))

        btn_frame = tk.Frame(self.root, bg="#fff0f5")
        btn_frame.pack()

        self.yes_btn = tk.Button(btn_frame,
                                 text="  YES of course!! 💖  ",
                                 font=("Georgia", 14, "bold"),
                                 bg="#ff85a1", fg="white",
                                 activebackground="#ff5c8a",
                                 activeforeground="white",
                                 relief="flat", cursor="heart",
                                 padx=16, pady=10,
                                 command=self.show_yes_screen)
        self.yes_btn.grid(row=0, column=0, padx=14)

        self.no_btn = tk.Button(btn_frame,
                                text="no 🙁",
                                font=("Helvetica", 10),
                                bg="#ffd6e7", fg="#c0567a",
                                activebackground="#ffd6e7",
                                activeforeground="#c0567a",
                                relief="flat", cursor="X_cursor",
                                padx=8, pady=6,
                                command=self.no_button_clicked)
        self.no_btn.grid(row=0, column=1, padx=14)

    def no_button_clicked(self):
        idx = min(self.no_clicks, len(self.no_texts) - 1)
        self.no_clicks += 1

        # shrink "no" button each click, grow "yes" button
        no_size = max(6, 10 - self.no_clicks)
        yes_size = min(20, 14 + self.no_clicks * 1)

        try:
            self.no_btn.config(text=self.no_texts[idx],
                               font=("Helvetica", no_size))
            self.yes_btn.config(font=("Georgia", yes_size, "bold"))
        except: pass

        # after enough clicks, hide "no" entirely
        if self.no_clicks >= len(self.no_texts):
            try: self.no_btn.destroy()
            except: pass

    # ── screen 4: yay!! ───────────────────────────────────────────────────────
    def show_yes_screen(self):
        self.clear()

        tk.Label(self.root, text="💖✨💖✨💖",
                 font=("Helvetica", 26),
                 bg="#fff0f5", fg="#ff85a1").pack(pady=(40, 6))

        tk.Label(self.root, text="YAY!! 🎉",
                 font=("Georgia", 32, "bold"),
                 bg="#fff0f5", fg="#ff5c8a").pack(pady=4)

        tk.Label(self.root,
                 text="i knew you'd say yes!! 🥹\nyou just made me the happiest girl ever!! 💕\n\ni love you so much, shey.\n\nhappy valentine's day!! 🌹",
                 font=("Georgia", 15, "italic"),
                 bg="#fff0f5", fg="#c0567a",
                 justify="center").pack(pady=12)

        tk.Label(self.root, text="🌸 🩷 💌 🩷 🌸",
                 font=("Helvetica", 22),
                 bg="#fff0f5", fg="#ffadc7").pack(pady=8)

        tk.Button(self.root, text="  mwah!! 💋  ",
                  font=("Georgia", 13, "bold"),
                  bg="#ff85a1", fg="white",
                  activebackground="#ff5c8a",
                  activeforeground="white",
                  relief="flat", cursor="heart",
                  padx=16, pady=8,
                  command=self.root.destroy).pack(pady=10)

    # ── helpers ───────────────────────────────────────────────────────────────
    def clear(self):
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Label) or widget not in [l[0] for l in self.floating_labels]:
                try: widget.destroy()
                except: pass
        # just destroy everything except we'll let floating hearts re-add themselves
        for widget in self.root.winfo_children():
            try: widget.destroy()
            except: pass
        self.floating_labels = []


if __name__ == "__main__":
    ValentineApp()