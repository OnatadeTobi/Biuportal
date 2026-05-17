"""Student identity lookup by matric number.

Replace MOCK_STUDENTS / fetch_student_by_matric with a real external API when available.
"""

MOCK_STUDENTS = [
    {
        'matric_number': 'BIU/23/CSC/001',
        'full_name': 'Samuel Asije',
        'email': 'samuel.asije@example.com',
    },
    {
        'matric_number': 'BIU/23/CSC/002',
        'full_name': 'Jane Doe',
        'email': 'jane.doe@example.com',
    },
    {
        'matric_number': 'BIU/23/CSC/003',
        'full_name': 'David Johnson',
        'email': 'david.johnson@example.com',
    },
]


def fetch_student_by_matric(matric_number):
    """
    Look up official student identity by matric number.

    Returns dict with full_name, email, matric_number or None if not found.
    """
    normalized = (matric_number or '').strip()
    for student in MOCK_STUDENTS:
        if student['matric_number'] == normalized:
            return {
                'full_name': student['full_name'],
                'email': student['email'],
                'matric_number': student['matric_number'],
            }
    return None
