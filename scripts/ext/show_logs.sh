set -e
log_file="${MY_DATA_DIR}/MyScripts.log"
tail +1f "$log_file" | run_script r/highlight.py -p "^D:.*=gray" "^W:.*=yellow" "^E:.*=red"
