export GDRIVE_LOCAL_ROOT={{GDRIVE_LOCAL_ROOT}}

source _gdrive.sh

# drive ls
drive pull "{{GDRIVE_REL_PATH_TO_SYNC}}"
