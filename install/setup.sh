#!/bin/bash
cp /opt/hgprofiler/conf/local.ini.template /opt/hgprofiler/conf/local.ini
sed -i "s/##DATABASE_USERNAME##/${DB_SER}/g" /opt/hgprofiler/conf/local.ini
sed -i "s/##DATABASE_PASSWORD##/${DB_PASS}/g" /opt/hgprofiler/conf/local.ini
sed -i "s/##DATABASE_SUPER_USERNAME##/${DB_SUPER_USER}/g" /opt/hgprofiler/conf/local.ini
sed -i "s/##DATABASE_SUPER_PASSWORD##/${DB_SUPER_PASS}/g" /opt/hgprofiler/conf/local.ini
sed -i "s/##FLASK_SECRET_KEY##/${SECRET_KEY}/g" /opt/hgprofiler/conf/local.ini
