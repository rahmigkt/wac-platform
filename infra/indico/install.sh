#!/bin/bash
# WAC 2027 — Indico bildiri sistemi kurulumu
# Hedef: Oracle Cloud, Ubuntu 24.04 (ARM veya x86), Cloudflare Flexible SSL arkasında, port 80.
# Kaynak: docs.getindico.io production/deb/nginx — wizard yerine etkileşimsiz yapılandırma.
# Kurulum ilerlemesi: http://<SUNUCU-IP>/kurulum.txt

set -euo pipefail

HOST="submissions.worldaerospacecongress.org"
ADMIN_EMAIL="bvhyapim@gmail.com"
NOREPLY_EMAIL="noreply@worldaerospacecongress.org"
TZNAME="Europe/Istanbul"
STATUS_DIR="/var/www/wac-status"
STATUS="$STATUS_DIR/kurulum.txt"
export DEBIAN_FRONTEND=noninteractive

mkdir -p "$STATUS_DIR"
step() { echo "$(date '+%H:%M:%S')  $*" | tee -a "$STATUS"; }
trap 'step "HATA: satır $LINENO başarısız oldu. Ayrıntı: /var/log/wac-install.log"' ERR

step "Kurulum başladı ($(uname -m))"

# İlk açılışta cloud-init ve otomatik güncellemeler apt kilidini tutar; bitmelerini bekle.
cloud-init status --wait >/dev/null 2>&1 || true
APT="apt-get -o DPkg::Lock::Timeout=1800 -y -q"
apt_wait() { while fuser /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock >/dev/null 2>&1; do sleep 10; done; }

# ── 1. Güvenlik duvarı (Oracle Ubuntu imajı 22 dışındaki her şeyi reddeder) ──
step "Güvenlik duvarı: 80 ve 443 açılıyor"
for port in 80 443; do
  iptables -C INPUT -p tcp --dport $port -m state --state NEW -j ACCEPT 2>/dev/null || \
    iptables -I INPUT 1 -p tcp --dport $port -m state --state NEW -j ACCEPT
done
if command -v netfilter-persistent >/dev/null; then netfilter-persistent save; fi

# ── 2. Paketler ──
step "Sistem paketleri kuruluyor (birkaç dakika)"
apt_wait; $APT update
apt_wait; $APT install lsb-release wget curl gnupg nginx
# İlerleme sayfasını hemen yayınla
cat > /etc/nginx/sites-available/default <<EOF
server {
  listen 80 default_server;
  listen [::]:80 default_server;
  location = /kurulum.txt { root $STATUS_DIR; default_type text/plain; charset utf-8; add_header Cache-Control no-store; }
  location / { return 200 "WAC kurulum suruyor. Ilerleme: /kurulum.txt\n"; default_type text/plain; }
}
EOF
systemctl restart nginx

wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor --yes -o /usr/share/keyrings/pgdg-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/pgdg-archive-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
apt_wait; $APT update
apt_wait; $APT install --install-recommends postgresql-16 libpq-dev libxslt1-dev libxml2-dev libffi-dev \
  libpcre2-dev libyaml-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
  libncurses-dev xz-utils liblzma-dev uuid-dev build-essential redis-server git libpango1.0-dev \
  libjpeg-turbo8-dev python3.12 python3.12-venv python3.12-dev
systemctl start postgresql.service redis-server.service
timedatectl set-timezone "$TZNAME" || true

# ── 3. Veritabanı ──
step "Veritabanı oluşturuluyor"
su - postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='indico'\"" | grep -q 1 || su - postgres -c 'createuser indico'
su - postgres -c "psql -lqt" | cut -d'|' -f1 | grep -qw indico || su - postgres -c 'createdb -O indico indico'
su - postgres -c 'psql indico -c "CREATE EXTENSION IF NOT EXISTS unaccent; CREATE EXTENSION IF NOT EXISTS pg_trgm;"'

# ── 4. Indico kullanıcısı ve Python ortamı ──
step "Indico indiriliyor ve derleniyor (5-15 dakika)"
id indico >/dev/null 2>&1 || useradd -rm -g www-data -d /opt/indico -s /bin/bash indico
su - indico -c 'python3.12 -m venv --upgrade-deps --prompt indico ~/.venv'
su - indico -c '~/.venv/bin/pip install -q setuptools wheel'
su - indico -c '~/.venv/bin/pip install -q uwsgi'
su - indico -c '~/.venv/bin/pip install -q indico'
grep -q 'source ~/.venv/bin/activate' /opt/indico/.bashrc || echo 'source ~/.venv/bin/activate' >> /opt/indico/.bashrc

# ── 5. Indico yapılandırması (wizard eşdeğeri) ──
step "Indico yapılandırılıyor"
su - indico <<EOF
set -e
source ~/.venv/bin/activate
mkdir -p ~/archive ~/cache ~/etc ~/log/nginx ~/tmp ~/web
PKG=\$(python -c "import indico, os; print(os.path.dirname(indico.__file__))")
if [ ! -f ~/etc/indico.conf ]; then
  SECRET=\$(python -c "import secrets; print(secrets.token_hex(32))")
  cat > ~/etc/indico.conf <<CONF
# General settings
SQLALCHEMY_DATABASE_URI = 'postgresql:///indico'
SECRET_KEY = '\$SECRET'
BASE_URL = 'https://$HOST'
CELERY_BROKER = 'redis://127.0.0.1:6379/0'
REDIS_CACHE_URL = 'redis://127.0.0.1:6379/1'
DEFAULT_TIMEZONE = '$TZNAME'
DEFAULT_LOCALE = 'en_GB'
ENABLE_ROOMBOOKING = False
CACHE_DIR = '/opt/indico/cache'
TEMP_DIR = '/opt/indico/tmp'
LOG_DIR = '/opt/indico/log'
LOCAL_PASSWORD_MIN_LENGTH = 15
CSP_ENABLED = True
STORAGE_BACKENDS = {'default': 'fs:/opt/indico/archive'}
ATTACHMENT_STORAGE = 'default'
USE_PROXY = True

# Email settings (SMTP sonradan girilecek)
SMTP_SERVER = ('localhost', 25)
SMTP_USE_TLS = False
SMTP_LOGIN = ''
SMTP_PASSWORD = ''
SUPPORT_EMAIL = '$ADMIN_EMAIL'
PUBLIC_SUPPORT_EMAIL = '$ADMIN_EMAIL'
NO_REPLY_EMAIL = '$NOREPLY_EMAIL'

SYSTEM_NOTICES_URL = None
ALLOW_PUBLIC_USER_SEARCH = False

STATIC_FILE_METHOD = ('xaccelredirect', {'/opt/indico': '/.xsf/indico'})
CONF
fi
cp -n "\$PKG/logging.yaml.sample" ~/etc/logging.yaml || true
ln -sfn "\$PKG/web/static" ~/web/static
cp -f "\$PKG/web/indico.wsgi" ~/web/indico.wsgi
ln -sfn ~/etc/indico.conf ~/.indico.conf
chmod go-rwx ~/* ~/.[^.]* || true
chmod 710 ~/ ~/archive ~/cache ~/log ~/tmp
chmod 750 ~/web ~/.venv
chmod g+w ~/log/nginx
EOF

# ── 6. Veritabanı şeması ──
step "Veritabanı şeması hazırlanıyor"
su - indico -c 'source ~/.venv/bin/activate && indico db prepare'

# ── 7. uWSGI, Celery, nginx ──
step "Servisler kuruluyor"
cat > /etc/uwsgi-indico.ini <<'EOF'
[uwsgi]
uid = indico
gid = www-data
umask = 027

processes = 4
enable-threads = true
chmod-socket = 770
chown-socket = indico:www-data
socket = /opt/indico/web/uwsgi.sock
stats = /opt/indico/web/uwsgi-stats.sock
protocol = uwsgi

master = true
auto-procname = true
procname-prefix-spaced = indico
disable-logging = true

single-interpreter = true

touch-reload = /opt/indico/web/indico.wsgi
wsgi-file = /opt/indico/web/indico.wsgi
virtualenv = /opt/indico/.venv

vacuum = true
buffer-size = 20480
memory-report = true
max-requests = 2500
harakiri = 900
harakiri-verbose = true
reload-on-rss = 2048
evil-reload-on-rss = 8192
EOF

cat > /etc/systemd/system/indico-uwsgi.service <<'EOF'
[Unit]
Description=Indico uWSGI
After=network.target

[Service]
ExecStart=/opt/indico/.venv/bin/uwsgi --ini /etc/uwsgi-indico.ini
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
SyslogIdentifier=indico-uwsgi
User=indico
Group=www-data
UMask=0027
Type=notify
NotifyAccess=all
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/indico-celery.service <<'EOF'
[Unit]
Description=Indico Celery
After=network.target

[Service]
ExecStart=/opt/indico/.venv/bin/indico celery worker -B
Restart=always
SyslogIdentifier=indico-celery
User=indico
Group=www-data
UMask=0027
Type=simple
KillMode=mixed
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
EOF

# Cloudflare (Flexible SSL) → origin HTTP:80. Ziyaretçi HTTPS görür.
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/conf.d/indico.conf <<EOF
server {
  listen 80 default_server;
  listen [::]:80 default_server;
  server_name $HOST _;

  access_log /opt/indico/log/nginx/access.log combined;
  error_log  /opt/indico/log/nginx/error.log;

  location = /kurulum.txt { root $STATUS_DIR; default_type text/plain; charset utf-8; add_header Cache-Control no-store; }

  location /.xsf/indico/ {
    internal;
    alias /opt/indico/;
    add_header Content-Security-Policy \$upstream_http_content_security_policy;
    add_header Content-Security-Policy-Report-Only \$upstream_http_content_security_policy_report_only;
    add_header Reporting-Endpoints \$upstream_http_reporting_endpoints;
  }

  location ~ ^/(images|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)\$ {
    alias /opt/indico/web/static/\$1\$2/\$3.\$5;
    access_log off;
  }

  location ~ ^/(css|dist|images|fonts)/(.*)\$ {
    alias /opt/indico/web/static/\$1/\$2;
    access_log off;
  }

  location /robots.txt {
    alias /opt/indico/web/static/robots.txt;
    access_log off;
  }

  location / {
    root /var/empty/nginx;
    include /etc/nginx/uwsgi_params;
    uwsgi_pass unix:/opt/indico/web/uwsgi.sock;
    uwsgi_param UWSGI_SCHEME https;
    uwsgi_param HTTPS on;
    uwsgi_read_timeout 15m;
    uwsgi_buffers 32 32k;
    uwsgi_busy_buffers_size 128k;
    uwsgi_hide_header X-Sendfile;
    client_max_body_size 1G;
  }
}
EOF
mkdir -p /var/empty/nginx
nginx -t

systemctl daemon-reload
systemctl restart nginx.service indico-celery.service indico-uwsgi.service
systemctl enable nginx.service postgresql.service redis-server.service indico-celery.service indico-uwsgi.service

# ── 8. Günlük veritabanı yedeği ──
mkdir -p /opt/backups && chown postgres /opt/backups
cat > /etc/cron.d/indico-backup <<'EOF'
30 3 * * * postgres pg_dump -Fc indico > /opt/backups/indico-$(date +\%u).dump
EOF

sleep 5
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $HOST" http://127.0.0.1/ || true)
step "Indico yanıt kodu: $code"
step "TAMAMLANDI. https://$HOST adresine gidip ilk yönetici hesabını oluşturun."
