import os

from utils.menu.logviewer import LogViewerMenu

LogViewerMenu(
    file=os.path.join(os.environ["MY_TEMP_DIR"], "MyScripts.log"), filter=" (I|W|E) .*"
).exec()
