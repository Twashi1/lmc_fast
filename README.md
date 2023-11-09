# lmc_fast
Faster LMC interpreter/tester

## How to use interpreter
1. Create a text file and write your code into it
2. Run `main.py`
3. Enter the name of the text file
4. Optionally enter the name of a text file containing tests if you want to test your program
5. Press enter to run the program
6. Can type enter to run the program again; this helps test that your program resets properly after halting

## Test format
All tests should be in the following format:  
`name;input_0;input_1;input_2;input_...;input_n;output;max_cycles`  
A name, `n` inputs, a single expected output, and the maximum number of cycles the test should run for before it's assumed the program is stuck. Multiple tests can be placed in the same file as long as they are separated by a newline

## How to generate cases
Just run `gentest.py`. You can change the `TEST_CASES` to how many test cases to generate (I recommend about 3000) and `FILENAME` to change the filename to which the tests are saved to.

## Instruction set
All instructions must be prefixed either with a whitespace or a `label`: a place you can
branch to. `DAT` instructions are prefixed with an `address`: the alias for the mailbox of the `DAT` instruction  
*Distinction between `address` and `label` in instructions is semantic only; both are 'valid' technically*  
*Operands after the `IN`, `OUT`, `HLT` operations will be ignored*  

- `ADD <address>` Add value at `address` to value stored in calculator
- `SUB <address>` Subtract value at `address` from value stored in calculator. Will set the negative flag if the result underflows
- `STO <address>` Store the value in the accumulator at `address`
- `LDA <address>` Load the value at `address` into calculator. Resets the negative flag
- `BR <label>` Jump to `label`
- `BRZ <label>` Jump to `label` only if the value stored in the calculator is 0
- `BRP <label>` Jump to `label` only if the negative flag is not set
- `IN` Requests input from the user and stores into calculator. Resets the negative flag
- `OUT` Outputs whatever is in the calculator
- `HLT` End the program