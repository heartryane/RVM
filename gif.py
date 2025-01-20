import tkinter as tk
from PIL import Image, ImageTk

class AnimatedGIF:
    def __init__(self, root, gif_path, width=None, height=None, interval=100):
        """Initialize the AnimatedGIF object."""
        self.root = root
        self.interval = interval  # Frame update interval in milliseconds
        self.frames = []  # Store pre-loaded frames
        self.current_frame = 0
        self.running = False  # To control animation state

        # Label to display the GIF
        self.label = tk.Label(self.root)
        self.label.pack(fill=tk.BOTH, expand=True)

        # Load the GIF frames
        self.load_frames(gif_path, width, height)

    def load_frames(self, gif_path, width, height):
        """Load frames in the main thread to avoid UI lag."""
        gif = Image.open(gif_path)
        try:
            while True:
                # Resize each frame to the specified width and height
                frame = gif.copy().resize((width, height), Image.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frame))
                gif.seek(len(self.frames))  # Move to the next frame
        except EOFError:
            gif.close()  # Close the GIF file when all frames are loaded

        # Start the animation once all frames are loaded
        self.running = True
        self.animate_gif()

    def animate_gif(self):
        """Loop through GIF frames to create a smooth animation."""
        if not self.running or not self.frames:
            return  # Stop if not running or frames not loaded

        frame = self.frames[self.current_frame]
        self.label.config(image=frame)
        self.current_frame = (self.current_frame + 1) % len(self.frames)

        # Use `after` to schedule the next frame
        self.root.after(self.interval, self.animate_gif)

    def bind_click(self, callback):
        """Bind a click event to the label displaying the GIF."""
        self.label.bind("<Button-1>", callback)

    def stop_animation(self):
        """Stop the animation."""
        self.running = False

    def start_animation(self):
        """Start or resume the animation."""
        if not self.running:
            self.running = True
            self.animate_gif()