from DoflirVirtualMachine import read_bytecode
from DoflirVirtualMachine import run_program
from pathlib import Path
from termcolor import colored

import DoflirCompiler


def main():
    sample_dir = Path("doflir_programs")
    file_list = []
    for item in sample_dir.iterdir():
        if item.is_file() and str(item).endswith("dof"):
            file_list.append(item)
    for file in file_list:
        DoflirCompiler.make_obj_code(file)

    bytecode_list = []
    for item in sample_dir.iterdir():
        if item.is_file() and str(item).endswith("obj"):
            bytecode_list.append(item)
    print()

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
