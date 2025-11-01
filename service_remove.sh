sudo systemctl stop vendingapp.service
sudo systemctl disable vendingapp.service
sudo rm /etc/systemd/system/vendingapp.service
sudo systemctl daemon-reload
