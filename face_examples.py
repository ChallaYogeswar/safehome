"""
SafeHome Face Recognition - Python Examples & Integration Guide

This file demonstrates how to use the face recognition API
with practical, copy-paste ready examples.
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
USERNAME = "user@example.com"
PASSWORD = "password123"

# ============================================================================
# 1. AUTHENTICATION
# ============================================================================

def get_session():
    """Create authenticated session"""
    session = requests.Session()
    
    # Login first
    login_response = session.post(
        f"{BASE_URL}/auth/login",
        json={"email": USERNAME, "password": PASSWORD}
    )
    
    if login_response.status_code == 200:
        print("✓ Authenticated")
        return session
    else:
        print("✗ Authentication failed")
        return None

session = get_session()

# ============================================================================
# 2. FACE ENROLLMENT
# ============================================================================

def enroll_person(person_name, image_paths, relation='family', is_resident=True):
    """
    Enroll a new person with face images
    
    Args:
        person_name: Name of the person
        image_paths: List of image file paths
        relation: 'family', 'guest', 'staff'
        is_resident: Can they open doors?
    
    Returns:
        Response with person_id and encoding_count
    """
    files = []
    for image_path in image_paths:
        with open(image_path, 'rb') as f:
            files.append(('images', f))
    
    response = session.post(
        f"{BASE_URL}/face/enroll",
        data={
            'person_name': person_name,
            'relation': relation,
            'is_resident': 'true' if is_resident else 'false'
        },
        files=files
    )
    
    return response.json()

# Example usage:
"""
result = enroll_person(
    person_name="John Doe",
    image_paths=[
        "path/to/john1.jpg",
        "path/to/john2.jpg",
        "path/to/john3.jpg"
    ],
    relation='family',
    is_resident=True
)

if result['success']:
    print(f"✓ Enrolled {result['message']}")
    print(f"  Person ID: {result['person_id']}")
    print(f"  Encodings: {result['encoding_count']}")
else:
    print(f"✗ {result['message']}")
"""

# ============================================================================
# 3. LIST ENROLLED PERSONS
# ============================================================================

def list_enrolled_persons():
    """Get all enrolled persons"""
    response = session.get(f"{BASE_URL}/face/enrolled")
    return response.json()

# Example usage:
"""
data = list_enrolled_persons()
if data['success']:
    for person in data['persons']:
        print(f"👤 {person['name']}")
        print(f"   Relation: {person['relation']}")
        print(f"   Resident: {person['is_resident']}")
        print(f"   Faces enrolled: {person['encoding_count']}")
        print(f"   Last seen: {person['last_recognized']}")
"""

# ============================================================================
# 4. DELETE ENROLLED PERSON
# ============================================================================

def delete_person(person_id):
    """Delete an enrolled person"""
    response = session.delete(f"{BASE_URL}/face/enrolled/{person_id}")
    return response.json()

# Example usage:
"""
result = delete_person(person_id=1)
if result['success']:
    print(f"✓ {result['message']}")
"""

# ============================================================================
# 5. RECOGNIZE A FACE
# ============================================================================

def recognize_face(camera_id, image_path):
    """
    Recognize a face from an image
    
    Args:
        camera_id: ID of the camera
        image_path: Path to image file
    
    Returns:
        Recognition result with confidence and person info
    """
    with open(image_path, 'rb') as f:
        response = session.post(
            f"{BASE_URL}/face/recognize",
            data={'camera_id': camera_id},
            files={'image': f}
        )
    
    return response.json()

# Example usage:
"""
result = recognize_face(camera_id=1, image_path="test_face.jpg")

if result['success']:
    rec = result['recognition']
    if rec['is_known']:
        print(f"✓ Known person detected!")
        print(f"  Name: {rec['person_name']}")
        print(f"  Confidence: {rec['confidence']:.2%}")
        print(f"  Relation: {rec['relation']}")
        print(f"  Resident: {rec['is_resident']}")
    else:
        print(f"⚠ Unknown person detected")
        print(f"  Confidence: {rec['confidence']:.2%}")
else:
    print(f"✗ Error: {result['message']}")
"""

# ============================================================================
# 6. ENABLE ACCESS CONTROL
# ============================================================================

def enable_access_control(camera_id):
    """Enable access control on a camera"""
    response = session.post(
        f"{BASE_URL}/face/camera/{camera_id}/enable-access-control"
    )
    return response.json()

# Example usage:
"""
result = enable_access_control(camera_id=1)
if result['success']:
    print(f"✓ Access control enabled on {result['camera']['name']}")
"""

# ============================================================================
# 7. GET ACCESS LOGS
# ============================================================================

def get_access_logs(camera_id=None, limit=50, offset=0):
    """Get access logs for cameras"""
    params = {'limit': limit, 'offset': offset}
    if camera_id:
        params['camera_id'] = camera_id
    
    response = session.get(
        f"{BASE_URL}/face/access-log",
        params=params
    )
    return response.json()

# Example usage:
"""
logs = get_access_logs(camera_id=1, limit=10)

if logs['success']:
    print(f"Total access attempts: {logs['total']}")
    print("\nRecent access:")
    for log in logs['logs']:
        status = "✓ ALLOWED" if log['access_granted'] else "✗ DENIED"
        print(f"{status} - {log['person_name']} ({log['confidence']:.0%})")
        print(f"  Camera: {log['camera_id']}")
        print(f"  Action: {log['action']}")
        print(f"  Time: {log['timestamp']}")
"""

# ============================================================================
# 8. GET STATISTICS
# ============================================================================

def get_face_stats():
    """Get face recognition statistics"""
    response = session.get(f"{BASE_URL}/face/stats")
    return response.json()

# Example usage:
"""
stats = get_face_stats()

if stats['success']:
    s = stats['stats']
    print(f"📊 Face Recognition Stats")
    print(f"  Enrolled persons: {s['enrolled_persons']}")
    print(f"  Total face encodings: {s['total_encodings']}")
    print(f"  Access granted: {s['access_granted_count']}")
    print(f"  Unknown persons: {s['unknown_persons_count']}")
    
    print(f"\n  Recent access:")
    for access in s['recent_access']:
        status = "✓" if access['access_granted'] else "✗"
        print(f"  {status} {access['person_name']} - {access['timestamp']}")
"""

# ============================================================================
# 9. REAL-WORLD WORKFLOW EXAMPLES
# ============================================================================

class FaceRecognitionWorkflow:
    """Complete workflow examples"""
    
    @staticmethod
    def setup_home_security():
        """Setup face recognition for home security"""
        print("🏠 Setting up home security...")
        
        # Step 1: Enroll family members
        family = [
            {
                'name': 'Mom',
                'images': ['photos/mom1.jpg', 'photos/mom2.jpg'],
                'relation': 'family'
            },
            {
                'name': 'Dad',
                'images': ['photos/dad1.jpg', 'photos/dad2.jpg'],
                'relation': 'family'
            },
            {
                'name': 'Child',
                'images': ['photos/child1.jpg', 'photos/child2.jpg'],
                'relation': 'family'
            }
        ]
        
        print("\n📝 Enrolling family members...")
        for person in family:
            result = enroll_person(
                person_name=person['name'],
                image_paths=person['images'],
                relation=person['relation'],
                is_resident=True
            )
            if result['success']:
                print(f"  ✓ {person['name']} enrolled")
        
        # Step 2: Enable access control on cameras
        print("\n🔓 Enabling access control...")
        for camera_id in [1, 2]:  # Front and back doors
            result = enable_access_control(camera_id)
            if result['success']:
                print(f"  ✓ {result['camera']['name']}")
        
        print("✓ Setup complete!")
    
    @staticmethod
    def monitor_entry():
        """Monitor entry point with real-time recognition"""
        print("👁️  Monitoring entry point...")
        
        # Simulate real-time frame processing
        import time
        
        test_images = [
            'test_faces/known1.jpg',
            'test_faces/unknown1.jpg',
            'test_faces/known2.jpg'
        ]
        
        for image in test_images:
            result = recognize_face(camera_id=1, image_path=image)
            
            if result['success']:
                rec = result['recognition']
                
                if rec['is_known']:
                    print(f"\n✓ {rec['person_name']} detected")
                    print(f"  Confidence: {rec['confidence']:.0%}")
                    
                    if rec['is_resident']:
                        print(f"  🔓 DOOR OPENED")
                    else:
                        print(f"  ⚠️  Guest detected - alerting owner")
                else:
                    print(f"\n⚠️  Unknown person detected!")
                    print(f"  🚨 Alert sent")
                    print(f"  🔒 Door remains locked")
            
            time.sleep(1)
    
    @staticmethod
    def generate_access_report():
        """Generate access control report"""
        print("📋 Access Control Report")
        print("=" * 50)
        
        # Get statistics
        stats = get_face_stats()
        s = stats['stats']
        
        print(f"\nSummary:")
        print(f"  Total enrolled persons: {s['enrolled_persons']}")
        print(f"  Face encodings: {s['total_encodings']}")
        print(f"  Successful accesses: {s['access_granted_count']}")
        print(f"  Unknown attempts: {s['unknown_persons_count']}")
        
        # Get detailed logs
        logs = get_access_logs(limit=20)
        
        print(f"\nRecent Access Log:")
        print(f"{'Time':<20} {'Person':<15} {'Status':<10} {'Camera':<10}")
        print("-" * 55)
        
        for log in logs['logs']:
            status = "✓ OK" if log['access_granted'] else "✗ DENIED"
            timestamp = log['timestamp'][-8:]  # Last 8 chars (time)
            print(f"{timestamp:<20} {log['person_name']:<15} {status:<10} {log['camera_id']:<10}")

# ============================================================================
# 10. BATCH OPERATIONS
# ============================================================================

def batch_enroll_from_folder(folder_path, relation='family'):
    """
    Enroll multiple people from folder structure
    
    Folder structure:
    people/
      ├── John/
      │   ├── photo1.jpg
      │   └── photo2.jpg
      ├── Jane/
      │   ├── photo1.jpg
      │   └── photo2.jpg
    """
    folder = Path(folder_path)
    
    for person_folder in folder.iterdir():
        if person_folder.is_dir():
            person_name = person_folder.name
            images = list(person_folder.glob('*.jpg')) + list(person_folder.glob('*.png'))
            
            if images:
                result = enroll_person(
                    person_name=person_name,
                    image_paths=[str(img) for img in images],
                    relation=relation,
                    is_resident=True
                )
                
                status = "✓" if result['success'] else "✗"
                print(f"{status} {person_name}: {len(images)} photos")

# ============================================================================
# 11. COMMAND LINE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Usage examples:
    
    python face_examples.py --enroll "photos/john" "John Doe"
    python face_examples.py --recognize "test.jpg" 1
    python face_examples.py --list
    python face_examples.py --setup
    python face_examples.py --monitor
    python face_examples.py --report
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description='SafeHome Face Recognition CLI')
    parser.add_argument('--enroll', nargs=2, help='Enroll person: --enroll <folder> <name>')
    parser.add_argument('--recognize', nargs=2, help='Recognize face: --recognize <image> <camera_id>')
    parser.add_argument('--list', action='store_true', help='List enrolled persons')
    parser.add_argument('--setup', action='store_true', help='Setup home security')
    parser.add_argument('--monitor', action='store_true', help='Monitor entry point')
    parser.add_argument('--report', action='store_true', help='Generate access report')
    
    args = parser.parse_args()
    
    if args.enroll:
        print(f"Enrolling {args.enroll[1]} from {args.enroll[0]}...")
        batch_enroll_from_folder(args.enroll[0])
    
    elif args.recognize:
        result = recognize_face(camera_id=int(args.recognize[1]), image_path=args.recognize[0])
        print(json.dumps(result, indent=2))
    
    elif args.list:
        data = list_enrolled_persons()
        for person in data['persons']:
            print(f"{person['name']} (ID: {person['id']})")
    
    elif args.setup:
        FaceRecognitionWorkflow.setup_home_security()
    
    elif args.monitor:
        FaceRecognitionWorkflow.monitor_entry()
    
    elif args.report:
        FaceRecognitionWorkflow.generate_access_report()
    
    else:
        parser.print_help()

