#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import shlex

def executeCommand(command):
    try:
        subprocess.run(shlex.split(command))
    except Exception as ex:
        print("Error: %s" % str(ex))

if __name__ == "__main__":
    # Open a prompt!
    while True:
        command = input("$ ").strip()
        
        if command == "exit":
            break
        elif command == "help":
            print("To-do! Implement this!")
        else:
            executeCommand(command)
