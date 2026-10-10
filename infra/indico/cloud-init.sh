#!/bin/bash
# Oracle Cloud > Initialization script. İnternet gelene kadar bekler (genel IP sonradan eklenebilir), sonra kurar.
systemd-run --unit=wac-install bash -c 'until curl -fsSL https://raw.githubusercontent.com/rahmigkt/wac-platform/main/infra/indico/install.sh -o /root/wac-install.sh; do sleep 30; done; bash /root/wac-install.sh > /var/log/wac-install.log 2>&1'
