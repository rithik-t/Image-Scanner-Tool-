import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import ImageTk, Image
import backend

class ImageScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Scanner Tool")

        self.label = tk.Label(root, text="Upload an Image", font=("Helvetica", 14))
        self.label.pack(pady=10)

        self.upload_btn = tk.Button(root, text="Choose Image", command=self.upload_image)
        self.upload_btn.pack(pady=5)

        self.image_label = tk.Label(root)
        self.image_label.pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
        self.result_text.pack(padx=10, pady=10)

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if not file_path:
            return

        # Show thumbnail
        img = Image.open(file_path)
        img.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(img)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

        self.result_text.delete(1.0, tk.END)

        try:
            text = backend.extract_text(file_path)
            description = backend.describe_image(file_path)
            metadata = backend.extract_metadata(file_path)
            is_ai = backend.is_ai_generated_by_exif(metadata)

            self.result_text.insert(tk.END, f"📝 Extracted Text:\n{text}\n\n")
            self.result_text.insert(tk.END, f"📸 Image Description:\n{description}\n\n")
            self.result_text.insert(tk.END, "📂 Metadata:\n")
            for key, value in metadata.items():
                self.result_text.insert(tk.END, f"{key}: {value}\n")

            # Show GPS info if available
            if 'GPS Latitude' in metadata and 'GPS Longitude' in metadata:
                self.result_text.insert(tk.END, f"\n📍 Location Info:\n")
                self.result_text.insert(tk.END, f"Latitude: {metadata['GPS Latitude']}\n")
                self.result_text.insert(tk.END, f"Longitude: {metadata['GPS Longitude']}\n")
                self.result_text.insert(tk.END, f"Google Maps: {metadata['Google Maps Location']}\n")

            self.result_text.insert(tk.END, f"\n🤖 AI Detection: {'Likely AI-generated' if is_ai else 'Likely Real Photo'}\n")

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageScannerApp(root)
    root.mainloop()
