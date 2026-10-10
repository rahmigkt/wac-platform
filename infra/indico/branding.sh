#!/bin/bash
# WAC 2027 kimliğini Indico'ya uygular. Kullanım: sudo bash branding.sh
set -euo pipefail
REPO=https://raw.githubusercontent.com/rahmigkt/wac-platform/main/infra/indico/custom
DIR=/opt/indico/custom
CONF=/opt/indico/etc/indico.conf

mkdir -p $DIR/css $DIR/files $DIR/templates/core
for f in css/00-wac.css files/wac-logo.svg files/wac-logo-dark.svg files/favicon.svg templates/core/footer.html; do
  curl -fsSL "$REPO/$f" -o "$DIR/$f"
done
chown -R indico:www-data $DIR
chmod -R u=rwX,g=rX,o= $DIR

python3 - "$CONF" <<'PY'
import re, sys
path = sys.argv[1]
s = open(path).read()
vals = {
    'CUSTOMIZATION_DIR': "'/opt/indico/custom'",
    'LOGO_URL': "'/static/custom/files/wac-logo.svg'",
    'LOGIN_LOGO_URL': "'/static/custom/files/wac-logo-dark.svg'",
    'FAVICON_URL': "'/static/custom/files/favicon.svg'",
    'HELP_URL': "'https://worldaerospacecongress.org'",
}
for k, v in vals.items():
    s, n = re.subn(rf'^{k}\s*=.*$', f'{k} = {v}', s, flags=re.M)
    if not n:
        s += f'\n{k} = {v}\n'
open(path, 'w').write(s)
PY

systemctl restart indico-uwsgi indico-celery
sleep 4
code=$(curl -s -o /tmp/home.html -w '%{http_code}' -H 'Host: submissions.worldaerospacecongress.org' http://127.0.0.1/)
if [ "$code" = "200" ] && grep -q 'World Aerospace Congress 2027' /tmp/home.html; then
  echo "KIMLIK UYGULANDI (yanit $code)"
else
  echo "SORUN: yanit $code"; journalctl -u indico-uwsgi -n 20 --no-pager | tail -20
fi
