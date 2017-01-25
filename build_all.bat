@rem TacBF #####################################################################

robocopy "multilauncher\tacbf" "resources" /mir /ndl /njs /njh
copy "multilauncher\config_tacbf.py" "src\config\config.py"

python build.py new

@rem Frontline #################################################################

robocopy "multilauncher\frontline" "resources" /mir /ndl /njs /njh
copy "multilauncher\config_frontline.py" "src\config\config.py"

python build.py new
