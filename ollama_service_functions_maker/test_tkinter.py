# test_tkinter.py
import tkinter as tk

def test_tkinter():
    try:
        root = tk.Tk()
        root.title("Tkinter Test")
        label = tk.Label(root, text="If you can see this, Tkinter is working!")
        label.pack()
        root.after(3000, root.destroy)  # Close after 3 seconds
        root.mainloop()
        return True
    except Exception as e:
        print(f"Tkinter error: {str(e)}")
        return False

if __name__ == "__main__":
    if test_tkinter():
        print("Tkinter is working correctly!")
    else:
        print("There's a problem with Tkinter installation")