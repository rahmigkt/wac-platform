#!/bin/bash
# Indico SMTP ayarı (Brevo). Kullanım: sudo bash set-smtp.sh '<SMTP_LOGIN>' '<SMTP_KEY>'
set -euo pipefail
LOGIN="$1"; KEY="$2"
CONF=/opt/indico/etc/indico.conf
FROM="noreply@worldaerospacecongress.org"
TO="bvhyapim@gmail.com"

python3 - "$CONF" "$LOGIN" "$KEY" <<'PY'
import re, sys
path, login, key = sys.argv[1:]
s = open(path).read()
vals = {
    'SMTP_SERVER': "('smtp-relay.brevo.com', 587)",
    'SMTP_USE_TLS': 'True',
    'SMTP_LOGIN': repr(login),
    'SMTP_PASSWORD': repr(key),
}
for k, v in vals.items():
    s, n = re.subn(rf'^{k}\s*=.*$', f'{k} = {v}', s, flags=re.M)
    if not n:
        s += f'\n{k} = {v}\n'
open(path, 'w').write(s)
PY

systemctl restart indico-uwsgi indico-celery
echo "Ayar kaydedildi, servisler yeniden başlatıldı."

python3 - "$LOGIN" "$KEY" "$FROM" "$TO" <<'PY'
import smtplib, sys
from email.message import EmailMessage
login, key, frm, to = sys.argv[1:]
m = EmailMessage()
m['From'] = f'WAC 2027 <{frm}>'; m['To'] = to
m['Subject'] = 'WAC 2027 — e-posta testi'
m.set_content('Bildiri sisteminden test e-postası. Bu e-postayı aldıysanız SMTP ayarı çalışıyor.')
try:
    with smtplib.SMTP('smtp-relay.brevo.com', 587, timeout=30) as s:
        s.starttls(); s.login(login, key); s.send_message(m)
    print(f'TEST BAŞARILI: {to} adresine e-posta gönderildi.')
except Exception as e:
    print(f'TEST BAŞARISIZ: {e}')
PY
