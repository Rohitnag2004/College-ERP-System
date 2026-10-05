from django.db import migrations


# Each list describes a semester sequence of draft subject suggestions. The
# entries are intentionally marked draft in the database for institutional review.
CURRICULA = {
    "cse": [
        ["Programming Fundamentals", "Engineering Mathematics I", "Digital Logic", "Communication Skills"],
        ["Object-Oriented Programming", "Data Structures", "Engineering Mathematics II", "Computer Organization"],
        ["Algorithms", "Database Systems", "Operating Systems", "Probability and Statistics"],
        ["Computer Networks", "Software Engineering", "Theory of Computation", "Web Technologies"],
        ["Compiler Design", "Distributed Systems", "Information Security", "Software Testing"],
        ["Cloud Computing", "Mobile Application Development", "Machine Learning Foundations", "Professional Elective I"],
        ["DevOps and Site Reliability", "Internet of Things", "Professional Elective II", "Project I"],
        ["Advanced Computing Seminar", "Professional Elective III", "Industry Internship", "Capstone Project"],
    ],
    "ai": [
        ["Programming for AI", "Mathematics for AI", "Digital Systems", "Communication Skills"],
        ["Data Structures", "Object-Oriented Programming", "Linear Algebra", "Computer Organization"],
        ["Foundations of Artificial Intelligence", "Algorithms", "Probability and Statistics", "Database Systems"],
        ["Machine Learning", "Data Engineering", "Computer Networks", "Software Engineering"],
        ["Deep Learning", "Natural Language Processing", "Computer Vision", "AI Ethics"],
        ["Generative AI", "Reinforcement Learning", "Big Data Analytics", "MLOps"],
        ["AI Security and Privacy", "Research Methods", "Industry Project I", "Professional Elective"],
        ["AI Systems Engineering", "Technology Entrepreneurship", "Industry Internship", "Capstone Project"],
    ],
    "cyber": [
        ["Programming Fundamentals", "Discrete Mathematics", "Digital Logic", "Communication Skills"],
        ["Data Structures", "Computer Organization", "Network Fundamentals", "Applied Mathematics"],
        ["Operating Systems", "Database Security", "Algorithms", "Probability and Statistics"],
        ["Cryptography", "Computer Networks", "Web Application Security", "Security Laws and Ethics"],
        ["Ethical Hacking", "Digital Forensics", "Secure Software Design", "Cloud Security"],
        ["Network Defense", "Incident Response", "Penetration Testing Lab", "Security Governance"],
        ["Threat Intelligence", "Malware Analysis", "Security Audit", "Industry Project I"],
        ["Advanced Forensics", "Cyber Risk Management", "Industry Internship", "Security Capstone"],
    ],
    "data": [
        ["Programming Fundamentals", "Mathematics for Data Science", "Digital Logic", "Communication Skills"],
        ["Data Structures", "Linear Algebra", "Database Systems", "Computer Organization"],
        ["Probability and Statistics", "Algorithms", "Data Wrangling", "Operating Systems"],
        ["Machine Learning", "Data Visualization", "Data Warehousing", "Software Engineering"],
        ["Big Data Platforms", "Deep Learning", "Data Mining", "Cloud Computing"],
        ["Time Series Analytics", "Natural Language Processing", "MLOps", "Business Intelligence"],
        ["Responsible Data Science", "Research Methods", "Industry Project I", "Professional Elective"],
        ["Advanced Analytics", "Data Product Design", "Industry Internship", "Capstone Project"],
    ],
    "robotics": [
        ["Engineering Mathematics", "Programming for Robotics", "Engineering Mechanics", "Electrical Fundamentals"],
        ["Digital Electronics", "Sensors and Instrumentation", "Data Structures", "Mechanics of Machines"],
        ["Microcontrollers", "Control Systems", "Computer-Aided Design", "Probability and Statistics"],
        ["Embedded Systems", "Robot Kinematics", "Industrial Automation", "Computer Vision"],
        ["Robot Dynamics", "PLC and SCADA", "Machine Learning for Robotics", "Mechatronics Lab"],
        ["Autonomous Systems", "Robot Operating Systems", "Industrial Robotics", "Safety Engineering"],
        ["Human-Robot Interaction", "Research and Design Methods", "Industry Project I", "Professional Elective"],
        ["Smart Manufacturing", "Robotics Integration", "Industry Internship", "Capstone Project"],
    ],
    "business": [
        ["Principles of Management", "Business Communication", "Microeconomics", "Business Mathematics"],
        ["Organizational Behaviour", "Financial Accounting", "Marketing Principles", "Business Statistics"],
        ["Human Resource Management", "Cost Accounting", "Business Law", "Management Information Systems"],
        ["Operations Management", "Corporate Finance", "Consumer Behaviour", "Research Methods"],
        ["Strategic Management", "Entrepreneurship", "Business Analytics", "Professional Elective I"],
        ["Supply Chain Management", "Digital Business", "Leadership and Ethics", "Professional Elective II"],
        ["Innovation Management", "Project Management", "Industry Project I", "Professional Elective III"],
        ["Corporate Strategy", "Business Simulation", "Industry Internship", "Capstone Project"],
    ],
    "marketing": [
        ["Principles of Management", "Business Communication", "Marketing Fundamentals", "Business Mathematics"],
        ["Consumer Behaviour", "Market Research", "Financial Accounting", "Business Statistics"],
        ["Brand Management", "Digital Marketing", "Content Strategy", "Business Law"],
        ["Search Marketing", "Social Media Strategy", "Marketing Analytics", "Public Relations"],
        ["E-Commerce", "Performance Marketing", "Marketing Automation", "Research Methods"],
        ["Integrated Campaign Design", "Customer Relationship Management", "Retail Marketing", "Ethics and Privacy"],
        ["Global Marketing", "Growth Strategy", "Industry Project I", "Professional Elective"],
        ["Strategic Brand Leadership", "Agency Practice", "Industry Internship", "Capstone Project"],
    ],
    "analytics": [
        ["Principles of Management", "Business Communication", "Business Mathematics", "Accounting Fundamentals"],
        ["Business Statistics", "Database Fundamentals", "Microeconomics", "Organizational Behaviour"],
        ["Data Visualization", "Operations Management", "Financial Analytics", "Marketing Principles"],
        ["Predictive Analytics", "Business Intelligence", "Research Methods", "Decision Science"],
        ["Data Mining for Business", "Supply Chain Analytics", "Customer Analytics", "Corporate Finance"],
        ["Machine Learning for Business", "Risk Analytics", "Data Governance", "Strategy"],
        ["Analytics Consulting", "Experiment Design", "Industry Project I", "Professional Elective"],
        ["Responsible AI for Business", "Executive Decision Lab", "Industry Internship", "Capstone Project"],
    ],
    "commerce": [
        ["Financial Accounting I", "Business Economics", "Business Communication", "Business Mathematics"],
        ["Financial Accounting II", "Business Statistics", "Business Law", "Principles of Management"],
        ["Corporate Accounting", "Cost Accounting", "Banking Principles", "Income Tax Fundamentals"],
        ["Financial Management", "Auditing", "Company Law", "Management Information Systems"],
        ["Investment Analysis", "GST and Indirect Taxation", "Management Accounting", "Financial Markets"],
        ["Banking Operations", "Corporate Tax Planning", "Accounting Information Systems", "Research Methods"],
        ["Risk Management", "Financial Reporting Standards", "Industry Project I", "Professional Elective"],
        ["Portfolio Management", "Corporate Governance", "Industry Internship", "Capstone Project"],
    ],
    "pharmacy": [
        ["Human Anatomy and Physiology I", "Pharmaceutical Analysis I", "Pharmaceutics I", "Pharmaceutical Inorganic Chemistry"],
        ["Human Anatomy and Physiology II", "Pharmaceutical Organic Chemistry I", "Biochemistry", "Pathophysiology"],
        ["Pharmaceutics II", "Pharmaceutical Microbiology", "Pharmaceutical Organic Chemistry II", "Pharmacognosy"],
        ["Pharmacology I", "Medicinal Chemistry I", "Pharmaceutical Engineering", "Pharmacognosy and Phytochemistry"],
        ["Pharmacology II", "Medicinal Chemistry II", "Industrial Pharmacy", "Pharmaceutical Jurisprudence"],
        ["Pharmacology III", "Herbal Drug Technology", "Biopharmaceutics", "Quality Assurance"],
        ["Instrumental Methods of Analysis", "Pharmacy Practice", "Research Methods", "Elective in Pharmacy"],
        ["Clinical Pharmacy", "Novel Drug Delivery", "Industrial Training", "Research Project"],
    ],
    "nursing": [
        ["Anatomy and Physiology", "Nursing Foundations", "Nutrition and Dietetics", "Psychology"],
        ["Applied Biochemistry", "Community Health Nursing I", "Medical-Surgical Nursing I", "Microbiology"],
        ["Pharmacology", "Medical-Surgical Nursing II", "Pathology and Genetics", "Sociology"],
        ["Child Health Nursing", "Mental Health Nursing", "Community Health Nursing II", "Nursing Education"],
        ["Midwifery and Obstetric Nursing I", "Nursing Research", "Medical-Surgical Nursing III", "Health Informatics"],
        ["Midwifery and Obstetric Nursing II", "Nursing Management", "Critical Care Nursing", "Clinical Practice I"],
        ["Advanced Community Health", "Emergency Nursing", "Clinical Practice II", "Leadership in Nursing"],
        ["Nursing Administration", "Evidence-Based Practice", "Clinical Internship", "Nursing Project"],
    ],
    "optometry": [
        ["General Anatomy and Physiology", "Geometrical Optics", "Ocular Anatomy", "Biochemistry"],
        ["Physical and Physiological Optics", "Ocular Physiology", "Optometric Instruments", "General Pathology"],
        ["Optometric Optics I", "Clinical Refraction I", "Ocular Disease I", "Visual Psychology"],
        ["Clinical Refraction II", "Contact Lens I", "Binocular Vision", "Pharmacology for Optometry"],
        ["Contact Lens II", "Low Vision Care", "Ocular Disease II", "Community Optometry"],
        ["Paediatric Optometry", "Clinical Optometry", "Public Health Optometry", "Research Methods"],
        ["Advanced Contact Lenses", "Geriatric Optometry", "Clinical Case Studies", "Elective in Vision Science"],
        ["Ocular Rehabilitation", "Optometry Practice Management", "Clinical Internship", "Research Project"],
    ],
    "physio": [
        ["Human Anatomy I", "Human Physiology I", "Biomechanics", "Psychology and Sociology"],
        ["Human Anatomy II", "Human Physiology II", "Exercise Therapy I", "Electrotherapy I"],
        ["Pathology", "Exercise Therapy II", "Electrotherapy II", "General Medicine"],
        ["Orthopaedics", "Neurology", "Physical Agents", "Research Methods"],
        ["Musculoskeletal Physiotherapy", "Neurological Physiotherapy", "General Surgery", "Community Health"],
        ["Cardiorespiratory Physiotherapy", "Paediatric Physiotherapy", "Rehabilitation Science", "Clinical Practice I"],
        ["Sports Physiotherapy", "Geriatric Rehabilitation", "Evidence-Based Practice", "Clinical Practice II"],
        ["Advanced Rehabilitation", "Physiotherapy Management", "Clinical Internship", "Research Project"],
    ],
    "clinical": [
        ["Human Anatomy and Physiology", "Medical Terminology", "Basic Biochemistry", "Patient Care Fundamentals"],
        ["Pathology", "Microbiology", "Clinical Laboratory Practice", "Medical Ethics"],
        ["Clinical Biochemistry", "Haematology", "Diagnostic Instrumentation", "Applied Pharmacology"],
        ["Immunology", "Transfusion Science", "Clinical Microbiology", "Quality Systems"],
        ["Advanced Diagnostics", "Critical Care Procedures", "Emergency Patient Care", "Research Methods"],
        ["Laboratory Management", "Clinical Case Studies", "Patient Safety", "Clinical Practice"],
        ["Advanced Clinical Practice", "Research Seminar", "Professional Elective", "Clinical Internship I"],
        ["Evidence-Based Diagnostics", "Professional Practice", "Clinical Internship II", "Research Project"],
    ],
    "agriculture": [
        ["Fundamentals of Agronomy", "Agricultural Botany", "Soil Science", "Agricultural Economics"],
        ["Crop Physiology", "Genetics and Plant Breeding", "Agricultural Microbiology", "Farm Machinery"],
        ["Field Crop Production", "Plant Pathology", "Agricultural Meteorology", "Soil Fertility Management"],
        ["Horticultural Crops", "Entomology", "Irrigation Management", "Agricultural Extension"],
        ["Seed Science and Technology", "Weed Management", "Plant Breeding Methods", "Farm Management"],
        ["Integrated Pest Management", "Post-Harvest Technology", "Water Resource Management", "Research Methods"],
        ["Precision Agriculture", "Sustainable Farming Systems", "Rural Development", "Field Project I"],
        ["Agri-Business Management", "Climate-Smart Agriculture", "Industry Internship", "Research Project"],
    ],
    "animation": [
        ["Drawing and Visual Design", "Digital Imaging", "Design Fundamentals", "Communication Skills"],
        ["2D Animation", "Typography", "Photography", "Storyboarding"],
        ["3D Modelling", "Character Design", "Video Editing", "Visual Storytelling"],
        ["3D Animation", "Lighting and Rendering", "Sound Design", "Compositing"],
        ["Visual Effects I", "Game Art and Assets", "Motion Graphics", "Interactive Media"],
        ["Visual Effects II", "Game Design", "Virtual Production", "Production Management"],
        ["Advanced Compositing", "Real-Time Graphics", "Portfolio Development", "Industry Project I"],
        ["Animation Direction", "Digital Production Studio", "Industry Internship", "Capstone Film or Game"],
    ],
    "media": [
        ["Introduction to Media Studies", "Writing for Media", "Communication Theory", "Media History"],
        ["Reporting and News Writing", "Photography", "Audio Production", "Media Law and Ethics"],
        ["Video Production", "Editing and Post-Production", "Public Relations", "Digital Journalism"],
        ["Broadcast Journalism", "Documentary Production", "Advertising Principles", "Media Research"],
        ["Investigative Journalism", "Social Media Publishing", "Media Economics", "Visual Communication"],
        ["Data Journalism", "Film and Television Studies", "Audience Analytics", "Communication Campaigns"],
        ["Media Entrepreneurship", "Advanced Production", "Industry Project I", "Professional Elective"],
        ["Editorial Practice", "Media Portfolio", "Industry Internship", "Capstone Production"],
    ],
    "english": [
        ["Introduction to Literary Studies", "Academic Writing", "British Literature I", "Language and Communication"],
        ["British Literature II", "Indian Writing in English", "Linguistics", "Critical Reading"],
        ["American Literature", "Literary Theory I", "Creative Writing", "English Language Teaching"],
        ["Postcolonial Literature", "World Literature", "Literary Theory II", "Professional Communication"],
        ["Modern Literature", "Translation Studies", "Research Methods", "Rhetoric and Composition"],
        ["Contemporary Literature", "Digital Humanities", "Gender and Literature", "Applied Linguistics"],
        ["Literature and Environment", "Advanced Literary Criticism", "Project Seminar", "Professional Elective"],
        ["Comparative Literature", "Publishing and Editing", "Teaching Practicum", "Research Project"],
    ],
    "law": [
        ["Legal Methods", "Law of Contract I", "Law of Torts", "Legal English"],
        ["Constitutional Law I", "Law of Contract II", "Family Law I", "Criminal Law I"],
        ["Constitutional Law II", "Property Law", "Family Law II", "Criminal Procedure"],
        ["Administrative Law", "Company Law", "Jurisprudence", "Civil Procedure"],
        ["Public International Law", "Labour Law", "Environmental Law", "Alternative Dispute Resolution"],
        ["Evidence Law", "Taxation Law", "Intellectual Property Law", "Professional Ethics"],
        ["Human Rights Law", "Competition Law", "Drafting and Pleading", "Clinical Legal Education"],
        ["Banking and Insurance Law", "Cyber Law", "Moot Court Practice", "Research Methods in Law"],
        ["Advanced Constitutional Studies", "International Trade Law", "Dissertation Seminar", "Legal Aid Clinic"],
        ["Advanced Legal Elective", "Corporate and Regulatory Practice", "Moot Court and Internship", "Dissertation"],
    ],
    "mathematics": [
        ["Linear Algebra", "Real Analysis I", "Abstract Algebra I", "Differential Equations"],
        ["Real Analysis II", "Abstract Algebra II", "Complex Analysis", "Numerical Methods"],
        ["Topology", "Functional Analysis", "Probability Theory", "Operations Research"],
        ["Advanced Algebra", "Mathematical Modelling", "Statistics", "Research Project"],
    ],
    "psychology": [
        ["Foundations of Psychology", "Research Methods", "Biological Psychology", "Cognitive Processes"],
        ["Developmental Psychology", "Social Psychology", "Psychological Statistics", "Personality Theories"],
        ["Clinical Psychology", "Psychological Assessment", "Counselling Skills", "Abnormal Psychology"],
        ["Health Psychology", "Organizational Psychology", "Advanced Research Methods", "Dissertation"],
    ],
    "biological": [
        ["Cell Biology", "Biochemistry", "Genetics", "Biostatistics"],
        ["Molecular Biology", "Microbiology", "Immunology", "Laboratory Methods"],
        ["Genetic Engineering", "Cell Culture Technology", "Bioinformatics", "Research Methods"],
        ["Applied Biotechnology", "Omics and Systems Biology", "Industrial Training", "Research Project"],
    ],
    "bioinformatics": [
        ["Biochemistry", "Cell and Molecular Biology", "Programming for Life Sciences", "Biostatistics"],
        ["Genomics", "Database Systems for Biology", "Algorithms in Bioinformatics", "Molecular Genetics"],
        ["Proteomics", "Sequence Analysis", "Structural Bioinformatics", "Machine Learning in Biology"],
        ["Systems Biology", "Computational Drug Discovery", "Research Internship", "Dissertation"],
    ],
    "nutrition": [
        ["Human Nutrition", "Food Chemistry", "Human Physiology", "Nutrition Assessment"],
        ["Clinical Nutrition", "Food Microbiology", "Community Nutrition", "Research Statistics"],
        ["Medical Nutrition Therapy", "Public Health Nutrition", "Food Service Management", "Nutrition Across the Lifespan"],
        ["Advanced Dietetics", "Nutrition Research Methods", "Clinical Internship", "Dissertation"],
    ],
    "electrical": [
        ["Electrical Circuit Theory", "Engineering Mathematics", "Engineering Physics", "Engineering Drawing"],
        ["Electrical Machines I", "Analog Electronics", "Measurements and Instrumentation", "Applied Mathematics"],
        ["Electrical Machines II", "Power Systems", "Digital Electronics", "Electrical Workshop"],
        ["Power Electronics", "Control Systems", "Microcontrollers", "Electrical Safety"],
        ["Renewable Energy Systems", "Switchgear and Protection", "Industrial Automation", "Electrical Design"],
        ["Smart Grid Fundamentals", "Energy Management", "Industrial Training", "Diploma Project"],
    ],
    "mechanical": [
        ["Engineering Mathematics", "Engineering Mechanics", "Engineering Drawing", "Workshop Practice"],
        ["Strength of Materials", "Thermodynamics", "Manufacturing Processes", "Material Science"],
        ["Fluid Mechanics", "Machine Design", "Metrology", "Applied Mechanics"],
        ["Heat Transfer", "Theory of Machines", "CNC Technology", "Mechanical Measurements"],
        ["Automobile Engineering", "Refrigeration and Air Conditioning", "Industrial Engineering", "CAD and CAM"],
        ["Renewable Energy", "Maintenance Engineering", "Industrial Training", "Diploma Project"],
    ],
    "civil": [
        ["Engineering Mathematics", "Engineering Mechanics", "Building Materials", "Engineering Drawing"],
        ["Surveying", "Strength of Materials", "Building Construction", "Fluid Mechanics"],
        ["Structural Analysis", "Concrete Technology", "Geotechnical Engineering", "Hydraulics"],
        ["Reinforced Concrete Design", "Transportation Engineering", "Environmental Engineering", "Quantity Surveying"],
        ["Steel Structures", "Water Supply Engineering", "Construction Management", "Foundation Engineering"],
        ["Estimation and Costing", "Urban Infrastructure", "Industrial Training", "Diploma Project"],
    ],
}


def curriculum_key(name):
    value = name.lower()
    if "bioinformatics" in value:
        return "bioinformatics"
    if "nutrition" in value or "dietetics" in value:
        return "nutrition"
    if "psychology" in value:
        return "psychology"
    if "mathematics" in value:
        return "mathematics"
    if "agriculture" in value or "agronomy" in value or "horticulture" in value:
        return "agriculture"
    if "llb" in value or "llm" in value or "law" in value:
        return "law"
    if "pharm" in value:
        return "pharmacy"
    if "nursing" in value or "gnm" in value:
        return "nursing"
    if "optom" in value:
        return "optometry"
    if "physio" in value or "bpt" in value:
        return "physio"
    if "critical care" in value or "cct" in value or "medical laboratory" in value or "dmls" in value or "mls" in value:
        return "clinical"
    if "animation" in value or "vfx" in value or "gaming" in value or "multimedia" in value:
        return "animation"
    if "media" in value or "journalism" in value:
        return "media"
    if "english" in value:
        return "english"
    if "biotechnology" in value:
        return "biological"
    if "business analytics" in value or "analytics" in value:
        return "analytics"
    if "digital marketing" in value:
        return "marketing"
    if "hospital management" in value or "healthcare" in value:
        return "business"
    if "b.com" in value or "m.com" in value or "banking" in value or "financial accounting" in value or "finance" in value:
        return "commerce"
    if "bba" in value or "mba" in value:
        return "business"
    if "electrical" in value:
        return "electrical"
    if "mechanical" in value:
        return "mechanical"
    if "civil" in value:
        return "civil"
    if "robot" in value or "automation" in value:
        return "robotics"
    if "cyber" in value or "network" in value:
        return "cyber"
    if "data science" in value:
        return "data"
    if "artificial intelligence" in value or "ai & ml" in value or "bca (hons) - ai" in value:
        return "ai"
    if "mobile app" in value or "web technology" in value:
        return "cse"
    return "cse"


def seed_curricula(apps, schema_editor):
    Course = apps.get_model("main_app", "Course")
    Semester = apps.get_model("main_app", "Semester")
    Subject = apps.get_model("main_app", "Subject")
    db_alias = schema_editor.connection.alias
    existing = set(Subject.objects.using(db_alias).values_list("course_id", "semester_id", "name"))
    additions = []
    for course in Course.objects.using(db_alias).all().iterator():
        blueprint = CURRICULA[curriculum_key(course.name)]
        semesters = Semester.objects.using(db_alias).filter(course_id=course.pk).order_by("number")
        is_lateral = "lateral entry" in course.name.lower()
        is_postgraduate = course.name.lower().startswith(("m.", "mba", "mca", "llm", "ma "))
        for index, semester in enumerate(semesters):
            source_index = index + (2 if is_lateral and len(semesters) >= 4 else 0)
            if is_postgraduate and len(semesters) == 4:
                source_index = max(0, len(blueprint) - 4) + index
            modules = blueprint[source_index % len(blueprint)]
            for title in modules:
                key = (course.pk, semester.pk, title)
                if key not in existing:
                    additions.append(Subject(
                        name=title, course_id=course.pk, semester_id=semester.pk,
                        staff_id=None, is_draft=True,
                    ))
                    existing.add(key)
    Subject.objects.using(db_alias).bulk_create(additions, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("main_app", "0011_curriculum_drafts_and_single_enrollment")]

    operations = [migrations.RunPython(seed_curricula, migrations.RunPython.noop)]
