#!/bin/bash
set -e

echo "Setting Up System Dependencies..."

sudo apt update
sudo apt remove mysql-server mysql-client
sudo apt install libcups2-dev redis-server mariadb-client

wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
sudo apt install ./wkhtmltox_0.12.6.1-2.jammy_amd64.deb
