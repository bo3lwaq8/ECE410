import re
from collections import Counter

def parse_disassembled_file(filename):
    """
    Reads the disassembled bytecode from a file and counts the occurrences
    of each instruction (opname).
    """
    # The regex pattern below expects lines that start with some whitespace,
    # then a number (line number), more whitespace, another number (offset),
    # more whitespace, then the instruction mnemonic (a word).
    pattern = re.compile(r'^\s*\d+\s+\d+\s+(\w+)')
    counts = Counter()
    
    with open(filename, 'r') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                opname = match.group(1)
                counts[opname] += 1
    return counts

if __name__ == '__main__':
    filename = 'de_disassembly.txt' #change to disassembled.txt for cryptogrpahy and tsp_disassembly.txt
    instruction_counts = parse_disassembled_file(filename)
    
    print(f"Instruction counts from {filename}:")
    for opname, count in sorted(instruction_counts.items()):
        print(f"{opname}: {count}")
