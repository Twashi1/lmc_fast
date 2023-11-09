# I made multiple very questionable design decisions when writing this code
# mainly because I did not make a single design decision and just bodged
# my way through to a kinda-working program

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

class Instruction:
    def __init__(self, address, opcode, operand, line):
        self.address = address
        self.opcode = opcode
        self.operand = operand
        self.line = line

class Test:
    def __init__(self, name, givenInputs, expectedOutput, maxInstructions):
        self.name = name
        self.givenInputs = givenInputs
        self.expectedOutput = expectedOutput
        self.maxInstructions = maxInstructions

class CompilerState:
    def __init__(self):
        # Mapping an address name to a memory cell
        self.registry = {}
        # Instruction memory, and initial values for data
        self.memory = [[0, None] for i in range(100)]
        # Position of end of instructions
        self.instructionCounter = 0

# TODO: add "compile" prefix
def getNextAvailable(compiler):
    if compiler.instructionCounter == 100:
        print("Ran out of space for instructions/memory, will roll over now, but expect catastrophic bugs")
        compiler.instructionCounter = 0
    
    available = compiler.instructionCounter
    compiler.instructionCounter += 1

    return available

def compileData(addressName, initialValue, compiler):
    dataPosition = getNextAvailable(compiler)
    compiler.registry[addressName] = dataPosition
    compiler.memory[dataPosition][0] = initialValue

def compileInstruction(instruction, compiler):
    instructionPosition = getNextAvailable(compiler)
    
    if instruction.address is not None:
        compiler.registry[instruction.address] = instructionPosition
    
    compiler.memory[instructionPosition][0] = instruction.opcode
    compiler.memory[instructionPosition][1] = instruction.operand

def compilationError(msg):
    raise RuntimeError(f"[Compiler] {msg}")

def compileLabels(compiler):
    for i, [opcode, operand] in enumerate(compiler.memory):
        if operand is not None:
            memoryAddress = compiler.registry.get(operand)

            if memoryAddress is None:
                compilationError(f"Unrecognised label: {[operand]} for opcode {[opcode]}")
            else:
                compiler.memory[i][0] += memoryAddress

# TODO: rename to ProgramState
class State:
    def __init__(self):
        self.memory = [0,] * 100
        self.accumulator = 0
        self.programCounter = 0

        self.negativeFlag = False
        self.haltFlag = False

        self.inputs = []
        self.outputs = []

        self.testMode = False

    def set(self, value, resetFlag = False):
        if value >= 0:
            self.accumulator = value
            # Only IN and LDA instructions
            # reset the negative flag
            self.negativeFlag = resetFlag
        else:
            self.accumulator = value + 1000
            self.negativeFlag = True

def programOutput(state):
    if not state.testMode:
        print(f"Output: {state.accumulator}")

    state.outputs.append(state.accumulator)

def programInput(state):
    if not state.testMode:
        # TODO: Check for valid input
        state.set(int(input("Input: ")), True)
    
    else:
        state.accumulator = state.inputs[-1]
        state.inputs.pop()

def programAdd(address, state):
    state.set((state.accumulator + state.memory[address]) % 1_000)

def programSubtract(address, state):
    state.set(state.accumulator - state.memory[address])

def programStore(address, state):
    state.memory[address] = state.accumulator

def programLoad(address, state):
    state.set(state.memory[address], True)

def programHalt(state):
    state.haltFlag = True

def programBranch(address, state):
    state.programCounter = address

def programJumpIfZero(address, state):
    if state.accumulator == 0:
        state.programCounter = address

def programJumpIfPositive(address, state):
    # Lie
    if not state.negativeFlag:
        state.programCounter = address

def programAdvance(state):
    # Get current instruction
    instruction = state.memory[state.programCounter]
    state.programCounter += 1

    # Get opcode of instruction
    opcode = instruction // 100 * 100
    operand = instruction - opcode

    if opcode == 900:
        if instruction == OUT:
            programOutput(state)
        elif instruction == IN:
            programInput(state)
    elif opcode == ADD:
        programAdd(operand, state)
    elif opcode == SUB:
        programSubtract(operand, state)
    elif opcode == STO:
        programStore(operand, state)
    elif opcode == LDA:
        programLoad(operand, state)
    elif instruction == HLT:
        programHalt(state)
    elif opcode == BR:
        programBranch(operand, state)
    elif opcode == BRZ:
        programJumpIfZero(operand, state)
    elif opcode == BRP:
        programJumpIfPositive(operand, state)

# Why did past-Thomas decide that the only thing he would abbreviate is the 
# word "abbreviation" itself?
def getOpcode(abrv):
    if abrv in ("HLT", "HALT"):
        return HLT
    elif abrv == "ADD":
        return ADD
    elif abrv in ("STO", "STORE"):
        return STO
    elif abrv in ("SUB", "SUBTRACT"):
        return SUB
    elif abrv in ("LDA", "LOAD"):
        return LDA
    elif abrv == "OUT":
        return OUT
    elif abrv == "IN":
        return IN
    elif abrv == "BR":
        return BR
    elif abrv == "BRZ":
        return BRZ
    elif abrv == "BRP":
        return BRP
    elif abrv in ("DAT", "DATA"):
        return DAT

    # TODO: Handling invalid opcode

# TODO: not a method that acts upon programState, yet given program prefix...
def programLoadCompiler(compiler):
    state = State()
    
    # Load memory
    for i, [instruction, _] in enumerate(compiler.memory):
        state.memory[i] = instruction

    return state

def readInstruction(instruction, line):
    address = None
    operation = None
    operand = None
    
    # TODO: more robust scheme for dealing with whitespace, this is horrific
    # Indicates no address
    if instruction[0].isspace():
        parts = instruction.split(" ")

        parts = [part for part in parts if part != "" and not part.isspace()]

        if len(parts) == 0:
            return None

        operation = parts[0]

        if len(parts) > 1:
            operand = parts[1]

    else:
        parts = instruction.split(" ")
        parts = [part for part in parts if part != "" and not part.isspace()]
        
        if len(parts) == 0:
            return None

        address = parts[0]
        operation = parts[1]

        if len(parts) > 2:
            operand = parts[2]

    return Instruction(address, getOpcode(operation.replace("\t", "")), operand, line)

def compile(text):
    instructions = []
    dataInstructions = []

    compilerState = CompilerState()

    for i, line in enumerate(text):
        cleaned = line.replace("\n", "")
        commentIndex = line.find("#")

        if commentIndex != -1:
            cleaned = cleaned[0:commentIndex]

        if cleaned != "":
            newInstruction = readInstruction(cleaned, i)

            if newInstruction != None:
                if newInstruction.opcode == DAT:
                    compileData(newInstruction.address, int(newInstruction.operand), compilerState)

                else:
                    compileInstruction(newInstruction, compilerState)

    compileLabels(compilerState)

    return compilerState            

filename = input("Enter source code file: ")
# Expected format for a test is:
# name;input;input;input;output;max_instructions
# As many inputs as the program asks for, with one single output, and max_instructions
# being how many instructions should be run before we assume you got stuck in an
# infinite loop
# Example (for the mean of 3 numbers):
# zero-test:0;1;0;0;50000
# big-test:999;333;666;666;50000
# ...
# Multiple tests can be in the same file, just separated by a newline
testSuite = input("Enter filename for tests to run, or leave blank to run no tests: ")

# Declare compilerState variable
compilerState = None

# Compile given source code
# TODO: check filename is real file
with open(filename, "r") as f:
    compilerState = compile(f.readlines())

# Load compiled source code into program
programState = programLoadCompiler(compilerState)

tests = []

if testSuite != "":
    # TODO: check filename is real file
    with open(testSuite, "r") as f:
        lines = f.readlines()

        for line in lines:
            cleaned = line.replace("\n", "")
            parts = cleaned.split(";")

            if cleaned[0] == "#":
                continue

            if cleaned == "":
                continue

            if len(parts) < 4:
                print("Too few parts in a test declaration, expecting at least 4")

            tests.append(Test(parts[0], [int(part) for part in parts[1:-2]], int(parts[-2]), int(parts[-1])))

# TODO: bad bad bad
first = True

# TODO: kinda bad
disableLogging = len(tests) > 100

# TODO: horrible mess of logic because trying to run same code when running tests or when running regularly
while input("Type 'exit' to exit program, type anything else to run program: ").lower() != 'exit':
    testIndex = -1
    currentTest = None
    testResults = []

    if len(tests) > 0:
        programState.testMode = True
        testIndex = 0

    while testIndex < len(tests):
        currentTest = None if not programState.testMode else tests[testIndex]
        instructionsExecuted = 0

        if programState.testMode:
            # Reverse given inputs since State::inputs behaves a bit like a stack
            programState.inputs = [currentTest.givenInputs[i] for i in range(len(currentTest.givenInputs) - 1, -1, -1)]
            if not disableLogging:
                print(f"Running test {currentTest.name} with inputs: {currentTest.givenInputs}, expecting {currentTest.expectedOutput}")

        # TODO: should set regular maximum instruction count
        while not (programState.haltFlag or (programState.testMode and instructionsExecuted > currentTest.maxInstructions)):
            programAdvance(programState)
            instructionsExecuted += 1

        if not programState.testMode:
            print(f"Program ended, {instructionsExecuted} instructions executed")
        else:
            testSucceeded = len(programState.outputs) == 1 and programState.outputs[0] == tests[testIndex].expectedOutput
            testResults.append(testSucceeded)

            if testSucceeded:
                if not disableLogging:
                    print(f"Test {testIndex + 1}: '{currentTest.name} passed in {instructionsExecuted} instructions")
            else:
                reason = None

                if instructionsExecuted > currentTest.maxInstructions:
                    reason = f"Exceeded maximum instructions {currentTest.maxInstructions}"

                else:
                    output = None if len(programState.outputs) < 1 else programState.outputs
                    reason = f"For input {[currentTest.givenInputs]} expected {currentTest.expectedOutput}, but got {output} instead"

                print(f"Test {testIndex + 1}: '{currentTest.name}' failed -> {reason}")

        # Soft-reset of program state
        programState.haltFlag = False
        # Behaviour here varies slightly, in LMC, these inputs and outputs would remain visible,
        # but to simplify testing, I'm clearing them on each run
        programState.inputs = []
        programState.outputs = []

        instructionsExecuted = 0
        testIndex += 1

    # Print summary of test results
    if programState.testMode:
        print(f"{sum(testResults)}/{len(tests)} passed")
    
    first = False

print("Goodbye")