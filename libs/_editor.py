import json
import os
import subprocess
from typing import Optional

from _pkgmanager import find_executable
from _shutil import exec_ahk, is_in_termux, start_process


def open_in_androidstudio(path, line=None):
    args = [r"C:\Program Files\Android\Android Studio\bin\studio64.exe"]
    if line is not None:
        args += ["--line", str(line)]
    args.append(path)
    subprocess.Popen(args)
    exec_ahk("WinActivate ahk_exe studio64.exe")


def vscode_set_include_path(include_path):
    include_path = [os.path.abspath(x).replace("\\", "/") for x in include_path]
    include_path.insert(0, "${workspaceFolder}/**")

    # Default configuration file
    data = {"configurations": [{"name": "Win32", "includePath": []}]}

    c_cpp_properties = ".vscode/c_cpp_properties.json"
    if os.path.exists(c_cpp_properties):
        with open(c_cpp_properties) as f:
            data = json.load(f)

    data["configurations"][0]["includePath"] = include_path

    os.makedirs(".vscode", exist_ok=True)
    with open(c_cpp_properties, "w") as f:
        json.dump(data, f, indent=4)


def is_vscode_installed() -> bool:
    return find_executable("vscode") is not None


def open_in_vscode(
    file: str,
    line_number: Optional[int] = None,
    vscode_executable: Optional[str] = None,
):
    if vscode_executable:
        vscode = vscode_executable
    else:
        vscode = find_executable("vscode")
        if vscode is None:
            raise FileNotFoundError(
                "Cannot locate vscode executable, maybe not installed."
            )

    if isinstance(file, str):
        if line_number is None:
            args = [vscode, file]
        else:
            args = [vscode, "-g", "{}:{}".format(file, line_number)]
    else:
        args = [vscode] + file

    start_process(args)


def open_in_vim(file: str, line_number: Optional[int] = None):
    args = ["vim"]
    if line_number is not None:
        args.append(f"+{line_number}")
    args.append(file)
    subprocess.call(args)


def open_in_editor(path: str, line_number: Optional[int] = None):
    if is_in_termux():
        open_in_vim(
            path if (isinstance(path, str)) else path[-1], line_number=line_number
        )
    else:
        open_in_vscode(path, line_number=line_number)
