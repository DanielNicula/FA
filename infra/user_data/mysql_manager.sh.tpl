#!/bin/bash
set -euxo pipefail

MYSQL_ROOT_PASSWORD="${mysql_password}"

apt-get update -y
sudo apt-get install mysql-server -y
sudo apt-get install sysbench -y

cd /tmp
wget https://downloads.mysql.com/docs/sakila-db.tar.gz
tar -xvf sakila-db.tar.gz
sudo mysql -u root -p"${mysql_password}" < sakila-db/sakila-schema.sql
sudo mysql -u root -p"${mysql_password}" < sakila-db/sakila-data.sql

# Let Proxy access MySQL remotely
sudo sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql

sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${mysql_password}';"
sudo mysql -e "CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${mysql_password}';"
sudo mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;"
sudo mysql -e "FLUSH PRIVILEGES;"