adb shell "dumpsys activity activities | grep -E '(Display|Stack) #|\* Task|Hist'"

echo '---'
adb shell "dumpsys activity activities"
