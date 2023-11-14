# lmc_fast
Faster Durham LMC interpreter/tester

## How to use
1. Create a text file and write your code into it
2. Run `main.py`
3. Enter the name of the text file
4. Optionally enter the name of a text file containing tests if you want to test your program
5. Press enter to run the program
6. Can type enter to run the program again; this helps test that your program resets properly after halting (not applicable in test mode)

## Test format
All tests should be in the following format:  
`name;input_0,input_1,input_2,input_...,input_n;output;maxCycles`  
A name, `n` inputs, a single expected output, and the maximum number of F-E the test should run for before it's assumed the program is stuck. Multiple tests can be placed in the same file as long as they are separated by a newline.

## How to generate cases
Just run `gentest.py`. You can change the `TEST_CASES` to how many test cases to generate and `FILENAME` to change the filename to which the tests are saved to. You can add special test cases by adding an entry `(a, b, c)` into the `specials` array.

## Instruction set
All instructions must be prefixed either with a whitespace or a `label`: an alias for the mailbox that instruction/data is stored in. You can use `_mailboxNumber` to reference a specific mailbox.

- `ADD <label>` Add value at `label` to value stored in calculator
- `SUB <label>` Subtract value at `label` from value stored in calculator. Will set the negative flag if the result underflows
- `STO <label>` Store the value in the accumulator at `label`
- `LDA <label>` Load the value at `label` into calculator. Resets the negative flag
- `BR  <label>` Jump to `label`
- `BRZ <label>` Jump to `label` only if the value stored in the calculator is 0
- `BRP <label>` Jump to `label` only if the negative flag is not set (a value of 0 would still cause a jump, despite 0 not being positive)
- `IN` Requests input from the user and stores into calculator. Resets the negative flag
- `OUT` Outputs whatever is in the calculator
- `HLT` End the program, resetting program counter to 0
- `DAT <value>` The mailbox of the data instruction is instead used to store `value`, this value is expected to be at most a 3-digit integer. You can omit the `value` to leave the mailbox uninitialised (storing 0)

## Behaviours
### Important
- The value in the calculator is not reset between tests (as in LMC), so if you assume the calculator stores the value `0` when your program starts,
but you don't reset it yourself, every subsequent test after the first will be wrong
- After the HLT instruction the program counter is reset to 0, so the next instruction executed will be the first mailbox/instruction
- Negative flag is only reset when a new value is loaded into the calculator through `LDA` or `IN`
- You can reference an exact mailbox (to jump to, or store data in) using `_mailboxNumber` (e.g. `BR _2` will jump to the 3rd mailbox)
### Mostly esoteric (ignore)
- You can jump to a `DAT` which will execute the data you specified as if it were an instruction. You can also load an instruction's opcode and operand into the calculator as if it were some regular data
- The HLT instruction ignores its operand, so you could store a 2 digit number in the last 2 digits of the HLT command `0xx`
- Any instruction with opcode `9` that isn't proceeded by either `01` (input) or `02` (output) is considered a NO-OP (just skipped)