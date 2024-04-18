import streamlit as st
import pandas as pd
from datetime import date
from github_contents import GithubContents

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

def clear_input():
    import getpass, sys, termios
    import anthonyztools.cli as cli
    # Save the current state
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    try:
        # Set the terminal to raw mode
        tty = termios.tcgetattr(fd)
        tty[3] = (tty[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(fd, termios.TCSANOW, tty)

        # Get the password
        password = getpass.getpass("Enter password: ")

    finally:
        # Restore the original terminal state
        termios.tcsetattr(fd, termios.TCSAFLUSH, old)

    return password

def main():
    # Expected user credentials
    expected_username = "Muster Marta"
    expected_password = "Muster Master"

    # Get user input for username and password
    username = input("Enter username: ")
    password = clear_input()

    # Compare user input with expected credentials
    if username == expected_username and password == expected_password:
        print("Login successful!")
    else:
        print("Invalid credentials!")

if __name__ == "__main__":
    main()