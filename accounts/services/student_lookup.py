import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

class BIUPortalError(Exception):
    def __init__(self, message, status_code=502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class BIUPortalTimeout(BIUPortalError):
    def __init__(self):
        super().__init__("BIU portal request timed out.", status_code=504)

class BIUPortalUnavailable(BIUPortalError):
    def __init__(self):
        super().__init__("BIU portal is currently unreachable.", status_code=502)

class StudentNotFound(BIUPortalError):
    def __init__(self):
        super().__init__("Student record not found.", status_code=404)

class BIUPortalParseError(BIUPortalError):
    def __init__(self):
        super().__init__("Failed to parse student data from BIU portal.", status_code=500)

def fetch_biu_student_details(matric_no: str) -> dict:
    """
    Fetch and parse student details from the external BIU portal.
    """
    base_url = "https://cell.biuportal.net/Student_Register.aspx"
    params = {'matric_no': matric_no}
    full_url = f"{base_url}?{urlencode(params)}"
    
    headers = {
        "User-Agent": "BIU-Key-Management-System/1.0"
    }
    
    try:
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise BIUPortalTimeout()
    except requests.exceptions.RequestException:
        raise BIUPortalUnavailable()

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check if the page contains actual student data
    # Based on the user's input and common ASP.NET patterns, we extract data from common IDs/labels.
    
    data = {}
    
    def get_text_by_label(label_text):
        label = soup.find('span', string=lambda t: t and label_text in t)
        if label and label.find_next():
            return label.find_next().get_text(strip=True)
        return None

    # Common field mappings for BIU portal
    fields_mapping = {
        'full_name': ['lblFullName', 'Full Name'],
        'department': ['lblDepartment', 'Department'],
        'faculty': ['lblFaculty', 'Faculty'],
        'programme': ['lblProgramme', 'Programme'],
        'level': ['lblLevel', 'Level'],
        'hostel': ['lblHostel', 'Hostel'],
        'room_number': ['lblRoomNo', 'Room Number'],
        'email': ['lblEmail', 'Email'],
        'phone': ['lblPhone', 'Phone'],
    }

    for key, identifiers in fields_mapping.items():
        val = None
        # Try by ID first
        for identifier in identifiers:
            element = soup.find(id=lambda x: x and identifier in x)
            if element:
                val = element.get_text(strip=True)
                break
        
        # Try by label if ID search failed
        if not val:
            val = get_text_by_label(identifiers[-1])
            
        data[key] = val if val else None

    # Basic validation to see if we got anything useful
    if not any(data.values()):
        # Check for specific "not found" or "error" indicators in HTML
        if "Runtime Error" in soup.text or "not found" in soup.text.lower():
            raise StudentNotFound()
        raise StudentNotFound()

    return data
