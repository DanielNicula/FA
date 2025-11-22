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


