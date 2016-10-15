@rem TacBF #####################################################################

robocopy "multilauncher\images_tacbf" "resources\images" /mir /ndl /njs /njh
copy "multilauncher\config_tacbf.py" "src\config\config.py"

python build.py new

@rem Frontline #################################################################

robocopy "multilauncher\images_frontline" "resources\images" /mir /ndl /njs /njh
copy "multilauncher\config_frontline.py" "src\config\config.py"

python build.py new
