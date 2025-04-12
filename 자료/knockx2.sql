create database knockx2;
drop database knockx2;

use knockx3;
show tables;

CREATE USER 'knockx2'@'%' IDENTIFIED BY 'knockx2';
GRANT ALL PRIVILEGES ON *.* TO 'knockx2'@'%';
FLUSH PRIVILEGES;
