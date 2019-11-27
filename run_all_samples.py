from DoflirVirtualMachine import read_bytecode
from DoflirVirtualMachine import run_program
from pathlib import Path
from termcolor import colored

import DoflirCompiler


def main():
    """Test program that compiles and runs all Doflir sample programs."""
    sample_dir = Path("doflir_programs")
    # Fetch list of Doflir source programs.
    file_list = []
    for item in sample_dir.iterdir():
        # Don't try to compile any random file that doesnt end with the
        # doflir source extension.
        if item.is_file() and str(item).endswith("dof"):
            file_list.append(item)
    for file in file_list:
        DoflirCompiler.make_obj_code(file)

    # Fetch list of Doflir bytecode programs.
    bytecode_list = []
    for item in sample_dir.iterdir():
        if item.is_file() and str(item).endswith("obj"):
            bytecode_list.append(item)
    print()

    # Run all bytecode programs found.
    for obj_name in bytecode_list:
        print(
            f"Running '{colored(obj_name, 'green')}'..."
        )
        run_program(
            read_bytecode(filename=obj_name)
        )
        print()
        print()
        print()


if __name__ == "__main__":
    main()
