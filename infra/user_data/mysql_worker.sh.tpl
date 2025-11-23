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

# Let Proxy access MySQL remotely and activate GTID for replication
sudo sed -i 's/^bind-address.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo tee -a /etc/mysql/mysql.conf.d/mysqld.cnf > /dev/null <<EOF

server-id = ${server_id}
gtid_mode = ON
enforce_gtid_consistency = ON
binlog_format = ROW
relay_log = relay-bin
read_only = ON
EOF
sudo systemctl restart mysql

#Let Proxy access MySQL remotely
sudo mysql -u root -p"${mysql_password}" <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${mysql_password}';
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${mysql_password}';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
EOF

# Setting up replication
    
sudo mysql -u root -p"${mysql_password}" <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${mysql_password}';
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${mysql_password}';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF

# Set up GTID replication
sudo mysql -u root -p"${mysql_password}" <<EOF
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='${manager_ip}',
  SOURCE_USER='repl',
  SOURCE_PASSWORD='${mysql_password}',
  SOURCE_AUTO_POSITION=1;

START REPLICA;
EOF