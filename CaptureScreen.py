# =============================================================================
# Nome file: CaptureScreen.py
# Autore: Vincenzo Scozzaro
# Repository: https://github.com/scozzaro/
#
# Copyright (c) 2025 Vincenzo Scozzaro
#
# Questo file è distribuito secondo i termini della Mozilla Public License, v. 2.0.
# Puoi ottenere una copia della licenza all'indirizzo: https://mozilla.org/MPL/2.0/
# In base a questa licenza:
# - Sei libero di usare, modificare e distribuire questo file, anche in progetti commerciali.
# - Le modifiche a questo file devono essere rilasciate sotto MPL 2.0.
# - Devono essere mantenuti i riferimenti all’autore e alla licenza.
#
# Il codice è fornito "così com'è", senza garanzie di alcun tipo di funzionamento o di errori
# =============================================================================

import tkinter as tk
from PIL import ImageGrab, ImageTk
import os
import time
import pyperclip
from io import BytesIO  # Importa BytesIO
import win32clipboard
from PIL import Image
from tkinter import filedialog
from tkinter import messagebox



class ScreenCaptureApp:
    def __init__(self, master):
        self.master = master
        master.title("Cattura Schermo Semplice")
        master.geometry("700x300")  # Imposta le dimensioni iniziali della finestra

        # Toolbar Frame
        self.toolbar = tk.Frame(master)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Pulsante Cattura
        self.capture_button = tk.Button(self.toolbar, text="Cattura", command=self.start_capture)
        self.capture_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Pulsante Salva
        self.save_button = tk.Button(self.toolbar, text="Salva", command=self.save_image)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_button.config(state=tk.DISABLED) # Inizialmente disabilitato

        # Pulsante Copia Immagine
        self.copy_button = tk.Button(self.toolbar, text="Copia Immagine", command=self.copy_image_to_clipboard)
        self.copy_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.copy_button.config(state=tk.DISABLED) # Inizialmente disabilitato

        # Pulsante Penna
        self.pen_button = tk.Button(self.toolbar, text="Penna", command=self.toggle_pen_mode)
        self.pen_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.pen_mode = False  # Modalità penna disabilitata di default
        self.last_draw = None  # Ultima posizione del disegno

        # Colore penna
        self.pen_color = "white"
        

        # Pulsante Seleziona Colore
        self.color_button = tk.Button(self.toolbar, text="Seleziona Colore", command=self.open_color_palette)
        self.color_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Label per mostrare il colore corrente della penna
        self.pen_color_label = tk.Label(self.toolbar, text=" ", bg=self.pen_color, width=3, height=1, relief=tk.SUNKEN, bd=2)
        self.pen_color_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Dimensione penna
        self.pen_width = 3  # valore iniziale
 

        # Frame per selezione dimensione penna
        self.pen_size_frame = tk.Frame(self.toolbar)
        self.pen_size_frame.pack(side=tk.LEFT, padx=5)


        # Pulsanti toggle per dimensione penna
        self.pen_size_3_button = self.create_pen_size_button(3)
        self.pen_size_3_button.pack(side=tk.LEFT)
 

        self.pen_size_6_button = self.create_pen_size_button(6)
        self.pen_size_6_button.pack(side=tk.LEFT)

        self.pen_size_9_button = self.create_pen_size_button(9)
        self.pen_size_9_button.pack(side=tk.LEFT)

        # Seleziona di default la dimensione 3 evidenziando il bottone in blu
        self.set_pen_size(3, self.pen_size_3_button)

        self.undo_stack = []
        self.redo_stack = []

        # Pulsante Undo
        self.undo_button = tk.Button(self.toolbar, text="Undo", command=self.undo)
        self.undo_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.undo_button.config(state=tk.DISABLED)

        # Pulsante Redo
        self.redo_button = tk.Button(self.toolbar, text="Redo", command=self.redo)
        self.redo_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.redo_button.config(state=tk.DISABLED)

        # Frame per l'anteprima dell'immagine
        self.preview_frame = tk.Frame(master)
        self.preview_frame.pack(fill="both", expand=True, pady=10, padx=10)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        # Label per visualizzare l'anteprima dell'immagine
        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.grid(row=0, column=0, sticky="nw")


        self.capture_window = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selection_rect = None
        self.full_screenshot = None  # Immagine completa dello schermo originale
        self.cropped_image = None
        self.preview_image = None # Oggetto ImageTk per la visualizzazione




        self.master.bind("<Configure>", self.on_resize)


    def push_undo(self):
        if self.cropped_image:
            self.undo_stack.append(self.cropped_image.copy())
            self.undo_button.config(state=tk.NORMAL)
            self.redo_stack.clear()
            self.redo_button.config(state=tk.DISABLED)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.cropped_image.copy())
            self.cropped_image = self.undo_stack.pop()
            self.update_preview()
            self.redo_button.config(state=tk.NORMAL)
            if not self.undo_stack:
                self.undo_button.config(state=tk.DISABLED)

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.cropped_image.copy())
            self.cropped_image = self.redo_stack.pop()
            self.update_preview()
            self.undo_button.config(state=tk.NORMAL)
            if not self.redo_stack:
                self.redo_button.config(state=tk.DISABLED)

    def create_pen_size_button(self, size):
        """Crea un pulsante per la dimensione della penna con un cerchio cliccabile."""
        canvas = tk.Canvas(self.pen_size_frame, width=30, height=30, highlightthickness=1, highlightbackground="gray")
        x0, y0 = 15 - size // 2, 15 - size // 2
        x1, y1 = 15 + size // 2, 15 + size // 2
        canvas.create_oval(x0, y0, x1, y1, fill=self.pen_color, outline="black")

        canvas.bind("<Button-1>", lambda e: self.set_pen_size(size, canvas))
        return canvas



    def set_pen_size(self, size, clicked_canvas):
        """Imposta la dimensione della penna e aggiorna l'aspetto dei pulsanti."""
        self.pen_width = size
        # Reimposta sfondo e bordo dei canvas
        for canvas in [self.pen_size_3_button, self.pen_size_6_button, self.pen_size_9_button]:
            canvas.config(bg="SystemButtonFace", highlightbackground="gray")  # sfondo predefinito
        # Evidenzia il canvas selezionato
        clicked_canvas.config(bg="blue", highlightbackground="blue")

        if size==3:
            print(3)
            self.pen_size_3_button.config(relief=tk.SUNKEN)
        else:
            print(33)
            self.pen_size_3_button.config(relief=tk.RAISED)
      


    def open_color_palette(self):
        colors = [
            "#000000", "#444444", "#888888", "#CCCCCC", "#FFFFFF",
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
            "#800000", "#008000", "#000080", "#808000", "#800080", "#008080"
        ]

        palette = tk.Toplevel(self.master)
        palette.title("Scegli un colore")
        palette.geometry("180x120")

        def select(c):
            self.pen_color = c
            self.pen_color_label.config(bg=c)  # <-- aggiorna colore mostrato nella label
            palette.destroy()

        for i, color in enumerate(colors):
            btn = tk.Button(palette, bg=color, width=3, height=1, command=lambda c=color: select(c))
            btn.grid(row=i // 6, column=i % 6, padx=2, pady=2)


    def toggle_pen_mode(self):
        if not self.preview_image:
            print("Nessuna immagine da disegnare.")
            return

        self.pen_mode = not self.pen_mode
        if self.pen_mode:
            self.pen_button.config(relief=tk.SUNKEN, text="Penna (ON)")
            self.enable_drawing()
        else:
            self.pen_button.config(relief=tk.RAISED, text="Penna")
            self.disable_drawing()

    def enable_drawing(self):
        self.preview_label.bind("<B1-Motion>", self.draw_on_image)
        self.preview_label.bind("<ButtonRelease-1>", self.reset_draw)

    def disable_drawing(self):
        self.preview_label.unbind("<B1-Motion>")
        self.preview_label.unbind("<ButtonRelease-1>")

    def draw_on_image(self, event):
        if not self.cropped_image:
            return

        # Calcola le coordinate relative all'immagine originale
        label_width = self.preview_label.winfo_width()
        label_height = self.preview_label.winfo_height()
        image_width, image_height = self.cropped_image.size
        ratio = min(label_width / image_width, label_height / image_height)

        x = int(event.x / ratio)
        y = int(event.y / ratio)

        if not self.last_draw:  # Primo punto del nuovo tratto
            self.push_undo()

        if self.last_draw:
            x0, y0 = self.last_draw
            draw = self.cropped_image.copy()
            from PIL import ImageDraw
            draw_tool = ImageDraw.Draw(self.cropped_image)
            draw_tool.line([x0, y0, x, y], fill=self.pen_color, width=self.pen_width)


            self.last_draw = (x, y)
            self.update_preview()
        else:
            self.last_draw = (x, y)

    def reset_draw(self, event):
        self.last_draw = None

    def start_capture(self):
        self.master.withdraw()  # Nasconde la finestra principale
        self.master.update_idletasks()  # Forza aggiornamento per nasconderla davvero

        # Aspetta brevemente per assicurarsi che la finestra sia sparita
        time.sleep(0.3)  # valore piccolo ma efficace

        # Cattura l'intero schermo prima di aprire la finestra opaca
        self.full_screenshot = ImageGrab.grab()

        # Crea una finestra trasparente a schermo intero per la selezione
        self.capture_window = tk.Toplevel(self.master)
        self.capture_window.attributes("-fullscreen", True)
        self.capture_window.attributes("-alpha", 0.2)  # Schermo opaco per la selezione

        self.canvas = tk.Canvas(self.capture_window, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.canvas.update()

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)

        x1, y1 = (min(self.start_x, cur_x), min(self.start_y, cur_y))
        x2, y2 = (max(self.start_x, cur_x), max(self.start_y, cur_y))

        if not self.selection_rect:
            self.selection_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2, outline="red", width=5)
        else:
            self.canvas.coords(self.selection_rect, x1, y1, x2, y2)

    def on_release(self, event):
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)

        x1 = int(min(self.start_x, self.end_x))
        y1 = int(min(self.start_y, self.end_y))
        x2 = int(max(self.start_x, self.end_x))
        y2 = int(max(self.start_y, self.end_y))

        bbox = (x1, y1, x2, y2)
        self.crop_and_preview(bbox)

        self.capture_window.destroy()  # Chiude la finestra di selezione
        self.master.deiconify()  # Rende visibile la finestra principale
        self.enable_save_copy_buttons()

    def crop_and_preview(self, bbox):
        try:
            # Ritaglia l'immagine originale non opaca
            self.cropped_image = self.full_screenshot.crop(bbox)
            print("Immagine ritagliata.")
            self.update_preview()
        except Exception as e:
            print(f"Errore durante il ritaglio dell'immagine: {e}")
            self.cropped_image = None

    def update_preview(self):
        if self.cropped_image:
            width, height = self.cropped_image.size
            frame_width = self.preview_frame.winfo_width()
            frame_height = self.preview_frame.winfo_height()

            if frame_width > 0 and frame_height > 0:
                ratio = min(frame_width / width, frame_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                resized_image = self.cropped_image.resize((new_width, new_height))
                self.preview_image = ImageTk.PhotoImage(resized_image)
                self.preview_label.config(image=self.preview_image)
            else:
                # Il frame potrebbe non avere ancora dimensioni definite, riprova dopo un po'
                self.master.after(100, self.update_preview)
        else:
            self.preview_label.config(image="")
            self.preview_image = None

    def on_resize(self, event):
        # Aggiorna l'anteprima solo se l'immagine è già stata catturata
        if self.cropped_image:
            self.update_preview()

    def save_image(self):
        if self.cropped_image:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All Files", "*.*")],
                title="Salva immagine come..."
            )
            if file_path:
                try:
                    self.cropped_image.save(file_path)
                    messagebox.showinfo("Salvataggio riuscito", f"Immagine salvata in:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Errore di salvataggio", f"Errore nel salvataggio del file:\n{str(e)}")
        else:
            messagebox.showwarning("Nessuna immagine", "Non c'è nessuna immagine da salvare.")
    
    def copy_image_to_clipboard(self):
        if self.cropped_image:
            try:
                output = BytesIO()
                # Converti in RGB e salva in formato BMP (senza header BMP per clipboard)
                self.cropped_image.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # Rimuove header BMP (i primi 14 byte)

                output.close()

                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                print("Immagine copiata negli appunti in formato compatibile (DIB/BMP).")
            except Exception as e:
                print(f"Errore durante la copia dell'immagine negli appunti: {e}")
        else:
            print("Nessuna immagine catturata da copiare.")

    def copy_image_to_clipboardOld(self):
        if self.cropped_image:
            try:
                output = BytesIO()
                self.cropped_image.convert("RGB").save(output, "BMP")
                data = output.getvalue()[14:]  # Remove BMP header
                pyperclip.copy(data)
                print("Immagine copiata negli appunti come BMP.")
            except Exception as e:
                print(f"Errore durante la copia dell'immagine negli appunti: {e}")
        else:
            print("Nessuna immagine catturata da copiare.")

    def enable_save_copy_buttons(self):
        self.save_button.config(state=tk.NORMAL)
        self.copy_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()
