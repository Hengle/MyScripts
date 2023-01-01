import json
import os
import shutil
import subprocess
import sys

from _shutil import call_echo, download, get_home_path, prepend_to_path, print2, unzip

EXTENSION_LIST = [
    # "donjayamanne.githistory",
    "ms-vscode.cpptools",
    "stkb.rewrap",
    "streetsidesoftware.code-spell-checker",
    # markdown
    "yzhang.markdown-all-in-one",
    "mushan.vscode-paste-image",
    "kortina.vscode-markdown-notes",  # [[wiki-links]], backlinks, #tags and @bibtex-citations
    # javascript
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    # bash
    "foxundermoon.shell-format",
    # python
    "ms-python.python",
    "njpwerner.autodocstring",
    # "ms-vscode-remote.vscode-remote-extensionpack",
    "ms-toolsai.jupyter",
    # AHK
    "cweijan.vscode-autohotkey-plus",
    # shader
    "circledev.glsl-canvas",  # shader preview
    # "cadenas.vscode-glsllint",
    "xaver.clang-format",
    # powershell
    "ms-vscode.powershell-preview",
    # mermaid
    "bierner.markdown-mermaid",
    "tomoyukim.vscode-mermaid-editor",
]

if sys.platform == "win32":
    prepend_to_path([r"C:\Program Files\Microsoft VS Code\bin"])


def install_glslangvalidator():
    if sys.platform == "win32":
        out = download(
            "https://github.com/KhronosGroup/glslang/releases/download/master-tot/glslang-master-windows-x64-Release.zip",
            save_to_tmp=True,
        )
        unzip(out, os.path.join(get_home_path(), "tools", "glslang"))
        os.remove(out)
        return os.path.join(
            get_home_path(), "tools", "glslang", "bin", "glslangValidator.exe"
        )


def get_vscode_cmdline(data_dir=None):
    if not shutil.which("code"):
        raise Exception("cannot locate vscode command: code")

    if sys.platform == "win32":
        args = ["cmd", "/c", "code"]  # code.cmd
    else:
        args = ["code"]
    if data_dir is not None:
        extensions_dir = os.path.join(data_dir, "extensions")
        args += [
            "--user-data-dir",
            data_dir,
            "--extensions-dir",
            extensions_dir,
        ]
    return args


def install_extensions(data_dir=None):
    print2("Install extensions...")

    for extension in EXTENSION_LIST:
        call_echo(
            get_vscode_cmdline(data_dir=data_dir)
            + ["--install-extension", "%s" % extension],
        )


def config_vscode(data_dir=None, compact=False, glslang=False):
    # call_echo([sys.executable, "-m", "pip", "install", "--user", "pylint"])
    # call_echo([sys.executable, "-m", "pip", "install", "--user", "autopep8"])
    call_echo([sys.executable, "-m", "pip", "install", "--user", "mypy"])

    install_extensions(data_dir=data_dir)

    if data_dir is None:
        if sys.platform == "win32":
            data_dir = os.path.expandvars("%APPDATA%/Code")
        elif sys.platform == "linux":
            data_dir = os.path.expanduser("~/.config/Code")
        else:
            raise Exception("OS not supported: {}".format(sys.platform))

    print2("Update key bindings...")
    with open(os.path.abspath(data_dir + "/User/keybindings.json"), "w") as f:
        json.dump(
            [
                {
                    "key": "ctrl+shift+v",
                    "command": "markdown.showPreviewToSide",
                    "when": "!notebookEditorFocused && editorLangId == 'markdown'",
                },
                {
                    "key": "ctrl+shift+v",
                    "command": "mermaid-editor.preview",
                    "when": "resourceExtname == '.mmd'",
                },
                {"key": "shift+alt+r", "command": "revealFileInOS"},
                {"key": "shift+alt+c", "command": "copyFilePath"},
                {"key": "ctrl+shift+enter", "command": "editor.action.openLink"},
                {
                    "key": "alt+l",
                    "command": "markdown.extension.editing.toggleList",
                    "when": "editorTextFocus && !editorReadonly && editorLangId == 'markdown'",
                },
                {"key": "ctrl+shift+r", "command": "workbench.action.reloadWindow"},
                {"key": "ctrl+shift+alt+enter", "command": "-jupyter.runAndDebugCell"},
                {
                    "key": "alt+left",
                    "command": "workbench.action.navigateBack",
                    "when": "canNavigateBack",
                },
                {
                    "key": "alt+right",
                    "command": "workbench.action.navigateForward",
                    "when": "canNavigateForward",
                },
            ],
            f,
            indent=4,
        )

    print2("Update settings...")
    SETTING_CONFIG = os.path.abspath(data_dir + "/User/settings.json")
    try:
        with open(SETTING_CONFIG) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data["workbench.colorTheme"] = "Default Light+"

    data["cSpell.enabledLanguageIds"] = ["markdown", "text"]
    data["search.exclude"] = {"**/build": True}
    data["pasteImage.path"] = "${currentFileNameWithoutExt}"
    data["workbench.editor.enablePreviewFromQuickOpen"] = False
    data["grammarly.autoActivate"] = False

    # Python
    call_echo([sys.executable, "-m", "pip", "install", "--user", "black"])
    data["python.pythonPath"] = sys.executable.replace("\\", "/")
    data["python.formatting.provider"] = "black"
    # Workaround for "has no member" issues
    data["python.linting.pylintArgs"] = [
        "--errors-only",
        "--generated-members=numpy.* ,torch.* ,cv2.* , cv.*",
    ]
    data["python.linting.mypyEnabled"] = True
    data["python.linting.enabled"] = True
    data["python.linting.pylintEnabled"] = False
    data["python.languageServer"] = "Pylance"
    data["window.title"] = "${rootName}${separator}${appName}"
    data["editor.minimap.enabled"] = False

    if glslang and sys.platform == "win32":
        data["glsllint.glslangValidatorPath"] = install_glslangvalidator()

    data.update(
        {
            "[markdown]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
            "[html]": {"editor.defaultFormatter": "esbenp.prettier-vscode"},
            "[jsonc]": {"editor.defaultFormatter": "vscode.json-language-features"},
        }
    )

    if compact:
        data.update(
            {
                "workbench.colorTheme": "One Dark Pro Flat",
                "workbench.startupEditor": "newUntitledFile",
                "explorer.openEditors.visible": 0,
                "workbench.activityBar.visible": False,
                "workbench.statusBar.visible": False,
                "window.zoomLevel": 0,
                "window.menuBarVisibility": "compact",
                "extensions.ignoreRecommendations": True,
                "liveServer.settings.AdvanceCustomBrowserCmdLine": "chrome --new-window",
                "extensions.autoCheckUpdates": False,
                "update.mode": "manual",
                # Terminal
                "terminal.integrated.profiles.windows": {
                    "Command Prompt": {"path": "cmd", "args": ["/k"]}
                },
                "terminal.integrated.defaultProfile.windows": "Command Prompt",
                "scm.diffDecorations": "none",
            }
        )

    with open(SETTING_CONFIG, "w") as f:
        json.dump(data, f, indent=4)


def open_vscode(data_dir):
    subprocess.Popen(get_vscode_cmdline(data_dir=data_dir), shell=True, close_fds=True)


if __name__ == "__main__":
    data_dir = os.environ.get("_DATA_DIR")
    config_vscode(data_dir=data_dir, compact=False, glslang=True)
