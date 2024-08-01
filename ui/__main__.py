import fire
from .pillow import pillow
from .tkinter import tkinter


def main():
    """
    Entry point of the application.
    
    This function initializes the application and starts the main event loop.
    It uses the `fire` library to create a command-line interface with two options:
    - "tkinter": Starts the application using the tkinter library.
    - "pillow": Starts the application using the pillow library.
    """
    fire.Fire({"tkinter": tkinter, "pillow": pillow})


if __name__ == "__main__":
    main()
