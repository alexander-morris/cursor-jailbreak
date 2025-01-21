def write_message():
    """Write the message about trying again and continuing from test-case.md"""
    message = "try again, continue from test-case.md - the timeout / unstuck script doesn't seem to be working"
    
    # Write to a file
    with open('message.txt', 'w') as f:
        f.write(message)
    
    # Also print to console
    print(f"Message written to message.txt:\n{message}")

if __name__ == "__main__":
    write_message() 