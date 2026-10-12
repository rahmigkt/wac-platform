"""WAC 2027 başvuru ve kayıt formlarını (event 2) oluşturur.

  sudo -u indico -i /opt/indico/.venv/bin/python /tmp/f.py
Tekrar çalıştırılırsa var olan formları atlar. Sonda form numaralarını yazar.
"""
from indico.web.flask.app import make_app

EVENT_ID = 2
T, A, F, C = 'text', 'textarea', 'file', 'checkbox'
CONSENT = ('Kişisel verilerimin başvurunun değerlendirilmesi amacıyla işlenmesini kabul ediyorum / '
           'I consent to the processing of my personal data for evaluating this application', C, True)

FORMS = [
    ('kayit', 'Kongre kaydı / Congress registration', False, [
        ('Katılımcı türü (akademisyen, sektör, öğrenci, diğer) / Participant type', T, True),
        ('Katılmak istediğiniz sempozyum eksenleri / Symposium axes of interest', A, False),
        ('Öğrenci ise öğrenci belgesi / Student certificate (if student)', F, False),
        CONSENT]),
    ('delegasyon', 'Ülke delegasyonu başvurusu / National delegation application', True, [
        ('Kurumun tam unvanı / Full name of the institution', T, True),
        ('Ülke / Country', T, True),
        ('Kurum türü ve yasal statüsü / Type and legal status', T, True),
        ('Kuruluş yılı / Year of establishment', T, True),
        ('Yetkili temsilcinin adı ve unvanı / Authorised representative and title', T, True),
        ('Kurum web sitesi / Website', T, False),
        ('Kurum tanıtımı / Institutional profile', A, True),
        ('Katkı planı: sempozyum, forum, uzman ve oturum önerileri / Contribution plan', A, True),
        ('Yasal statü veya yetki belgesi / Legal status or authorisation document', F, True),
        CONSENT]),
    ('fuar', 'Fuar ve pavyon başvurusu / Expo and pavilion application', True, [
        ('Firma veya kurum / Company or institution', T, True),
        ('Ülke / Country', T, True),
        ('Pavyon kategorisi (Standart, Büyük, Premium, Kurumsal) / Pavilion category', T, True),
        ('Sergilenecek ürün ve teknolojiler / Products and technologies', A, True),
        ('Web sitesi / Website', T, False),
        ('Firma tanıtım dosyası / Company profile', F, False),
        CONSENT]),
    ('konusmaci', 'Konuşmacı ve uzman önerisi / Speaker and expert proposal', True, [
        ('Önerilen kişinin adı, unvanı ve kurumu / Proposed person, title, institution', T, True),
        ('Önerilen kişinin e-postası / E-mail of the proposed person', T, False),
        ('İlgili eksen veya forum başlığı / Related axis or forum topic', T, True),
        ('Öneri gerekçesi ve konu / Rationale and topic', A, True),
        ('Özgeçmiş / CV', F, False),
        CONSENT]),
    ('isbirligi', 'Sponsorluk ve iş birliği / Sponsorship and cooperation', True, [
        ('Kurum / Organisation', T, True),
        ('İş birliği türü (sponsorluk, akademik, program desteği) / Type of cooperation', T, True),
        ('Teklif veya görüşme talebi / Proposal or request', A, True),
        ('Ek dosya / Attachment', F, False),
        CONSENT]),
    ('evsahipligi', 'Ev sahipliği adaylığı / Hosting candidacy', True, [
        ('Aday ülke ve şehir / Candidate country and city', T, True),
        ('Başvuran delegasyon / Applying delegation', T, True),
        ('Önerilen kongre yılı ve tarih aralığı / Proposed year and dates', T, True),
        ('Mekân, ulaşım, konaklama, güvenlik ve sağlık altyapısı / Venue and infrastructure', A, True),
        ('Mali plan özeti / Financial plan summary', A, True),
        ('Adaylık dosyası / Candidacy dossier', F, True),
        CONSENT]),
]

app = make_app()
with app.app_context():
    from indico.core.db import db
    from indico.modules.events import Event
    from indico.modules.events.features.util import set_feature_enabled
    from indico.modules.events.registration.models.form_fields import RegistrationFormField
    from indico.modules.events.registration.models.forms import RegistrationForm
    from indico.modules.events.registration.models.items import RegistrationFormSection
    from indico.modules.events.registration.util import create_personal_data_fields
    from indico.util.date_time import now_utc

    event = Event.get(EVENT_ID)
    set_feature_enabled(event, 'registration', True)
    out = []
    for key, title, moderated, fields in FORMS:
        rf = RegistrationForm.query.filter_by(event=event, title=title, is_deleted=False).first()
        if rf:
            out.append((key, rf.id, 'vardı'))
            continue
        rf = RegistrationForm(event=event, title=title, currency='EUR')
        create_personal_data_fields(rf)
        for f in rf.active_fields:
            if f.personal_data_type and f.personal_data_type.name in ('affiliation', 'position', 'country', 'phone'):
                f.is_enabled = True
        rf.moderation_enabled = moderated
        rf.start_dt = now_utc()
        sec = RegistrationFormSection(registration_form=rf, title='Başvuru bilgileri / Application details')
        db.session.add(rf)
        db.session.flush()
        for ftitle, ftype, req in fields:
            fld = RegistrationFormField(registration_form=rf, parent=sec, title=ftitle,
                                        input_type=ftype, is_required=req)
            try:
                data = fld.field_impl.create_setup_schema().load({})
            except Exception:
                data = {}
            fld.data, fld.versioned_data = fld.field_impl.process_field_data(data)
        db.session.flush()
        out.append((key, rf.id, 'oluşturuldu'))
    db.session.commit()
    for key, i, s in out:
        print(f'{key}={i} {s}')
    print('TAMAM')
