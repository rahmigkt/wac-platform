#!/bin/bash
# Oracle Cloud > Create instance > Advanced options > Initialization script alanına yapıştırılır.
curl -fsSL https://raw.githubusercontent.com/rahmigkt/wac-platform/main/infra/indico/install.sh -o /root/wac-install.sh
bash /root/wac-install.sh > /var/log/wac-install.log 2>&1
