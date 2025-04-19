import dis
import io
import contextlib

def transform_text(text):
    # Predefined mapping for signs:
    sign_mapping = {
        '(': ')',
        ')': '(',
        '+': '-',
        '-': '+',
        '!': '?',
        '?': '!',
        ',': ';',
        ';': ','
        # Add more mappings for other punctuation as needed.
    }
    
    result = []
    for ch in text:
        if ch.isalpha():
            # Determine the base for uppercase or lowercase letters.
            base = ord('A') if ch.isupper() else ord('a')
            # Get the 0-25 index for the letter.
            index = ord(ch) - base
            # Multiply by 3 and wrap around with modulo 26.
            new_index = (index * 3) % 26
            # Convert back to the corresponding character.
            new_char = chr(new_index + base)
            result.append(new_char)
        elif ch in sign_mapping:
            # Replace the sign using the predefined mapping.
            result.append(sign_mapping[ch])
        else:
            # Leave other characters (e.g., spaces, numbers) unchanged.
            result.append(ch)
    return ''.join(result)

def main():
    # Prompt the user for input.
    user_input = input("Enter a string to encrypt: ")
    
    # Encrypt the input string.
    encrypted_text = transform_text(user_input)
    
    # Save the original and encrypted text in a file called "crypted.txt".
    with open("crypted.txt", "w") as file:
        file.write("Original: " + user_input + "\n")
        file.write("Encrypted: " + encrypted_text + "\n")
    
    # Display the result to the user.
    print("\nEncryption complete!")
    print("Original: ", user_input)
    print("Encrypted:", encrypted_text)
    
    # Ask the user if they want to disassemble the encryption function.
    choice = input("\nDo you want to disassemble the encryption function and save it to a file? (y/n): ")
    if choice.strip().lower() == 'y':
        # Capture the disassembled bytecode into a StringIO object.
        bytecode_output = io.StringIO()
        with contextlib.redirect_stdout(bytecode_output):
            dis.dis(transform_text)
        disassembled_code = bytecode_output.getvalue()
        
        # Write the disassembled bytecode to "disassembled.txt".
        with open("disassembled.txt", "w") as dis_file:
            dis_file.write(disassembled_code)
        
        print("\nDisassembled bytecode saved in 'disassembled.txt'.")

if __name__ == '__main__':
    main()
