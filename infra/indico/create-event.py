"""WAC 2027 kongresini, beş sempozyum eksenini ve bildiri çağrısını oluşturur.

Sunucuda indico kullanıcısıyla çalışır:
  sudo -u indico -i /opt/indico/.venv/bin/python /tmp/create-event.py
Tekrar çalıştırılırsa mevcut kongreyi bulur, eksik olanları tamamlar.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from indico.web.flask.app import make_app

TZ = ZoneInfo('Europe/Istanbul')
TITLE = 'World Aerospace Congress — WAC 2027'
START = datetime(2027, 10, 4, 9, 0, tzinfo=TZ)
END = datetime(2027, 10, 8, 18, 0, tzinfo=TZ)
CFA_END = datetime(2027, 3, 31, 23, 59, tzinfo=TZ)
DESCRIPTION = (
    '<p>The World Aerospace Congress (WAC 2027) will be held in Istanbul, Türkiye, in October 2027, '
    'organised by the Turkish Society for History of Science (TBTK).</p>'
    '<p>Abstracts are invited for the five symposium axes of the congress.</p>'
    '<p>More information: <a href="https://worldaerospacecongress.org">worldaerospacecongress.org</a></p>'
)
TRACKS = [
    ('01', 'Aerospace Sciences and Engineering', 'Havacılık Bilimleri ve Mühendisliği'),
    ('02', 'Space Sciences and Technologies', 'Uzay Bilimleri ve Teknolojileri'),
    ('03', 'Aviation Management, Economics and Law', 'Havacılık Yönetimi, Ekonomisi ve Hukuku'),
    ('04', 'Aerospace Ecosystem', 'Havacılık ve Uzay Ekosistemi'),
    ('05', 'Aviation History and Society', 'Havacılık Tarihi ve Toplum'),
]

app = make_app()
with app.app_context():
    from flask import session

    from indico.core.config import config
    from indico.core.db import db
    from indico.core.db.sqlalchemy.protection import ProtectionMode
    from indico.modules.categories import Category
    from indico.modules.events import Event
    from indico.modules.events.models.events import EventType
    from indico.modules.events.operations import create_event
    from indico.modules.events.tracks.operations import create_track
    from indico.modules.users import User
    from indico.util.date_time import now_utc

    with app.test_request_context(base_url=config.BASE_URL):
        admin = User.query.filter_by(is_admin=True, is_deleted=False).order_by(User.id).first()
        if admin is None:
            raise SystemExit('Yönetici kullanıcı bulunamadı')
        session.set_session_user(admin)

        event = Event.query.filter(Event.title.ilike('%WAC 2027%'), ~Event.is_deleted).first()
        if event is None:
            event = create_event(Category.get_root(), EventType.conference, {
                'title': TITLE,
                'creator': admin,
                'description': DESCRIPTION,
                'start_dt': START,
                'end_dt': END,
                'timezone': 'Europe/Istanbul',
                'location_data': {'inheriting': False, 'venue_name': 'Istanbul, Türkiye',
                                  'room_name': '', 'address': ''},
                'protection_mode': ProtectionMode.public,
            })
            print(f'Kongre oluşturuldu (id {event.id})')
        else:
            print(f'Kongre zaten var (id {event.id})')

        existing = {t.code for t in event.tracks}
        for code, en, tr in TRACKS:
            if code in existing:
                continue
            create_track(event, {'code': code, 'title': en, 'description': tr})
            print(f'Eksen eklendi: {code} {en}')

        if not event.cfa.end_dt:
            event.cfa.schedule(now_utc(), CFA_END, None)
            print('Bildiri çağrısı açıldı, son tarih 31 Mart 2027 23:59 (İstanbul)')

        db.session.commit()
        print('TAMAM: ' + event.external_url)
