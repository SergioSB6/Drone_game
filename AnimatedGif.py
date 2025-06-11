import tkinter as tk  # Compatible con Python 3
from PIL import Image, ImageTk
from screeninfo import get_monitors

class AnimatedGif(tk.Label):
    """
    Clase para mostrar un GIF animado sin bloquear el mainloop de tkinter.
    Usa el método start_thread() para iniciar la animación.
    """

    def __init__(self, root, gif_file, delay=0.04):
        super().__init__(root)
        self.root = root
        self.gif_file = gif_file
        self.delay = delay  # En segundos, por ejemplo 0.04
        self.stop = False
        self._num = 0

        # Tamaño de pantalla
        self.monitors = get_monitors()
        self.width = self.monitors[0].width
        self.height = self.monitors[0].height

    def _animate(self):
        try:
            # Cargar fotograma actual
            self.gif = tk.PhotoImage(file=self.gif_file, format=f'gif -index {self._num}')
            self.gif_img = ImageTk.getimage(self.gif)
            self.gif_img = self.gif_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            self.gif = ImageTk.PhotoImage(self.gif_img)
            self.configure(image=self.gif)
            self._num += 1
        except tk.TclError:
            # Reiniciar la animación
            self._num = 0

        if not self.stop:
            # Repetir con after (no bloquea el mainloop)
            self.after(int(self.delay * 1000), self._animate)

    def start_thread(self):
        """Inicia la animación de forma segura usando .after()"""
        self.stop = False
        self._num = 0
        self._animate()

    def stop_thread(self):
        """Detiene la animación"""
        self.stop = True
