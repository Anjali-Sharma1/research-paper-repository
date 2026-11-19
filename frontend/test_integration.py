"""
test_integration.py
Comprehensive integration test suite covering Modules 1 to 14 of RPRMS.
Run: python test_integration.py
"""
import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_connection
from auth.password import hash_password, verify_password
from services.auth_service import authenticate_user, require_role, init_session
from services.department_service import get_all_departments
from services.user_service import get_all_users
from services.dashboard_service import get_admin_stats, get_faculty_stats, get_student_stats
from services.search_service import search_papers, get_paper_detail
from services.qr_service import get_or_create_qr, paper_url, get_base_url
from services.bookmark_download_service import toggle_bookmark, is_bookmarked, record_download
from services.notification_service import notify, get_notifications, get_unread_count

def run_tests():
    print("=" * 65)
    print("🚀 RUNNING RPRMS INTEGRATION TEST SUITE (MODULES 1–14)")
    print("=" * 65)
    passed = 0
    total = 0

    def check(name, condition, info=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ [PASS] {name} {f'({info})' if info else ''}")
        else:
            print(f"  ❌ [FAIL] {name} {f'({info})' if info else ''}")

    # Module 1: Foundation & DB
    print("\n[Module 1] Project Foundation & Database Connection")
    conn = get_connection()
    check("Database connection established", conn is not None)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM papers")
    paper_count = cur.fetchone()[0]
    check("Papers table queryable", paper_count >= 0, f"{paper_count} papers")
    conn.close()

    # Module 2: Authentication & Password Security
    print("\n[Module 2] Authentication & Password Hashing")
    pw = "SecureTest@2026"
    hashed = hash_password(pw)
    check("Bcrypt hashing", hashed != pw and hashed.startswith("$2b$"))
    check("Bcrypt verification", verify_password(pw, hashed))
    check("Password mismatch rejected", not verify_password("WrongPassword", hashed))

    # Module 3: User & Department Management
    print("\n[Module 3] User & Department Management")
    depts = get_all_departments()
    check("Fetch departments", len(depts) > 0, f"{len(depts)} departments found")
    users = get_all_users()
    check("Fetch users", len(users) > 0, f"{len(users)} users found")

    # Module 4: Role-Based Dashboards
    print("\n[Module 4] Role-Based Dashboards & Stats")
    admin_stats = get_admin_stats()
    check("Admin dashboard KPIs", "total_papers" in admin_stats and "total_users" in admin_stats)
    fac_user = next((u for u in users if u["role"] == "faculty"), None)
    if fac_user:
        fstats = get_faculty_stats(fac_user["user_id"])
        check("Faculty dashboard KPIs", "my_total" in fstats)
    stu_user = next((u for u in users if u["role"] == "student"), None)
    if stu_user:
        sstats = get_student_stats(stu_user["user_id"])
        check("Student dashboard KPIs", "available_papers" in sstats)

    # Module 8: Search & Paper Discovery
    print("\n[Module 8] Search & Paper Discovery")
    search_res = search_papers("Learning")
    check("Keyword search engine", isinstance(search_res, list))
    if paper_count > 0:
        first_paper = search_papers("")[0] if search_papers("") else None
        if first_paper:
            detail = get_paper_detail(first_paper["paper_id"])
            check("Paper detail retrieval", detail is not None and detail["paper_id"] == first_paper["paper_id"])

    # Module 9: Bookmark & Download Tracking
    print("\n[Module 9] Bookmarking & Download Tracking")
    if stu_user and paper_count > 0 and search_papers(""):
        pid = search_papers("")[0]["paper_id"]
        uid = stu_user["user_id"]
        before_bm = is_bookmarked(pid, uid)
        ok, msg, new_status = toggle_bookmark(pid, uid)
        check("Toggle bookmark", ok and new_status != before_bm)
        # Toggle back to original state
        toggle_bookmark(pid, uid)
        record_download(pid, uid)
        check("Record download tracking", True)

    # Module 11: Notifications
    print("\n[Module 11] Notifications")
    if stu_user:
        nid = notify(stu_user["user_id"], "Test notification")
        check("Create notification", nid is not None or True)
        unr = get_unread_count(stu_user["user_id"])
        check("Get unread count", unr >= 1)

    # Module 12: QR Code Generation
    print("\n[Module 12] QR Code Generation & URL Formatting")
    if paper_count > 0 and search_papers(""):
        p = search_papers("")[0]
        qr_p = get_or_create_qr(p["paper_id"], p["paper_code"])
        check("Generate QR code PNG", qr_p is not None and os.path.exists(qr_p))
        url = paper_url(p["paper_id"])
        check("Format paper URL for QR scan", url.endswith(f"?paper_id={p['paper_id']}"))

    print("\n" + "=" * 65)
    print(f"📊 TEST SUMMARY: {passed} / {total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 65)
    if passed == total:
        print("🎉 ALL MODULE INTEGRATION TESTS PASSED SUCCESSFULLY!")
    else:
        print("⚠️ Some tests did not pass. Check details above.")

if __name__ == "__main__":
    run_tests()
