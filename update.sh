echo
echo "Pulling latest version from GitHub…"
echo
git pull
echo
echo "Reinstalling chime…"
echo
venv/bin/python3 -m pip install .
echo
read -r -p "Restart chime (y/n)?" CONT
if [ "$CONT" = "y" ]; then
  sudo service chime restart;
else
  exit;
fi