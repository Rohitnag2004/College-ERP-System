from decimal import Decimal

from django.db import migrations


COURSES = [
    # Undergraduate programmes
    ("B.Tech - Computer Science & Engineering", "4 years", "579600", "579600", "Undergraduate engineering programme."),
    ("B.Tech - Artificial Intelligence & Machine Learning", "4 years", "579600", "579600", "Undergraduate engineering programme."),
    ("B.Tech - Cyber Security", "4 years", "579600", "579600", "Undergraduate engineering programme."),
    ("B.Tech - Data Science & AI", "4 years", "579600", "579600", "Undergraduate engineering programme."),
    ("B.Tech - AI & Robotics", "4 years", "579600", "579600", "Undergraduate engineering programme."),
    ("B.Tech (Lateral Entry) - CSE", "3 years", "256200", "256200", "Lateral entry programme."),
    ("B.Tech (Lateral Entry) - AI & ML", "3 years", "256200", "256200", "Lateral entry programme."),
    ("B.Tech (Lateral Entry) - Cyber Security", "3 years", "256200", "256200", "Lateral entry programme."),
    ("B.Tech (Lateral Entry) - Data Science", "3 years", "256200", "256200", "Lateral entry programme."),
    ("B.Tech (Lateral Entry) - Robotics", "3 years", "256200", "256200", "Lateral entry programme."),
    ("BCA (Hons) - General", "4 years", "482600", "498600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("BCA (Hons) - AI & ML", "4 years", "482600", "498600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("BCA (Hons) - Mobile App & Web Technology", "4 years", "482600", "498600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("B.Sc (Hons) - Advanced Networking & Cyber Security", "4 years", "407600", "407600", "Undergraduate programme."),
    ("BBA (Hons) - General", "4 years", "472600", "492600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("BBA (Hons) - Digital Marketing", "4 years", "472600", "492600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("BBA (Hons) - Business Analytics", "4 years", "472600", "492600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("BBA (Hons) - Hospital Management", "4 years", "472600", "492600", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("B.Com (Hons) - Accounts, Finance & Banking", "4 years", "292600", "292600", "Undergraduate programme."),
    ("B.Pharm", "4 years", "729600", "729600", "Undergraduate pharmacy programme."),
    ("B.Pharm (Lateral Entry)", "3 years", "496200", "496200", "Lateral entry pharmacy programme."),
    ("B.Sc Nursing", "4 years", "691000", "691000", "For female applicants only, as stated in the supplied course details."),
    ("B.Optom - Bachelor of Optometry", "4 years + 1 year internship", "457200", "457200", "Includes a one-year internship."),
    ("BPT - Bachelor of Physiotherapy", "4 years + 1 year internship", "457200", "699600", "Published programme fee is a range; confirm the applicable amount with the administration. Includes a one-year internship."),
    ("B.Sc CCT - Critical Care Technology", "3 years + 1 year internship", "429200", "429200", "Includes a one-year internship."),
    ("BMLT / B.Sc MLS - Medical Laboratory Technology / Science", "3 years + 1 year internship", "429000", "429000", "Includes a one-year internship."),
    ("B.Sc (Hons) - Agriculture", "4 years", "459600", "459600", "Undergraduate programme."),
    ("B.Sc (Hons) - Animation, VFX & Gaming", "3-4 years", "302200", "518000", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("B.Sc (Hons) - Media Science & Journalism", "3-4 years", "302200", "518000", "Published programme fee is a range; confirm the applicable amount with the administration."),
    ("BA (Hons) - Applied English", "4 years", "217600", "217600", "Undergraduate programme."),
    ("BA LLB - Integrated Law", "5 years", "577000", "577000", "Integrated law programme."),
    ("BBA LLB - Integrated Law", "5 years", "577000", "577000", "Integrated law programme."),
    ("LLB - Bachelor of Laws", "3 years", "355200", "355200", "Undergraduate law programme."),
    # Postgraduate programmes
    ("M.Tech - Computer Science & Engineering", "2 years", "289800", "289800", "Postgraduate programme."),
    ("M.Tech CSE - Artificial Intelligence & Machine Learning", "2 years", "289800", "289800", "Postgraduate programme."),
    ("M.Tech CSE - Data Science", "2 years", "289800", "289800", "Postgraduate programme."),
    ("M.Tech - Robotics & Automation", "2 years", "289800", "289800", "Postgraduate programme."),
    ("MCA - Master of Computer Applications", "2 years", "299800", "299800", "Postgraduate programme."),
    ("M.Sc - Advanced Networking & Cyber Security", "2 years", "269800", "269800", "Postgraduate programme."),
    ("M.Sc - Mathematics", "2 years", "129800", "129800", "Postgraduate programme."),
    ("MBA - General Management", "2 years", "509800", "509800", "Postgraduate programme."),
    ("MBA - Healthcare & Hospital Management", "2 years", "509800", "509800", "Postgraduate programme."),
    ("M.Com - Banking & Financial Accounting", "2 years", "139800", "139800", "Postgraduate programme."),
    ("M.Pharm - Pharmaceutics", "2 years", "399800", "399800", "Postgraduate programme."),
    ("M.Pharm - Pharmaceutical Chemistry", "2 years", "399800", "399800", "Postgraduate programme."),
    ("M.Optom - Master of Optometry", "2 years", "259800", "259800", "Postgraduate programme."),
    ("M.MLS - Master of Medical Laboratory Science", "2 years", "259800", "259800", "Postgraduate programme."),
    ("M.Sc - Nutrition & Dietetics", "2 years", "209800", "209800", "Postgraduate programme."),
    ("M.Sc - Biotechnology", "2 years", "229800", "229800", "Postgraduate programme."),
    ("M.Sc - Bioinformatics", "2 years", "229800", "229800", "Postgraduate programme."),
    ("M.Sc Agriculture - Agronomy", "2 years", "219800", "219800", "Postgraduate programme."),
    ("M.Sc Agriculture - Horticulture", "2 years", "219800", "219800", "Postgraduate programme."),
    ("LLM - Master of Law", "2 years", "239800", "239800", "Postgraduate programme."),
    ("M.Sc - Animation & Multimedia", "2 years", "369800", "369800", "Postgraduate programme."),
    ("M.Sc - Media Science & Journalism", "2 years", "249800", "249800", "Postgraduate programme."),
    ("MA - English", "2 years", "109800", "109800", "Postgraduate programme."),
    ("M.Sc - Applied Psychology", "2 years", "149800", "149800", "Postgraduate programme."),
    # Diploma programmes
    ("Diploma in Engineering - CSE", "3 years", "182200", "182200", "Diploma programme."),
    ("Diploma in Engineering (Lateral Entry) - CSE", "2 years", "134800", "134800", "Lateral entry diploma programme."),
    ("Diploma in Engineering - Electrical Engineering", "3 years", "162200", "162200", "Diploma programme."),
    ("Diploma in Engineering (Lateral Entry) - Electrical Engineering", "2 years", "134800", "134800", "Lateral entry diploma programme."),
    ("Diploma in Engineering - Mechanical Engineering", "3 years", "162200", "162200", "Diploma programme."),
    ("Diploma in Engineering (Lateral Entry) - Mechanical Engineering", "2 years", "134800", "134800", "Lateral entry diploma programme."),
    ("Diploma in Engineering - Civil Engineering", "3 years", "137200", "137200", "Diploma programme."),
    ("Diploma in Robotics (Lateral Entry) - Robotics & Automation", "2 years", "124800", "124800", "Lateral entry diploma programme."),
    ("D.Pharm - Diploma in Pharmacy", "2 years", "337400", "337400", "Diploma pharmacy programme."),
    ("GNM - General Nursing & Midwifery", "3 years", "501000", "501000", "Diploma programme."),
    ("DMLS - Diploma in Medical Laboratory Science", "2 years + 6 months internship", "139800", "139800", "Includes a six-month internship."),
]


def seed_catalog(apps, schema_editor):
    Course = apps.get_model("main_app", "Course")
    names = [row[0] for row in COURSES]
    existing_names = set(Course.objects.filter(name__in=names).values_list("name", flat=True))
    Course.objects.bulk_create([
        Course(
            name=name,
            duration=duration,
            tuition_fee_min=Decimal(low),
            tuition_fee_max=Decimal(high),
            description=description,
            is_active=True,
        )
        for name, duration, low, high, description in COURSES
        if name not in existing_names
    ], batch_size=100)


class Migration(migrations.Migration):
    dependencies = [("main_app", "0003_course_duration_course_tuition_fee_max_and_more")]

    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
