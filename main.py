# For checking if files entered exist
import os

# Should imitate some of the weirder behaviours of the LMC like:
#   - Negative flag stays on until a new value is loaded into the calculator
#       - this can only occur through a LDA or IN instrutcion
#       - this also means the negative flag is preserved between executions
#           of the program
#   - Using DAT instruction to insert code, and also do RCI
#   - Using labels as valid places to LDA from and STO to e.g.
"""
jumpHere IN
    LDA jumpHere # Loads value 901 (opcode for IN) into accumulator
    HLT

---

weird LDA weird # Loads value 500 (opcode for LDA + address 0) into accumulator
    HLT
"""
#   would also allow you to overwrite instructions/operands, which maybe could be used for some insane optimisation?

# Some aliases available
ADD = 100 # ADD
SUB = 200 # SUB, SUBTRACT
STO = 300 # STO, STORE
LDA = 500 # LDA, LOAD
BR  = 600 # BR
BRZ = 700 # BRZ
BRP = 800 # BRP
IN  = 901 # IN
OUT = 902 # OUT
HLT = 000 # HLT, HALT
DAT = -1  # DAT, DATA

# Editing this constant won't allow for your program to use more memory
MEMORY_MAX = 100

# Above N tests, it will only print tests you failed, not tests you succeeded
TEST_LOGGING_CUTOFF = 100

# TODO: test!
def splitByWhitespace(string : str) -> list:
    """
    Split a string by any whitespace character

    No part will be an empty string or a whitespace character itself
    e.g.
    "aa bb   cc  " -> ["aa", "bb", "cc"]
    """
    parts = []

    lastNonWhitespace = -1

    for i, character in enumerate(string):
        if character.isspace():
            if i != lastNonWhitespace and lastNonWhitespace != -1:
                parts.append(string[lastNonWhitespace:i])
                lastNonWhitespace = -1
        elif lastNonWhitespace == -1:
            lastNonWhitespace = i

    if lastNonWhitespace != -1:
        parts.append(string[lastNonWhitespace:])

    return parts

class Instruction(object):
    """
    Struct to represent an instruction
    label: Label giving alias to the address of the instruction/data
    opcode: Which operation to perform
    operand: Operand/data for that operation if applicable
    """
    def __init__(self, label : str, opcode : int, operand : str, line : int):
        self.label = label
        self.opcode = opcode
        self.operand = operand
        self.line = line

class Test(object):
    """
    Struct to represent a test
    name: Name of the test
    givenInputs: Inputs to enter into the program
    expectedOutput: Single output expected for the given inputs
    maxCycles: Maximum amount of F-E cycles before we assume program has gotten into an infinite loop
    """
    def __init__(self, name : str, givenInputs : list, expectedOutput : int, maxCycles : int):
        self.name = name
        self.givenInputs = givenInputs
        self.expectedOutput = expectedOutput
        self.maxCycles = maxCycles

# Combination of both semantic analysis and compiler
# i use big fancy jargon so i must be smart :)
class CompilerState(object):
    """
    Struct to hold current state of compiler

    registry: Maps a label to an address in memory (mailbox)
    memory: Memory containing opcodes and data values
    operands: Contains operands for instructions if they have one
    memoryIndex: First available index into memory
    """
    def __init__(self):
        self.registry = {}
        self.memory = [0,] * MEMORY_MAX
        self.operands = [None,] * MEMORY_MAX
        self.memoryIndex = 0

def compilerGetNextAvailable(compiler : CompilerState) -> int:
    """
    Get next available index in memory for an instruction/data
    """
    if compiler.memoryIndex == MEMORY_MAX:
        raise RuntimeError("Ran out of space for instructions/data")
    
    available = compiler.memoryIndex
    compiler.memoryIndex += 1

    return available

def compilerAddLabelToRegistry(label : str, value : int, compiler : CompilerState) -> None:
    # Check label is not already in compiler registry
    if label in compiler.registry.keys():
        raise RuntimeError(f"Label {label} had >1 data locations associated with it")
    
    # Add label to registry
    compiler.registry[label] = value

def compilerReadDataInstruction(instruction : Instruction, compiler : CompilerState) -> None:
    """
    Allocate memory for a data instruction, and set initial value
    """
    # Get index to store data at
    dataIndex = compilerGetNextAvailable(compiler)
    # Add label to compiler registry
    compilerAddLabelToRegistry(instruction.label, dataIndex, compiler)
    # Add initial value to memory
    compiler.memory[dataIndex] = int(instruction.operand)

def compilerReadInstruction(instruction : Instruction, compiler : CompilerState) -> None:
    """
    Allocate memory for an instruction, and store operand if it has one
    """
    # If it's a data instruction, handle accordingly
    if instruction.opcode == DAT:
        return compilerReadDataInstruction(instruction, compiler)

    instructionIndex = compilerGetNextAvailable(compiler)
    
    if instruction.label is not None:
        compilerAddLabelToRegistry(instruction.label, instructionIndex, compiler)
    
    # Add opcode and operand to compiler
    compiler.memory[instructionIndex] = instruction.opcode
    compiler.operands[instructionIndex] = instruction.operand

def compilerConsolidateLabels(compiler : CompilerState) -> None:
    """
    Lookup each label referenced in an operand, find address, and add to opcode
    """
    for i in range(MEMORY_MAX):
        operand = compiler.operands[i]

        # We have an operand for this instruction
        if operand is not None:
            # Lookup address
            address = compiler.registry.get(operand)

            # Label referenced doesn't exist
            if address is None:
                raise RuntimeError(f"Unrecognised label: '{operand}' in mailbox {i}")
            else:
                # TODO: is it possible to attach an operand to an instruction which doesn't take one?
                #   does it raise an error, or does it just add and cause some weird bugs
                #   should check since we're trying to perfectly imitate behaviour

                # Add address to opcode
                compiler.memory[i] += address

class ProgramState(object):
    """
    Struct to hold current state of a running program

    memory: Memory containing instructions and data of program
    accumulator: Value stored in calculator
    programCounter: Stored address of next instruction to execute
    negativeFlag: Set when a subtraction would cause an underflow. Reset upon LDA/IN
    haltFlag: Indicated if the program should halt
    inputs: Stores inputs of ONLY THE LAST RUN (not preserved like LMC) (Stored in reverse order in test mode)
    outputs: Stores outputs of ONLY THE LAST RUN (not preserved like LMC)
    testMode: Indicates whether we should request user input (False) or read from inputs array (True)
    """
    def __init__(self):
        self.memory = [0,] * MEMORY_MAX
        self.accumulator = 0
        self.programCounter = 0

        self.negativeFlag = False
        self.haltFlag = False

        self.inputs = []
        self.outputs = []

        self.testMode = False

def interpreterSetAccumulator(value : int, opcode : int, state : ProgramState) -> None:
    if value >= 0:
        state.accumulator = value
        # Only reset the negative flag if loading a new value, not upon addition/subtraction
        if opcode in (LDA, IN):
            state.negativeFlag = False
    else:
        # Roll-over
        state.accumulator = value + 1000
        state.negativeFlag = True

def interpreterExecuteOutput(state : ProgramState) -> None:
    if not state.testMode:
        print(f"Output: {state.accumulator}")

    state.outputs.append(state.accumulator)

def interpreterExecuteInput(state : ProgramState) -> None:
    value = None

    if not state.testMode:
        userInput = input("Input: ")

        while not (userInput.isdigit() and len(userInput) <= 3):
            print("Invalid input!")
            userInput = input("Input: ")

        value = int(userInput)

    else:
        if len(state.inputs) == 0:
            raise RuntimeError("Ran out of inputs to use for a test!")

        # Get last input in state inputs list
        value = state.inputs[-1]
        # Pop last input
        state.inputs.pop()

    interpreterSetAccumulator(value, IN, state)

def interpreterExecuteAdd(address : int, state : ProgramState) -> None:
    interpreterSetAccumulator((state.accumulator + state.memory[address]) % 1_000, ADD, state)

def interpreterExecuteSubtract(address : int, state : ProgramState) -> None:
    interpreterSetAccumulator(state.accumulator - state.memory[address], SUB, state)

def interpreterExecuteStore(address : int, state : ProgramState) -> None:
    state.memory[address] = state.accumulator

def interpreterExecuteLoad(address : int, state : ProgramState) -> None:
    interpreterSetAccumulator(state.memory[address], LDA, state)

def interpreterExecuteHalt(state : ProgramState) -> None:
    state.haltFlag = True

def interpreterExecuteBranch(address : int, state : ProgramState) -> None:
    state.programCounter = address

def interpreterExecuteBranchZero(address : int, state : ProgramState) -> None:
    if state.accumulator == 0:
        state.programCounter = address

def interpreterExecuteBranchPositive(address : int, state : ProgramState) -> None:
    if not state.negativeFlag:
        state.programCounter = address

INTERPRETER_JUMP_TABLE = [
    None,                               # 0 (HALT)
    interpreterExecuteAdd,              # 1 ADD
    interpreterExecuteSubtract,         # 2 SUB
    interpreterExecuteStore,            # 3 STO
    None,                               # 4 (NONE)
    interpreterExecuteLoad,             # 5 LDA
    interpreterExecuteBranch,           # 6 BR
    interpreterExecuteBranchZero,       # 7 BRZ
    interpreterExecuteBranchPositive,   # 8 BRP
    None                                # 9 (IN, OUT)
]

def interpreterAdvance(state : ProgramState) -> None:
    # Get current instruction
    instruction = state.memory[state.programCounter]

    # Increment program counter
    state.programCounter += 1

    # Get opcode and operand of instruction
    opcode = instruction // 100
    operand = instruction - opcode * 100

    if instruction == OUT:
        interpreterExecuteOutput(state)
    elif instruction == IN:
        interpreterExecuteInput(state)
    elif instruction == HLT:
        interpreterExecuteHalt(state)
    else:
        INTERPRETER_JUMP_TABLE[opcode](operand, state)

def interpreterLoadCompiler(program : ProgramState, compiler : CompilerState) -> None:
    # Load memory
    for i in range(MEMORY_MAX):
        program.memory[i] = compiler.memory[i]

def parserGetOpcode(operationName : str) -> int:
    if operationName in ("HLT", "HALT"):
        return HLT
    elif operationName == "ADD":
        return ADD
    elif operationName in ("STO", "STORE"):
        return STO
    elif operationName in ("SUB", "SUBTRACT"):
        return SUB
    elif operationName in ("LDA", "LOAD"):
        return LDA
    elif operationName == "OUT":
        return OUT
    elif operationName == "IN":
        return IN
    elif operationName == "BR":
        return BR
    elif operationName == "BRZ":
        return BRZ
    elif operationName == "BRP":
        return BRP
    elif operationName in ("DAT", "DATA"):
        return DAT

    raise RuntimeError(f"Unrecognised operation: {operationName}")

def parserReadInstruction(instruction : str, line : int) -> Instruction:
    label = None
    operation = None
    operand = None

    # Get all non whitespace parts of the instruction split by space
    parts = splitByWhitespace(instruction)

    # Case where a line is just whitespace or empty string
    if len(parts) == 0:
        return None

    # Check for some whitespace at start of instruction
    # This indicates an instruction without a label
    if instruction[0].isspace():
        # Operation is thus the 1st part since there's no label
        operation = parts[0]

        if len(parts) > 1:
            operand = parts[1]

    # Indicates instruction starts with a label
    else:
        label = parts[0]
        operation = parts[1]

        # If there is an operand, include it as well
        if len(parts) > 2:
            operand = parts[2]

    opcode = parserGetOpcode(operation)

    # Ensure operand is a digit
    if opcode == DAT and not (operand is not None and operand.isdigit() and len(operand) <= 3):
        raise RuntimeError(f"Data instruction must have 3 or fewer digit integer operand, but got {operand}")
    # TODO: Ensure operand is valid identifier, if LMC enforces it
    else:
        pass

    return Instruction(label, opcode, operand, line)

def compilerCompileLines(lines : list, compiler : CompilerState) -> None:
    for i, line in enumerate(lines):
        # Replace \n at the end of line
        if line[:-1] == "\n":
            line = line[:-1]

        # Replace any comments
        commentIndex = line.find("#")

        # If a comment was found
        if commentIndex != -1:
            # Remove the commented part of text
            line = line[:commentIndex]

        # If line is not now empty
        if line != "":
            newInstruction = parserReadInstruction(line, i)

            # Will return None for some inputs
            if newInstruction != None:
                compilerReadInstruction(newInstruction, compiler)

    compilerConsolidateLabels(compiler)

def runProgram(state : ProgramState, maxCycles = 1_000_000) -> int:
    """
    Executes program to completion, returning number of F-E cycles
    """
    FECycles = 0

    #  and FECycles <= maxCycles
    while not state.haltFlag:
        interpreterAdvance(state)
        # TODO: BAD! FECycles != instructions executed AFAIK!
        FECycles += 1

    return FECycles

def softResetProgram(state : ProgramState) -> None:
    """
    Performs soft reset on halt flag, inputs, outputs so program can be run again
    Does NOT reload initial values of data, this is something you have to do yourself
    """
    state.haltFlag = False
    # Behaviour here varies slightly, in LMC, these inputs and outputs would remain visible,
    # but to simplify testing, I'm clearing them on each run
    state.inputs = []
    state.outputs = []

def runTestMode(tests : list, state : ProgramState) -> None:
    disableLogging = len(tests) > TEST_LOGGING_CUTOFF

    testResults = []

    state.testMode = True

    for testIndex, currentTest in enumerate(tests):
        # Reverse given inputs since State::inputs behaves a bit like a stack                
        state.inputs = [currentTest.givenInputs[i] for i in range(len(currentTest.givenInputs) - 1, -1, -1)]
        if not disableLogging:
            print(f"Running test {currentTest.name} with inputs: {currentTest.givenInputs}, expecting {currentTest.expectedOutput}")

        cycles = runProgram(state)

        testSucceeded = len(state.outputs) == 1 and state.outputs[0] == tests[testIndex].expectedOutput
        testResults.append(testSucceeded)

        if testSucceeded:
            if not disableLogging:
                print(f"Test {testIndex + 1}: '{currentTest.name}' passed in {cycles} F-E cycles")
        else:
            reason = None

            if cycles > currentTest.maxCycles:
                reason = f"Exceeded maximum instructions {currentTest.maxInstructions}"

            else:
                output = None if len(state.outputs) < 1 else state.outputs
                reason = f"For input {currentTest.givenInputs} expected {currentTest.expectedOutput}, but got {output} instead"

            print(f"Test {testIndex + 1}: '{currentTest.name}' failed -> {reason}")

        softResetProgram(state)

    print(f"{sum(testResults)}/{len(tests)} passed")

def runUserMode(state : ProgramState) -> None:
    cycles = runProgram(state)
    softResetProgram(state)

    print(f"Program ended in {cycles} F-E cycles")

# Entrypoint/driver code
if __name__ == "__main__":
    sourceFilename = input("Enter source code file: ")

    while not os.path.exists(sourceFilename):
        print(f"Couldn't find file {sourceFilename}?")
        sourceFilename = input("Enter source code file: ")

    # Expected format for a test is:
    # name;input;input;input;output;maxCycles
    # As many inputs as the program asks for, with one single output, and maxCycles
    # being how many F-E cycles should be run before we assume you got stuck in an
    # infinite loop
    # Example (for the mean of 3 numbers):
    # zero-test:0;1;0;0;50000
    # big-test:999;333;666;666;50000
    # ...
    # Multiple tests can be in the same file, just separated by a newline
    testFilename = input("Enter filename for tests to run, or leave blank to run no tests: ")

    while not (os.path.exists(testFilename) or testFilename == ""):
        print(f"Couldn't find file {testFilename}?")
        testFilename = input("Enter filename for tests to run, or leave blank to run no tests: ")

    # Declare compiler state variable
    compilerState = CompilerState()

    # Compile sourcecode
    with open(sourceFilename, "r") as f:
        compilerCompileLines(f.readlines(), compilerState)

    print(f"Finished compilation successfully, using {compilerState.memoryIndex} mailboxes")

    # Declare program state variable
    programState = ProgramState()

    # Load compiled program into state
    interpreterLoadCompiler(programState, compilerState)

    # Read in tests if we have any
    tests = []

    if testFilename != "":
        with open(testFilename, "r") as f:
            lines = f.readlines()

            for i, line in enumerate(lines):
                # Remove newline
                line = line[:-1]
                # If line starts with a comment, is whitespace or empty
                if line[0] == "#" or line.isspace() or line == "":
                    continue

                parts = line.split(";")

                if len(parts) < 4:
                    raise RuntimeError(f"Too few arguments in test definition on line {i}, expected at least 4")

                # This line is a warcrime
                tests.append(Test(parts[0], [int(part) for part in parts[1:-2]], int(parts[-2]), int(parts[-1])))

    while input("Type 'exit' to exit program, type anything else to run program: ").lower() != 'exit':
        if len(tests) > 0:
            runTestMode(tests, programState)
        else:
            runUserMode(programState)

print("Goodbye")